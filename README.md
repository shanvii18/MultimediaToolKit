# MultimediaToolKit

Convert anything into anything: **5 formats (Text, Image, Audio, Video, Animation) and 20 directed conversions**. Each one does a real operation and produces a real downloadable file.

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind, dark and light mode, responsive
- **Backend:** FastAPI, SQLAlchemy 2, Alembic, PostgreSQL (SQLite for local dev), a durable DB-backed job queue (optional Redis wake-ups), and S3-compatible storage
- **Engines:** FFmpeg, faster-whisper, Kokoro-82M TTS, Tesseract OCR and Pillow, all on CPU. An optional hosted AI provider (Cloudflare Workers AI or Hugging Face) handles generative image models and image description.

**Live demo:** https://multimedia-tool-kit.vercel.app (free account: sign up with email and password) · **API:** https://mtk-backend.onrender.com/health · **Presenting?** See [DEMO_GUIDE.md](DEMO_GUIDE.md)

---

## The 20 conversions

Each conversion has at least one **CPU mode that always works**. *AI modes* need an AI provider to be configured (see [AI provider](#ai-provider-optional)). Without one they say so and are never faked.

| # | Conversion | CPU modes | AI modes (provider) |
|---|---|---|---|
| 1 | Text → Audio | Kokoro neural TTS (9 voices, MP3/WAV/OGG/FLAC/M4A) | n/a |
| 2 | Audio → Text | Whisper transcript as TXT/SRT/VTT/JSON | n/a |
| 3 | Video → Text | FFmpeg + Whisper | n/a |
| 4 | Video → Audio | FFmpeg extraction (5 formats) | n/a |
| 5 | Animation → Text | On-screen text (Tesseract) + speech (Whisper) | Describe visuals |
| 6 | Animation → Audio | Extract soundtrack · read on-screen text aloud | Narrate visuals |
| 7 | Text → Image | Typography poster | AI image (FLUX.1-schnell) |
| 8 | Text → Video | Narrated scene video (cards + Kokoro + Ken Burns + captions) | AI-illustrated scenes |
| 9 | Text → Animation | Kinetic typography GIF/WebP | AI image loop |
| 10 | Audio → Image | Waveform art · spectrogram | AI cover art (speech + mood → prompt) |
| 11 | Audio → Video | Waves / spectrum / bars visualiser + Whisper captions | Visualiser on AI art |
| 12 | Audio → Animation | Waveform loop · beat pulse | AI art pulse |
| 13 | Image → Text | OCR (Tesseract) | Describe image |
| 14 | Image → Audio | Read text aloud (OCR → TTS) | Describe in speech |
| 15 | Image → Video | Ken Burns camera motion | AI-narrated video |
| 16 | Image → Animation | Seamless motion loop | n/a |
| 17 | Video → Image | Frame picker + edits · best frame · poster | AI poster |
| 18 | Video → Animation | Palette GIF/WebP, effects (cartoon, vintage, B&W), boomerang | n/a |
| 19 | Animation → Image | Best frame · poster · contact sheet | n/a |
| 20 | Animation → Video | MP4/WebM, loops, motion smoothing | n/a |

The live status of every conversion and mode on a given server is available at `GET /api/v1/conversions`. If an engine is missing (for example Tesseract), the UI shows **"Engine not installed"** and the API refuses the job with 503.

## Features
- **Conversion workspace** (`/convert/[id]`), generated from the backend registry: drag-and-drop upload, local preview (scrub a video to pick a frame), mode and settings forms, live progress with step messages, and audio, image and text previews with downloads.
- **Conversion history** (`/jobs`) with filters, errors and all output files. **Projects and media library** (`/projects`) with search, type filter, previews and delete.
- **Public accounts:** anyone can sign up with an email and password (scrypt-hashed). Sign-in issues a random,
  expiring session token, stored hashed. Sign-up and sign-in are rate-limited. Every user sees only their own
  files, jobs and history, and downloads use short-lived signed links.
- **Reliability:** durable job queue with leases, heartbeats and automatic recovery; FFmpeg timeouts; honest error codes (`NO_SPEECH`, `NO_AUDIO`, `INPUT_TOO_LONG`, `AI_PROVIDER_ERROR`, …); failed jobs leave no partial files behind.
- **Security:** server-derived MIME types, `nosniff` and sandbox CSP on downloads, upload allow-list and size cap, path-traversal-safe storage keys, and refusal to start in production with an unsafe configuration.

## Architecture
```text
Next.js (Vercel)  ──HTTPS + Bearer key──►  FastAPI API ──► PostgreSQL (jobs = durable queue, Alembic)
                                              │  ▲                 ▲
                                              ▼  │ signed URLs     │ claim / heartbeat / recover
                                     S3-compatible storage   Worker (embedded thread or `python -m app.worker`)
                                     (local disk in dev)        └─ registry → pipelines → adapters:
                                                                   FFmpeg · Whisper · Kokoro · Tesseract ·
                                                                   Pillow graphics/motion · AI provider (opt.)
```
Code map: `backend/app/engines/registry.py` (the 20 conversions), `backend/app/engines/pipelines/` (workflows), `backend/app/adapters/` (engines), `frontend/src/app/convert/` (workspace UI).

## Local development

### Backend
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# optional: keep model weights off the system drive
echo MODEL_CACHE_DIR=D:/MultimediaToolKit/models > .env
python -m app.cli download-models                      # Whisper tiny+base, Kokoro (~330 MB)
uvicorn app.main:app --reload                           # http://localhost:8000/docs
```
System tools: **FFmpeg** (required) and **Tesseract** (for OCR modes; Windows: `winget install UB-Mannheim.TesseractOCR`). Migrations run automatically at start-up (`alembic upgrade head` also works). In development, requests without a key act as a local developer user.

### Frontend
```bash
cd frontend
npm install
set NEXT_PUBLIC_API_URL=http://localhost:8000            # macOS/Linux: export ...
npm run dev                                              # http://localhost:3000
```

### Docker (full stack)
```bash
docker compose up --build     # postgres, redis, backend (API), worker, frontend
```

### Tests
```bash
cd backend && pytest            # backend + workflow tests (real FFmpeg/Whisper/Kokoro; AI provider mocked)
cd frontend && npx tsc --noEmit && npm run lint && npm run build
```

## Configuration
All settings are environment variables; see [`.env.example`](.env.example). The important ones:

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | `development` or `production` (production requires sign-in, PostgreSQL and a signing secret) |
| `DATABASE_URL` | PostgreSQL URL (use a non-expiring one, for example Neon free tier) |
| `SIGNING_SECRET` | ≥ 32 random characters, used for signed download links |
| `ALLOWED_ORIGINS` | Your frontend origin(s) |
| `STORAGE_BACKEND` | `local` or `s3` (+ `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`) |
| `MODEL_CACHE_DIR` | Where Whisper/Kokoro weights are stored |
| `AI_PROVIDER` | `none` (default), `cloudflare` or `huggingface` |
| `QUEUE_NOTIFY_REDIS` | `true` to wake workers instantly through Redis (`REDIS_URL`) |

### AI provider (optional)
- **Cloudflare Workers AI** (has a free daily allowance): `AI_PROVIDER=cloudflare`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` (Workers AI permission). Models: `@cf/black-forest-labs/flux-1-schnell` (images), `@cf/llava-hf/llava-1.5-7b-hf` (description).
- **Hugging Face Inference**: `AI_PROVIDER=huggingface`, `HF_API_TOKEN`. Models: `black-forest-labs/FLUX.1-schnell`, `Salesforce/blip-image-captioning-large`.

AI usage counts against your provider account. Outputs are marked `ai_generated` in their metadata.

### Accounts
Users create their own accounts on the website (`/login` → **Create account**). API:
`POST /api/v1/auth/signup`, `POST /api/v1/auth/login` (both return a bearer token), and `POST /api/v1/auth/logout`.
Every other `/api/v1` route requires `Authorization: Bearer <token>`.

Admin helpers:
```bash
cd backend
python -m app.cli list-users
python -m app.cli set-password --email owner@example.com   # give an existing account a password
python -m app.cli revoke --email someone@example.com       # sign a user out everywhere
```

## Deployment (all free tiers)

| Part | Service | Notes |
|---|---|---|
| Frontend | **Vercel Hobby** | Root directory `frontend`. `NEXT_PUBLIC_API_URL=https://mtk-backend.onrender.com` (applied at build time) |
| Backend | **Render Free** (Docker, Oregon) | [`render.yaml`](render.yaml), 512 MB RAM, sleeps after 15 min idle (~1 min cold start) |
| Database | **Neon Free** PostgreSQL 18 (Oregon, pooled) | Persistent; Alembic migrations run automatically at start-up |
| Files | Render local `/tmp/storage` | Temporary: cleared on restart or sleep. Old downloads return 410 Gone |

Backend environment (set in the Render dashboard; secrets never committed):
- **Secrets and URLs:** `DATABASE_URL` (Neon pooled URL), `SIGNING_SECRET` (random, at least 32 characters),
  `ALLOWED_ORIGINS` and `FRONTEND_URL` (the Vercel URL).
- **Mode:** `ENVIRONMENT=production`, `AUTH_MODE=access_key`, `EMBEDDED_WORKER=true`.
- **Storage:** `STORAGE_BACKEND=local`, `STORAGE_DIR=/tmp/storage`.
- **512 MB tuning:** `WHISPER_DEFAULT_MODEL=tiny`, `KEEP_MODELS_LOADED=false`,
  `FFMPEG_THREADS=2`, `WHISPER_CPU_THREADS=2`, `TTS_CPU_THREADS=2`.
- **AI:** `AI_PROVIDER=none`.

With these settings, all 20 conversions measured at or below ~450 MB peak on short inputs. Long media may still
exceed 512 MB on the free plan. See [DEPLOYMENT_PROGRESS.md](DEPLOYMENT_PROGRESS.md) for the migration record and limits.

## Licences
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [LICENSE_AUDIT.md](LICENSE_AUDIT.md). All bundled engines and models are permissively licensed. Note: `phonemizer`/`espeak-ng` (used by Kokoro) are GPL-3.0, which is fine for hosting, but don't publish Docker images without reviewing LICENSE_AUDIT.md §4.1.
