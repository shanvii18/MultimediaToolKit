"""
Conversion engine framework.

A ``ConversionSpec`` describes one directed conversion (e.g. audio -> text): its modes,
user parameters, accepted inputs, the processing engines it needs and the pipeline
function that runs it. ``JobContext`` gives pipelines a small, safe API: report progress,
read inputs (materialised from storage), and register real output files as assets.
"""
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app.core.media_types import mime_type_for
from app.models.entities import Asset, Job, JobOutput

logger = logging.getLogger(__name__)

FORMATS = ("text", "image", "audio", "video", "animation")

VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v")
AUDIO_EXTENSIONS = (".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")
ANIMATION_EXTENSIONS = (".gif", ".webp", ".mp4", ".webm", ".mov", ".m4v")
TEXT_EXTENSIONS = (".txt",)


class ConversionError(Exception):
    """A user-facing processing failure (bad input, nothing found...). Never a fake success."""

    def __init__(self, message: str, code: str = "INVALID_INPUT"):
        super().__init__(message)
        self.code = code


class EngineUnavailableError(ConversionError):
    def __init__(self, message: str):
        super().__init__(message, code="ENGINE_UNAVAILABLE")


@dataclass
class ParamSpec:
    name: str
    label: str
    type: str = "select"                       # select | number | boolean | text | textarea
    default: Any = None
    choices: Optional[List[Tuple[str, str]]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    max_length: Optional[int] = None
    help: str = ""
    modes: Optional[Tuple[str, ...]] = None    # only shown/used for these modes

    def to_dict(self) -> dict:
        return {
            "name": self.name, "label": self.label, "type": self.type, "default": self.default,
            "choices": [{"value": v, "label": l} for v, l in self.choices] if self.choices else None,
            "min": self.min, "max": self.max, "step": self.step, "max_length": self.max_length,
            "help": self.help, "modes": list(self.modes) if self.modes else None,
        }

    def clean(self, raw: Any) -> Any:
        value = self.default if raw is None or raw == "" else raw
        if self.type == "select":
            allowed = [v for v, _ in (self.choices or [])]
            value = str(value)
            if value not in allowed:
                raise ValueError(f"Unsupported {self.label.lower()} '{value}'. Supported: {', '.join(allowed)}.")
            return value
        if self.type == "number":
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise ValueError(f"{self.label} must be a number.")
            if self.min is not None and value < self.min:
                raise ValueError(f"{self.label} must be at least {self.min:g}.")
            if self.max is not None and value > self.max:
                raise ValueError(f"{self.label} must be at most {self.max:g}.")
            return value
        if self.type == "boolean":
            if isinstance(value, str):
                return value.strip().lower() in ("1", "true", "yes", "on")
            return bool(value)
        # text / textarea
        value = "" if value is None else str(value)
        if self.max_length and len(value) > self.max_length:
            raise ValueError(f"{self.label} is too long (max {self.max_length} characters).")
        return value


@dataclass
class ModeSpec:
    id: str
    label: str
    description: str
    engines: Tuple[str, ...] = ()
    coming_soon: bool = False


@dataclass
class ConversionSpec:
    id: str
    source: str
    target: str
    title: str
    description: str
    category: str                               # normal | generative | workflow
    run: Optional[Callable[["JobContext"], None]] = None
    modes: List[ModeSpec] = field(default_factory=list)
    params: List[ParamSpec] = field(default_factory=list)
    input_kind: str = "file"                    # file | text | file_or_text
    accepted_extensions: Sequence[str] = ()
    max_inputs: int = 1
    validator: Optional[Callable[[Dict[str, Any], List[Asset]], None]] = None
    listed: bool = True                          # False for legacy/internal tools

    @property
    def implemented(self) -> bool:
        return self.run is not None and any(not m.coming_soon for m in self.modes)

    def get_mode(self, mode_id: Optional[str]) -> ModeSpec:
        if not self.modes:
            raise ValueError("This conversion has no modes defined.")
        if mode_id in (None, ""):
            return next((m for m in self.modes if not m.coming_soon), self.modes[0])
        for m in self.modes:
            if m.id == mode_id:
                return m
        raise ValueError(f"Unknown mode '{mode_id}'. Available: {', '.join(m.id for m in self.modes)}.")

    def clean_params(self, raw: Dict[str, Any], mode: ModeSpec) -> Dict[str, Any]:
        raw = raw or {}
        cleaned: Dict[str, Any] = {"mode": mode.id}
        for p in self.params:
            if p.modes and mode.id not in p.modes:
                continue
            cleaned[p.name] = p.clean(raw.get(p.name))
        return cleaned


class JobContext:
    """Everything a pipeline may touch while running one job."""

    def __init__(self, db: Session, job: Job, work_dir: str, storage):
        self.db = db
        self.job = job
        self.work_dir = work_dir
        self.storage = storage
        self.params: Dict[str, Any] = dict(job.params_json or {})
        self.mode: str = self.params.get("mode", "")
        self.stored_keys: List[str] = []
        self.outputs: List[Asset] = []

    # ---- progress ----
    def progress(self, percent: float, message: str = "") -> None:
        self.job.progress = int(max(0, min(99, percent)))
        if message:
            self.job.progress_message = message[:255]
        self.db.commit()

    def sub_progress(self, start: float, end: float, message: str) -> Callable[[float], None]:
        """Callback mapping a 0..1 fraction onto [start, end] percent (throttled to whole percents)."""
        last = {"value": -1}

        def callback(fraction: float) -> None:
            value = int(start + (end - start) * max(0.0, min(1.0, fraction)))
            if value != last["value"]:
                last["value"] = value
                self.progress(value, message)

        return callback

    # ---- inputs ----
    def input_asset(self, index: int = 0) -> Asset:
        ids = self.job.input_asset_ids or []
        if index >= len(ids):
            raise ConversionError("This conversion needs an input file.")
        asset = self.db.query(Asset).filter(Asset.id == ids[index]).first()
        if not asset:
            raise ConversionError("The input file was not found.")
        if asset.owner_id is not None and asset.owner_id != self.job.user_id:
            raise PermissionError("Input asset does not belong to the job owner.")
        return asset

    def input_path(self, index: int = 0) -> str:
        asset = self.input_asset(index)
        try:
            return self.storage.materialize(asset.storage_key, self.work_dir)
        except FileNotFoundError:
            raise ConversionError("The input file is no longer available in storage (it may have expired). "
                                  "Please upload it again.", code="INPUT_EXPIRED")

    def tmp(self, name: str) -> str:
        return os.path.join(self.work_dir, name)

    # ---- outputs ----
    def add_output(self, local_path: str, filename: str, output_type: str,
                   metadata: Optional[Dict[str, Any]] = None) -> Asset:
        if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
            raise RuntimeError(f"Output '{filename}' was not produced.")
        ext = os.path.splitext(filename)[1].lower()
        key, size, checksum = self.storage.store_file(local_path, ext)
        self.stored_keys.append(key)
        asset = Asset(
            project_id=self.job.project_id,
            owner_id=self.job.user_id,
            filename=filename,
            storage_key=key,
            media_type=mime_type_for(key),
            size=size,
            checksum=checksum,
            metadata_json={"source_job_id": self.job.id, "tool": self.job.tool, **(metadata or {})},
        )
        self.db.add(asset)
        self.db.flush()
        self.db.add(JobOutput(job_id=self.job.id, asset_id=asset.id, output_type=output_type))
        self.outputs.append(asset)
        return asset

    def add_text_output(self, text: str, filename: str, output_type: str,
                        metadata: Optional[Dict[str, Any]] = None) -> Asset:
        path = self.tmp(f"_{len(self.outputs)}_{filename}")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return self.add_output(path, filename, output_type, metadata)

    def cleanup_failed_outputs(self) -> None:
        for key in self.stored_keys:
            try:
                self.storage.delete(key)
            except Exception:  # noqa: BLE001
                logger.warning("Could not remove output %s after failure", key)


def stem_of(filename: str, fallback: str = "output") -> str:
    stem = os.path.splitext(os.path.basename(filename or ""))[0].strip()
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in stem).strip()
    return (safe or fallback)[:80]
