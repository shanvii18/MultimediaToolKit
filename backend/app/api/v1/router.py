import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db, Base, engine
from app.models.entities import Project, Asset, Job, JobOutput
from app.schemas.schemas import (
    ProjectCreate, ProjectResponse,
    AssetResponse,
    JobCreate, JobResponse
)
from app.services.storage_service import storage_service
from app.services.job_runner_service import job_runner_service

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api/v1", tags=["MultimediaToolKit API v1"])


# ---------------- Projects ----------------
@router.post("/projects", response_model=ProjectResponse)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(title=payload.title.strip(), description=payload.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/projects/{project_id}/assets", response_model=List[AssetResponse])
def get_project_assets(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(Asset).filter(Asset.project_id == project_id).order_by(Asset.created_at.desc()).all()


# ---------------- Media / Assets ----------------
@router.post("/media", response_model=AssetResponse)
def upload_media(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded or filename is empty.")

    if project_id:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    try:
        storage_key, size, checksum = storage_service.save_upload(file)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    safe_filename = os.path.basename(file.filename)
    asset = Asset(
        project_id=project_id,
        filename=safe_filename,
        storage_key=storage_key,
        media_type=file.content_type or "application/octet-stream",
        size=size,
        checksum=checksum,
        metadata_json={"original_name": safe_filename}
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/assets", response_model=List[AssetResponse])
def list_assets(db: Session = Depends(get_db)):
    return db.query(Asset).order_by(Asset.created_at.desc()).all()


@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get("/assets/{asset_id}/download")
def download_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    try:
        file_path = storage_service.get_full_path(asset.storage_key)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid storage path")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Physical asset file missing on disk")

    return FileResponse(
        path=file_path,
        filename=asset.filename,
        media_type=asset.media_type
    )


# ---------------- Jobs ----------------
@router.post("/jobs", response_model=JobResponse)
def create_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    if not payload.tool or not payload.tool.strip():
        raise HTTPException(status_code=400, detail="Tool parameter cannot be empty.")

    if payload.project_id:
        proj = db.query(Project).filter(Project.id == payload.project_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail=f"Project '{payload.project_id}' not found.")

    # Validate specific tool inputs prior to queuing
    if payload.tool == "idea_to_storyboard":
        concept = (payload.params_json or {}).get("concept", "")
        if not concept or not concept.strip():
            raise HTTPException(status_code=400, detail="Concept / brief cannot be empty.")
        if len(concept.strip().split()) < 3 or len(concept.strip()) < 12:
            raise HTTPException(
                status_code=400,
                detail="Concept brief is too brief. Please provide at least 3 descriptive words (min 12 characters)."
            )

    elif payload.tool == "video_to_audio":
        if not payload.input_asset_ids or len(payload.input_asset_ids) == 0:
            raise HTTPException(status_code=400, detail="No input asset specified for video_to_audio.")
        input_asset = db.query(Asset).filter(Asset.id == payload.input_asset_ids[0]).first()
        if not input_asset:
            raise HTTPException(status_code=404, detail=f"Input asset '{payload.input_asset_ids[0]}' not found.")

    job = Job(
        project_id=payload.project_id,
        tool=payload.tool.strip(),
        input_asset_ids=payload.input_asset_ids,
        params_json=payload.params_json,
        status="queued",
        progress=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Queue execution on background task pool passing only job_id (independent session managed in runner)
    background_tasks.add_task(job_runner_service.process_job, job.id)

    return job


@router.get("/jobs", response_model=List[JobResponse])
def list_jobs(db: Session = Depends(get_db)):
    return (
        db.query(Job)
        .options(joinedload(Job.outputs).joinedload(JobOutput.asset))
        .order_by(Job.created_at.desc())
        .all()
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = (
        db.query(Job)
        .options(joinedload(Job.outputs).joinedload(JobOutput.asset))
        .filter(Job.id == job_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
