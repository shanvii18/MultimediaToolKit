from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


# ---------------- Project Schemas ----------------
class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ---------------- Asset Schemas ----------------
class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: Optional[str] = None
    owner_id: Optional[str] = None
    filename: str
    media_type: str
    size: int
    checksum: Optional[str] = None
    metadata_json: Dict[str, Any] = {}
    created_at: datetime


# ---------------- Job Schemas ----------------
class JobCreate(BaseModel):
    project_id: Optional[str] = None
    tool: str = Field(..., description="Tool identifier, e.g. video_to_audio, speech_to_text, idea_to_storyboard")
    input_asset_ids: List[str] = Field(default_factory=list)
    params_json: Dict[str, Any] = Field(default_factory=dict)


class JobOutputResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    asset_id: str
    output_type: str
    created_at: datetime
    asset: Optional[AssetResponse] = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    tool: str
    status: str
    progress: int
    input_asset_ids: List[str] = []
    params_json: Dict[str, Any] = {}
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outputs: List[JobOutputResponse] = []
