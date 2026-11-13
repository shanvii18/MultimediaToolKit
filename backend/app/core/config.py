import os
import logging
import secrets
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

AUTH_MODE_ACCESS_KEY = "access_key"
AUTH_MODE_DEV_OPEN = "dev_open"


class Settings(BaseSettings):
    PROJECT_NAME: str = "MultimediaToolKit API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS configuration (comma-separated origins, or "*").
    # Auth uses a bearer header, not cookies, so credentials are never allowed cross-origin.
    ALLOWED_ORIGINS: str = "*"
    # Optional regex for extra origins, e.g. Vercel preview deployments:
    #   ^https://multimedia-toolkit(-[a-z0-9-]+)?\.vercel\.app$
    ALLOWED_ORIGIN_REGEX: str = ""

    # Database configuration (PostgreSQL; SQLite only for local development)
    DATABASE_URL: str = "sqlite:///./multimediatoolkit.db"
    # Development only: fall back to local SQLite if PostgreSQL is unreachable.
    # Never honoured outside ENVIRONMENT=development (silent fallback = silent data loss).
    ALLOW_SQLITE_FALLBACK: bool = True

    # Redis configuration (optional; not required by the job queue)
    REDIS_URL: str = "redis://localhost:6379/0"

    # File storage root directory
    STORAGE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage")
    MAX_UPLOAD_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB default cap

    # ---- Access control (invite-only access keys) ----
    # "access_key": every request needs a valid personal access key.
    # "dev_open":   keyless requests act as a single local developer user (development only).
    # Unset -> "dev_open" when ENVIRONMENT=development, otherwise "access_key".
    AUTH_MODE: Optional[str] = None
    # Secret for signing short-lived download URLs. Required outside development.
    SIGNING_SECRET: str = ""
    DOWNLOAD_URL_TTL_SECONDS: int = 3600
    # Public sign-up / sign-in abuse limits (per client IP / per email, in-memory)
    SIGNUP_RATE_LIMIT_PER_HOUR: int = 10
    LOGIN_RATE_LIMIT_PER_15_MIN: int = 10
    # Used only to print invite links from the CLI.
    FRONTEND_URL: str = "http://localhost:3000"

    # ---- Job processing ----
    # Run the job worker loop inside the API process (single-service deployments such as Render Free).
    EMBEDDED_WORKER: bool = True
    WORKER_POLL_INTERVAL_SECONDS: float = 2.0
    WORKER_HEARTBEAT_SECONDS: int = 15
    # A running job whose heartbeat is older than this is considered abandoned.
    JOB_STALE_AFTER_SECONDS: int = 180
    JOB_MAX_ATTEMPTS: int = 2
    # Run each job in a child process with a memory watchdog (recommended on small servers).
    JOB_ISOLATION: bool = False
    # Watchdog limit for one job's process tree (MB, 0 = off). Render Free has 512 MB in total.
    JOB_MEMORY_LIMIT_MB: int = 400
    # On Linux containers the watchdog instead watches the container's real working set (cgroup memory,
    # the number the platform's OOM killer uses) and stops the job when it gets within this margin of
    # the container limit. Summed process RSS double-counts shared libraries and stopped jobs that fit.
    JOB_CONTAINER_MARGIN_MB: int = 40
    JOB_CONTAINER_LIMIT_MB: int = 0                 # 0 = read the limit from the cgroup (memory.max)

    # ---- FFmpeg ----
    FFMPEG_TIMEOUT_SECONDS: int = 600
    # 0 = FFmpeg decides (one thread per visible core). Small servers (Render Free, 512 MB):
    # 1-2 keeps encoder/filter memory low, because containers often "see" many host cores.
    FFMPEG_THREADS: int = 0

    # ---- Storage backend ----
    # "local": files under STORAGE_DIR (development / tests).
    # "s3": any S3-compatible bucket (Backblaze B2, Cloudflare R2, MinIO, AWS S3...).
    STORAGE_BACKEND: str = "local"
    S3_BUCKET: str = ""
    S3_ENDPOINT_URL: str = ""          # e.g. https://s3.us-west-004.backblazeb2.com
    S3_REGION: str = "auto"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_KEY_PREFIX: str = "mtk/"
    S3_PRESIGN_TTL_SECONDS: int = 900
    # Scratch space for jobs (downloaded inputs, intermediates). Cleaned after each job.
    WORK_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "work")

    # ---- CPU AI engines ----
    # Model weights/caches. Point this at a large drive (e.g. D:/MultimediaToolKit/models).
    MODEL_CACHE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "models")
    # Download missing models on first use. Set false on servers that must stay offline.
    AUTO_DOWNLOAD_MODELS: bool = True
    WHISPER_DEFAULT_MODEL: str = "base"           # tiny | base | small
    WHISPER_COMPUTE_TYPE: str = "int8"
    WHISPER_CPU_THREADS: int = 0                  # 0 = library default
    KOKORO_MODEL_FILE: str = "kokoro-v1.0.int8.onnx"
    KOKORO_VOICES_FILE: str = "voices-v1.0.bin"
    KOKORO_RELEASE_URL: str = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
    TTS_CPU_THREADS: int = 0                       # 0 = ONNX Runtime default; 1-2 on 512 MB servers
    TESSERACT_CMD: str = ""                        # auto-detected when empty
    # false = release Whisper/Kokoro from RAM after every job (slower next job, lower idle memory)
    KEEP_MODELS_LOADED: bool = True
    OCR_TIMEOUT_SECONDS: int = 120

    # ---- Optional hosted AI provider (image generation + image description) ----
    # "none" (default): AI modes report "needs configuration"; CPU modes still work.
    # "cloudflare": Cloudflare Workers AI (free daily allowance; needs account id + API token).
    # "huggingface": Hugging Face Inference (needs an access token).
    AI_PROVIDER: str = "none"
    AI_TIMEOUT_SECONDS: int = 120
    CLOUDFLARE_ACCOUNT_ID: str = ""
    CLOUDFLARE_API_TOKEN: str = ""
    CLOUDFLARE_IMAGE_MODEL: str = "@cf/black-forest-labs/flux-1-schnell"
    CLOUDFLARE_CAPTION_MODEL: str = "@cf/llava-hf/llava-1.5-7b-hf"
    # SD 1.5 img2img is no longer granted to new accounts (403 code 5018); DreamShaper 8 LCM accepts image+strength.
    CLOUDFLARE_IMG2IMG_MODEL: str = "@cf/lykon/dreamshaper-8-lcm"
    # After a provider failure (5xx / 429 / network) AI modes show "temporarily unavailable" this long.
    AI_FAILURE_COOLDOWN_SECONDS: int = 180
    HF_API_TOKEN: str = ""
    HF_INFERENCE_BASE_URL: str = "https://router.huggingface.co/hf-inference/models"
    HF_IMAGE_MODEL: str = "black-forest-labs/FLUX.1-schnell"
    HF_CAPTION_MODEL: str = "Salesforce/blip-image-captioning-large"

    # ---- Optional Redis wake-up queue (the database remains the source of truth) ----
    QUEUE_NOTIFY_REDIS: bool = False

    # ---- Input limits (protect a small CPU server) ----
    MAX_TEXT_CHARS: int = 5000
    MAX_VIDEO_SCENES: int = 10                     # text-to-video scenes (one per sentence); 6 on 512 MB servers
    MAX_TRANSCRIBE_SECONDS: int = 1800             # 30 minutes of audio/video
    MAX_IMAGE_PIXELS: int = 40_000_000

    # Whitelist of supported media and document extensions
    ALLOWED_EXTENSIONS: set = {
        # Video
        ".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v",
        # Audio
        ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma",
        # Images
        ".png", ".jpg", ".jpeg", ".webp", ".svg", ".bmp", ".gif",
        # Documents & Captions
        ".pdf", ".docx", ".txt", ".json", ".srt", ".vtt"
    }

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.strip().lower() == "development"

    @property
    def effective_auth_mode(self) -> str:
        if self.AUTH_MODE:
            return self.AUTH_MODE.strip().lower()
        return AUTH_MODE_DEV_OPEN if self.is_development else AUTH_MODE_ACCESS_KEY

    @property
    def cors_origins(self) -> List[str]:
        if self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


def validate_settings(s: Settings) -> List[str]:
    """Return a list of fatal configuration errors (empty list = OK)."""
    errors: List[str] = []
    mode = s.effective_auth_mode
    if mode not in (AUTH_MODE_ACCESS_KEY, AUTH_MODE_DEV_OPEN):
        errors.append(f"AUTH_MODE must be '{AUTH_MODE_ACCESS_KEY}' or '{AUTH_MODE_DEV_OPEN}', got '{mode}'.")
    if not s.is_development:
        if mode == AUTH_MODE_DEV_OPEN:
            errors.append("AUTH_MODE=dev_open is only allowed when ENVIRONMENT=development.")
        if not s.SIGNING_SECRET or len(s.SIGNING_SECRET) < 32:
            errors.append("SIGNING_SECRET (at least 32 characters) is required outside development.")
    backend = s.STORAGE_BACKEND.strip().lower()
    if backend not in ("local", "s3"):
        errors.append(f"STORAGE_BACKEND must be 'local' or 's3', got '{s.STORAGE_BACKEND}'.")
    if backend == "s3":
        missing = [n for n in ("S3_BUCKET", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY") if not getattr(s, n)]
        if missing:
            errors.append(f"STORAGE_BACKEND=s3 requires: {', '.join(missing)}.")
    return errors


def storage_warnings(s: Settings) -> List[str]:
    warnings: List[str] = []
    raw = s.STORAGE_DIR.replace("\\", "/")
    is_local = s.STORAGE_BACKEND.strip().lower() == "local"
    if is_local and not s.is_development and (raw.startswith("/tmp") or raw.startswith("/var/tmp")):
        warnings.append(
            f"STORAGE_DIR={s.STORAGE_DIR} is ephemeral: uploaded and generated files are lost on every "
            "restart/redeploy. Downloads of lost files return 410 Gone. See PROJECT_STATUS.md storage plan."
        )
    return warnings


settings = Settings()

# Empty values (e.g. "STORAGE_DIR=" copied from .env.example) mean "use the default".
for _name in ("STORAGE_DIR", "WORK_DIR", "MODEL_CACHE_DIR", "WHISPER_DEFAULT_MODEL", "AI_PROVIDER",
              "STORAGE_BACKEND", "ENVIRONMENT"):
    if not str(getattr(settings, _name) or "").strip():
        setattr(settings, _name, Settings.model_fields[_name].default)

_errors = validate_settings(settings)
if _errors:
    raise RuntimeError("Invalid configuration:\n  - " + "\n  - ".join(_errors))

if not settings.SIGNING_SECRET:
    # Development only (validated above): per-process secret; signed URLs expire on restart.
    settings.SIGNING_SECRET = secrets.token_hex(32)

for _w in storage_warnings(settings):
    logger.warning(_w)

os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.WORK_DIR, exist_ok=True)

# Keep every model/cache download (Hugging Face hub, etc.) inside MODEL_CACHE_DIR,
# never in the user's home directory on the system drive.
os.environ.setdefault("HF_HOME", os.path.join(settings.MODEL_CACHE_DIR, "hf"))
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
