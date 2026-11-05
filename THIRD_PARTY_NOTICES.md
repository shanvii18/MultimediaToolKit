# THIRD_PARTY_NOTICES.md

MultimediaToolKit uses the open-source software listed below. Each component remains the property of its authors and is used under the licence shown. The full licence texts are in each package's distribution (for example `site-packages/<pkg>*.dist-info/`, `node_modules/<pkg>/LICENSE`) or at the linked upstream repository.

**Last updated:** 2026-11-06 (Phase 1)
**Section A** lists components **currently used**.
**Section B** lists components **planned but not yet integrated**. An entry moves to A only when its code is merged, and its licence must be re-verified at that time.

---

## A. Components currently in use

### A.1 Backend (Python): `backend/requirements.txt`

| Component | Licence | Upstream |
|---|---|---|
| FastAPI | MIT | https://github.com/fastapi/fastapi |
| Starlette (via FastAPI) | BSD-3-Clause | https://github.com/encode/starlette |
| Uvicorn | BSD-3-Clause | https://github.com/encode/uvicorn |
| Pydantic | MIT | https://github.com/pydantic/pydantic |
| pydantic-settings | MIT | https://github.com/pydantic/pydantic-settings |
| SQLAlchemy | MIT | https://github.com/sqlalchemy/sqlalchemy |
| psycopg2-binary | LGPL-3.0 (with exceptions) | https://github.com/psycopg/psycopg2 |
| redis-py | MIT | https://github.com/redis/redis-py |
| HTTPX | BSD-3-Clause | https://github.com/encode/httpx |
| python-multipart | Apache-2.0 | https://github.com/Kludex/python-multipart |
| python-dotenv (transitive) | BSD-3-Clause | https://github.com/theskumar/python-dotenv |
| AnyIO (transitive) | MIT | https://github.com/agronholm/anyio |
| pytest (development only) | MIT | https://github.com/pytest-dev/pytest |

### A.1b Backend Phase 1 additions (storage, migrations, CPU conversion engines)

| Component | Licence | Upstream | Notes |
|---|---|---|---|
| Alembic (+ Mako) | MIT | https://github.com/sqlalchemy/alembic | Schema migrations |
| boto3 / botocore | Apache-2.0 | https://github.com/boto/boto3 | S3-compatible storage client |
| faster-whisper | MIT | https://github.com/SYSTRAN/faster-whisper | Speech-to-text |
| CTranslate2 | MIT | https://github.com/OpenNMT/CTranslate2 | Inference runtime for Whisper |
| OpenAI Whisper model weights (tiny, base; CTranslate2 conversions by Systran) | MIT | https://huggingface.co/Systran | Downloaded at runtime to MODEL_CACHE_DIR, never committed |
| PyAV (`av`) | BSD-3-Clause; wheels bundle FFmpeg libraries (LGPL) | https://github.com/PyAV-Org/PyAV | Dependency of faster-whisper |
| ONNX Runtime | MIT | https://github.com/microsoft/onnxruntime | Runs Kokoro TTS and Whisper VAD |
| huggingface_hub, tokenizers | Apache-2.0 | https://github.com/huggingface | Model download / tokenisation |
| kokoro-onnx | MIT | https://github.com/thewh1teagle/kokoro-onnx | TTS runtime |
| Kokoro-82M weights (`kokoro-v1.0.int8.onnx`, `voices-v1.0.bin`) | Apache-2.0 | https://huggingface.co/hexgrad/Kokoro-82M | Downloaded at runtime, never committed |
| **phonemizer** | **GPL-3.0-or-later** | https://github.com/bootphon/phonemizer | Imported in-process by kokoro-onnx. Hosted use only; see LICENSE_AUDIT.md §4 |
| espeakng-loader (bundles **espeak-ng**, GPL-3.0) | MIT wrapper / GPL-3.0 library | https://github.com/thewh1teagle/espeakng-loader | Phonemisation backend |
| pytesseract | Apache-2.0 | https://github.com/madmaze/pytesseract | OCR wrapper |
| Tesseract OCR (system binary; Docker `tesseract-ocr` package) | Apache-2.0 | https://github.com/tesseract-ocr/tesseract | Invoked as a separate process |
| Pillow | MIT-CMU (HPND) | https://github.com/python-pillow/Pillow | Image processing |
| NumPy | BSD-3-Clause (+ bundled permissive licences) | https://github.com/numpy/numpy | |
| tqdm (transitive) | MPL-2.0 AND MIT | https://github.com/tqdm/tqdm | |
| moto (tests only) | Apache-2.0 | https://github.com/getmoto/moto | In-process S3 fake |

### A.1c Optional hosted AI models (called over HTTPS only when AI_PROVIDER is configured; not bundled)

| Model | Licence | Used for |
|---|---|---|
| FLUX.1-schnell (Black Forest Labs) | Apache-2.0 | Text→image in AI modes |
| LLaVA-1.5-7B (via Cloudflare Workers AI) | Llama 2 Community License | Image description (Cloudflare provider) |
| BLIP image captioning large (Salesforce) | BSD-3-Clause | Image description (Hugging Face provider) |

Provider terms of service (Cloudflare, Hugging Face) apply to those requests. AI outputs are marked `ai_generated: true`.

### A.2 Worker (Python): `worker/requirements.txt`
redis-py (MIT), pydantic-settings (MIT), psycopg2-binary (LGPL-3.0). See above.

### A.3 Frontend (JavaScript/TypeScript): `frontend/package.json`

| Component | Licence | Upstream |
|---|---|---|
| Next.js | MIT | https://github.com/vercel/next.js |
| React, React-DOM | MIT | https://github.com/facebook/react |
| lucide-react | ISC | https://github.com/lucide-icons/lucide |
| Tailwind CSS | MIT | https://github.com/tailwindlabs/tailwindcss |
| PostCSS | MIT | https://github.com/postcss/postcss |
| Autoprefixer | MIT | https://github.com/postcss/autoprefixer |
| TypeScript (dev) | Apache-2.0 | https://github.com/microsoft/TypeScript |
| ESLint, eslint-config-next (dev) | MIT | https://github.com/eslint/eslint |
| Inter typeface (via `next/font/google`) | SIL Open Font License 1.1 | https://github.com/rsms/inter |

### A.4 System software

| Component | Licence | Notes |
|---|---|---|
| **FFmpeg** | LGPL-2.1-or-later; the builds used (Debian `ffmpeg` package in the Dockerfiles, Gyan "essentials" build for local Windows development) are configured with GPL components and are therefore **GPL-2.0-or-later / GPL-3.0** | Invoked as a separate executable via `subprocess`; not linked into MultimediaToolKit. Source: https://ffmpeg.org/download.html · Legal: https://ffmpeg.org/legal.html |
| PostgreSQL (Docker image `postgres:16-alpine`) | PostgreSQL Licence | https://www.postgresql.org |
| Redis (Docker image `redis:7-alpine`) | BSD-3-Clause (Redis 7.x) | https://github.com/redis/redis |
| Debian base image `python:3.11-slim` | Various OSS licences | https://hub.docker.com/_/python |

> **If Docker images are ever distributed publicly:** they will contain FFmpeg (GPL). The image must then include FFmpeg's licence text and a written offer of, or link to, the corresponding source code for the exact version shipped.

---

## B. Planned components (not yet integrated; listed for transparency)

| Component | Role | Licence (to re-verify at integration) |
|---|---|---|
| RapidOCR + PaddleOCR models | OCR | Apache-2.0 |
| Florence-2 weights (Microsoft) | Image captioning | MIT |
| Moondream2 weights | Visual Q&A | Apache-2.0 |
| SmolVLM2 weights | Multi-frame description | Apache-2.0 |
| Qwen3 weights · llama.cpp / llama-cpp-python | Text LLM | Apache-2.0 · MIT |
| FLUX.1-schnell weights (Black Forest Labs) | Text-to-image (GPU) | Apache-2.0 |
| Stable Diffusion 1.5 · LCM-LoRA | Text-to-image (CPU) | CreativeML OpenRAIL-M · OpenRAIL++ (use-based restrictions apply, see the Acceptable Use Policy) |
| FastSD CPU | CPU diffusion runtime | MIT |
| Wan2.1 / Wan2.2 weights (Wan Team, Alibaba) | Text/image-to-video | Apache-2.0 |
| AnimateDiff motion modules | Animation | Apache-2.0 |
| Depth-Anything-V2-**Small** | Depth for parallax | Apache-2.0 |
| YAMNet | Audio tagging | Apache-2.0 |
| librosa | Audio analysis | ISC |
| PySceneDetect | Scene detection | BSD-3-Clause |
| OpenCV | Image/video processing | Apache-2.0 |
| Real-ESRGAN | Upscaling | BSD-3-Clause |
| Practical-RIFE | Frame interpolation | MIT |
| Hugging Face Diffusers / Transformers | Model runtime | Apache-2.0 |
| PyTorch | Model runtime | BSD-3-Clause |
| ONNX Runtime · OpenVINO | CPU inference | MIT · Apache-2.0 |

---

## C. AI-generated content
Outputs produced by AI models are labelled as AI-generated in the application. Use of the OpenRAIL-licensed models is subject to the use-based restrictions in their licences. Those restrictions are passed on to users through the MultimediaToolKit Acceptable Use Policy.
