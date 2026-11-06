import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Header
from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlalchemy.orm import Session, joinedload
from app.core.config import settings
from app.core.database import get_db
from app.core.media_types import mime_type_for
from app.core.security import verify_download_signature
from app.api.deps import get_current_user, owned_by, is_owner, resolve_user
from app.models.entities import Project, Asset, Job, JobOutput, User
from app.schemas.schemas import (
    ProjectCreate, ProjectResponse,
    AssetResponse,
    JobCreate, JobResponse
)
from app.services.storage_service import storage_service
from app.engines.registry import get_spec, list_conversions, validate_job_request
from app.services.job_queue import notify_new_job

router = APIRouter(prefix="/api/v1", tags=["MultimediaToolKit API v1"])

# Headers that stop a downloaded file from ever being interpreted as active content
# on the API origin, regardless of what was uploaded.
SAFE_DOWNLOAD_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; sandbox",
    "Cross-Origin-Resource-Policy": "cross-origin",
    "Cache-Control": "private, max-age=0, no-store",
}


def _get_owned_project(db: Session, project_id: str, user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or not is_owner(project.owner_id, user):
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _get_owned_asset(db: Session, asset_id: str, user: User) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset or not is_owner(asset.owner_id, user):
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


# ---------------- Current user ----------------
@router.get("/me")
def me(user: User = Depends(get_current_user)):
    """Who am I? Used by the frontend to validate the session and show the signed-in user."""
    return {"id": user.id, "email": user.email, "role": user.role, "auth_mode": settings.effective_auth_mode}


# ---------------- Projects ----------------
@router.post("/projects", response_model=ProjectResponse)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = Project(title=payload.title.strip(), description=payload.description, owner_id=user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Project)
        .filter(owned_by(Project.owner_id, user))
        .order_by(Project.created_at.desc())
        .all()
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_owned_project(db, project_id, user)


@router.get("/projects/{project_id}/assets", response_model=List[AssetResponse])
def get_project_assets(project_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_owned_project(db, project_id, user)
    return (
        db.query(Asset)
        .filter(Asset.project_id == project_id, owned_by(Asset.owner_id, user))
        .order_by(Asset.created_at.desc())
        .all()
    )


# ---------------- Media / Assets ----------------
@router.post("/media", response_model=AssetResponse)
def upload_media(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded or filename is empty.")

    if project_id:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj or not is_owner(proj.owner_id, user):
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    try:
        storage_key, size, checksum = storage_service.save_upload(file)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    safe_filename = os.path.basename(file.filename)
    asset = Asset(
        project_id=project_id,
        owner_id=user.id,
        filename=safe_filename,
        storage_key=storage_key,
        # Never trust the client-supplied Content-Type; derive it from the allow-listed extension.
        media_type=mime_type_for(storage_key),
        size=size,
        checksum=checksum,
        metadata_json={"original_name": safe_filename}
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/assets", response_model=List[AssetResponse])
def list_assets(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Asset)
        .filter(owned_by(Asset.owner_id, user))
        .order_by(Asset.created_at.desc())
        .all()
    )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_owned_asset(db, asset_id, user)


@router.delete("/assets/{asset_id}", status_code=204)
def delete_asset(asset_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Delete one of the caller's files (database row, job-output links and stored object)."""
    asset = _get_owned_asset(db, asset_id, user)
    storage_key = asset.storage_key
    db.delete(asset)
    db.commit()
    try:
        storage_service.delete(storage_key)
    except Exception:  # the row is gone; a leftover object is harmless and not addressable
        pass
    return Response(status_code=204)


@router.get("/assets/{asset_id}/download")
def download_asset(
    asset_id: str,
    expires: Optional[int] = Query(None),
    signature: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    x_access_key: Optional[str] = Header(None),
):
    """
    Download an asset. Authorised by either:
      - a valid short-lived signed URL (``expires`` + ``signature``, as returned in ``download_url``), or
      - the owner's session token (``Authorization: Bearer <token>``), or the local dev user in development.
    """
    if signature is not None or expires is not None:
        if not verify_download_signature(asset_id, expires, signature):
            raise HTTPException(status_code=403, detail="Download link is invalid or has expired.")
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
    else:
        user = resolve_user(db, authorization, x_access_key)
        if user is None:
            raise HTTPException(status_code=401, detail="Please sign in to download this file.")
        asset = _get_owned_asset(db, asset_id, user)

    gone = HTTPException(
        status_code=410,
        detail="This file is no longer available (temporary storage was reset). Please re-upload or re-run the job.",
    )
    # Server-derived type: ignores any (possibly attacker-supplied) value stored in the DB.
    content_type = mime_type_for(asset.storage_key)
    backend = storage_service.backend

    try:
        file_path = backend.local_path(asset.storage_key)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid storage path")

    if file_path is not None:
        if not os.path.exists(file_path):
            raise gone
        return FileResponse(
            path=file_path,
            filename=asset.filename,
            media_type=content_type,
            content_disposition_type="attachment",
            headers=SAFE_DOWNLOAD_HEADERS,
        )

    # Remote object storage: authorise here, then redirect to a short-lived presigned URL
    # (the bucket enforces the same content type + attachment disposition).
    if not backend.exists(asset.storage_key):
        raise gone
    url = backend.presigned_url(asset.storage_key, asset.filename, content_type, settings.S3_PRESIGN_TTL_SECONDS)
    return RedirectResponse(url=url, status_code=307, headers={"Cache-Control": "no-store"})


# ---------------- Conversions catalogue ----------------
@router.get("/conversions")
def conversions():
    """Public catalogue of the 20 conversions with live engine availability on this server."""
    return list_conversions()


# ---------------- Jobs ----------------
@router.post("/jobs", response_model=JobResponse)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not payload.tool or not payload.tool.strip():
        raise HTTPException(status_code=400, detail="Tool parameter cannot be empty.")

    if payload.project_id:
        proj = db.query(Project).filter(Project.id == payload.project_id).first()
        if not proj or not is_owner(proj.owner_id, user):
            raise HTTPException(status_code=404, detail=f"Project '{payload.project_id}' not found.")

    # Every referenced input asset must belong to the caller
    inputs = []
    for input_id in payload.input_asset_ids:
        input_asset = db.query(Asset).filter(Asset.id == input_id).first()
        if not input_asset or not is_owner(input_asset.owner_id, user):
            raise HTTPException(status_code=404, detail=f"Input asset '{input_id}' not found.")
        inputs.append(input_asset)

    spec = get_spec(payload.tool)
    if spec is None:
        raise HTTPException(status_code=400, detail=f"Unknown conversion '{payload.tool}'.")
    try:
        cleaned_params = validate_job_request(spec, payload.params_json or {}, inputs)
    except NotImplementedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=503, detail=str(e))

    job = Job(
        project_id=payload.project_id,
        user_id=user.id,
        tool=payload.tool.strip(),
        input_asset_ids=payload.input_asset_ids,
        params_json=cleaned_params,
        status="queued",
        progress=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # The job is now durably queued in the database; a worker (embedded or standalone)
    # claims it. Nothing runs inside this request, so restarts cannot lose it.
    notify_new_job(job.id)
    return job


@router.get("/jobs", response_model=List[JobResponse])
def list_jobs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Job)
        .options(joinedload(Job.outputs).joinedload(JobOutput.asset))
        .filter(owned_by(Job.user_id, user))
        .order_by(Job.created_at.desc())
        .all()
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = (
        db.query(Job)
        .options(joinedload(Job.outputs).joinedload(JobOutput.asset))
        .filter(Job.id == job_id)
        .first()
    )
    if not job or not is_owner(job.user_id, user):
        raise HTTPException(status_code=404, detail="Job not found")
    return job
