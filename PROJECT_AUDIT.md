# PROJECT_AUDIT.md — MultimediaToolKit Repository Audit

**Status update:** P0/P1 findings 4.1–4.10 were fixed in **Phase 0**, except 4.5 (storage): a plan is written but storage is still ephemeral. See PROJECT_STATUS.md §2 and §5.
**Audit date:** 2026-11-06
**Branch audited:** `dev/multimedia-toolkit-upgrade` (identical to `main` @ `57bc6d4`, synced with `origin/main`)
**Method:** I read every tracked source file. I ran the backend test suite against an isolated scratch database and storage folder, so local data was not touched, and type-checked the frontend with `tsc --noEmit`. I changed no application code.

---

## 1. Executive summary

| Area | Verdict |
|---|---|
| Backend API (FastAPI) | Solid, small and readable. **15/15 tests pass**, including a real FFmpeg end-to-end test. |
| Video → Audio | **Works** (verified by test and by reading the code). It has two bugs (§4). |
| Idea → Storyboard | **Works**, but it is a **deterministic keyword/template engine, not AI**. |
| Projects / Assets / Jobs | **Work** (create/list/upload/download/poll). There is **no user ownership**, so every visitor sees every file. |
| Worker service | **Stub.** It connects to Redis and logs a heartbeat. It processes nothing. |
| Redis | Defined in Docker Compose, but **nothing uses it**. |
| Frontend | Compiles cleanly (`tsc` exit 0). **12 of 17 components are unused** dead code. The catalog shows 20 *old* modules, 10 of them badged "Integrated" with **no backend implementation**. |
| Deployment config | It would deploy, but jobs run inside the web process, storage is ephemeral `/tmp`, and Render's free Postgres expires. **Not suitable for real users yet.** |
| Of the 20 target conversions | **1 implemented** (Video→Audio). 19 still to build. |

**Conclusion:** the foundation is worth keeping: the data model, storage service, job state machine, FFmpeg adapter, test suite and app shell. The product layer, meaning the 20 conversions, the worker, ownership and durable storage, has to be built on top of it. **No rebuild from scratch is needed.**

---

## 2. Architecture as it exists today

```text
Browser (Next.js 14 App Router, client components)
   │  fetch() → NEXT_PUBLIC_API_URL
   ▼
FastAPI (backend/app)
   ├─ /health                      → always {"status":"ok"}
   ├─ /api/v1/projects  (CRUD-lite)
   ├─ /api/v1/media     (multipart upload → StorageService)
   ├─ /api/v1/assets[/id][/download]
   └─ /api/v1/jobs      → DB row + FastAPI BackgroundTasks → JobRunnerService
                                                         ├─ idea_to_storyboard → StoryboardAdapter (templates)
                                                         └─ video_to_audio     → FFmpegAdapter (subprocess)
   │
   ├─ SQLAlchemy 2 → PostgreSQL (or SQLite fallback, see §4.6)
   └─ Local disk  → backend/storage/<uuid>.<ext>

worker/ (separate container) → Redis ping + heartbeat loop only
```

### 2.1 Data model ([entities.py](backend/app/models/entities.py))
`users`, `projects`, `assets`, `jobs`, `job_outputs`, `usage_events`. This is a good, reusable schema. `Job` already has `tool`, `status`, `progress`, `input_asset_ids`, `params_json`, `error_code` and `error_message`, which is exactly what a multi-step pipeline worker needs. `User` and `UsageEvent` exist but **nothing reads or writes them**.

### 2.2 API surface ([router.py](backend/app/api/v1/router.py))

| Method & path | Status |
|---|---|
| `GET /health` | Works, but it hides DB failure (always returns `ok`) |
| `GET /` | Works |
| `POST/GET /api/v1/projects`, `GET /projects/{id}`, `GET /projects/{id}/assets` | Works |
| `POST /api/v1/media` | Works: streaming write, 100 MB cap, extension allow-list, SHA-256 |
| `GET /api/v1/assets`, `/assets/{id}` | Works, but **global**: lists every user's files |
| `GET /api/v1/assets/{id}/download` | Works, but has a **security issue** (§4.1) |
| `POST /api/v1/jobs` | Works for `idea_to_storyboard` and `video_to_audio`. Any other tool name is accepted and then fails with `NotImplementedError` |
| `GET /api/v1/jobs`, `/jobs/{id}` | Works, global |

There are no endpoints for: auth, deleting an asset, cancelling a job, listing tools, or quotas.

### 2.3 Frontend routes

| Route | What it really does |
|---|---|
| `/` | Dashboard. Lists projects and jobs from the API (works) |
| `/modules` | Searchable catalog of the **old** 20-module concept (static data in [modulesCatalog.ts](frontend/src/services/modulesCatalog.ts)) |
| `/modules/[slug]` | Spec page. "Launch" only for `operational` modules, otherwise an honest roadmap notice |
| `/workspace?tool=idea-to-storyboard` | Works end to end |
| `/workspace?tool=media-extractor` | Works end to end (upload → job → poll → MP3 preview and download) |
| `/projects` | Create project, list assets, download (works) |
| `/jobs` | Polls every 4 s, status table, download (works) |

---

## 3. Feature status matrix (checked against the code)

### 3.1 Target product: 20 directed conversions

| # | Conversion | Category | Status | Evidence |
|---|---|---|---|---|
| 1 | Text → Audio | Normal | ❌ Not started | No TTS code |
| 2 | Audio → Text | Normal | ❌ Not started | Catalog says "Whisper adapter", but no code exists |
| 3 | Video → Text | Normal | ❌ Not started | — |
| 4 | **Video → Audio** | Normal | ✅ **Working** | `ffmpeg_adapter.extract_audio` + `test_media_extractor_end_to_end` passes |
| 5 | Animation → Text | Normal | ❌ | — |
| 6 | Animation → Audio | Normal | ❌ | (FFmpeg extraction would handle GIF/MP4 *with* audio; untested) |
| 7–20 | All generative conversions | Generative | ❌ Not started | No model code, no worker, no GPU path |

**Existing assets to reuse:**
- `StoryboardAdapter`: a scene planner for Text → Video and Text → Animation.
- `FFmpegAdapter`: the base media engine.
- `StorageService`, `JobRunnerService`, `Job`/`JobOutput`: the pipeline backbone.

### 3.2 Platform features

| Feature | Status |
|---|---|
| Project workspace & media library | ✅ Works (no ownership) |
| Job monitor & export | ✅ Works (polling; no cancel/retry) |
| Upload validation & integrity | ✅ Works (size, extension, empty file, checksum) |
| Path-traversal protection | ✅ `basename` + `abspath` prefix check |
| Authentication / accounts | ❌ The `User` table exists. `SignInModal.tsx` is an **unused fake** (`setTimeout`) |
| Quotas / rate limits | ❌ (needed before any GPU feature goes public) |
| Background worker / queue | ❌ Stub only |
| Durable object storage | ❌ Local disk only |
| DB migrations | ❌ `Base.metadata.create_all()` at import time |
| Observability | ❌ No structured logs, metrics or error tracking |

---

## 4. Bugs, risks and broken behaviour (by severity)

### P0: fix before real users

**4.1 Client-controlled `Content-Type` stored and served back on download.**
The original code stored `file.content_type` exactly as the browser sent it and served the file back with that type.

> **Correction (2026-11-06, during Phase 0):** this audit first said the response had no `Content-Disposition: attachment` and that the file would be "rendered as HTML". That was wrong. Starlette's `FileResponse` adds `attachment` by default when a filename is given, so a browser *navigating* to the URL downloads the file instead of rendering it. The real issues were an attacker-controlled MIME type in the DB and API, no `nosniff`, and no sandbox. Severity is lower than first stated, but it was still fixed.

*Fixed in Phase 0:* the MIME type is derived server-side, with explicit `attachment`, `X-Content-Type-Options: nosniff` and `Content-Security-Policy: default-src 'none'; sandbox`.

**4.2 No ownership, so all user data is public to all users.**
`/assets`, `/jobs` and `/projects` return every row. With 10–20 real users, each one could see and download everyone's uploads.

**4.3 Jobs run inside the web process (`BackgroundTasks`).**
A restart, deploy or Render free-tier sleep (after 15 min idle) kills running jobs. They stay `running` forever, because nothing recovers them. Long AI jobs would also block web workers.

**4.4 Silent PostgreSQL → SQLite fallback in production.**
[database.py:19-31](backend/app/core/database.py#L19-L31): if Postgres is unreachable at boot, the app silently switches to a local SQLite file. On Render that file is on an ephemeral disk, which means silent data loss and a split database. This should only be allowed when `ENVIRONMENT=development`.

**4.5 Ephemeral storage in production.**
`render.yaml` sets `STORAGE_DIR=/tmp/storage`. Files vanish on every restart while their DB rows remain, so downloads return "Physical asset file missing on disk".

### P1: correctness

**4.6 `audio_format` bug in Video→Audio.**
[ffmpeg_adapter.py:90](backend/app/adapters/ffmpeg_adapter.py#L90): any format other than `mp3` uses `-acodec copy`, but the output path is always `audio_<id>.mp3` ([job_runner_service.py:118](backend/app/services/job_runner_service.py#L118)). That stream-copies AAC/Opus into an `.mp3` container, which fails or produces a mislabelled file, and the metadata always says `"mp3"`. The UI currently only sends `mp3`, so it's latent. Fix it before adding WAV/M4A/OGG options.

**4.7 No FFmpeg timeout.**
`subprocess.run` without `timeout=` means a malformed or very long file can hang a job forever.

**4.8 `/health` always reports OK**, even when the DB is down. The exception is swallowed at [health.py:17-18](backend/app/api/routes/health.py#L17-L18).

**4.9 CORS:** `ALLOWED_ORIGINS="*"` plus `allow_credentials=True`. In this configuration Starlette reflects any origin for credentialed requests. That's harmless today (no cookies) but dangerous once auth is added. `render.yaml` ships `"*"` to production.

**4.10 Tests are not isolated.**
`test_api.py` writes to the real dev database and `backend/storage/`. That explains the ~45 leftover `.mp4`, `.mp3` and `.json` files in local storage. The suite needs a `conftest.py` with temp DB and storage fixtures.

### P2: quality and maintainability

- `datetime.utcnow()` (deprecated in Python 3.12+) is used throughout the models and runner.
- `NotImplementedError` for unknown tools happens *after* the job row is created. Validate against a tool registry instead.
- No Alembic migrations. Schema changes will break existing Postgres databases.
- *(Corrected in Phase 0 by an import-graph check: **16 of 17** components are unreachable. See PROJECT_STATUS.md §9.)* Unused components: `Hero`, `Navbar`, `Footer`, `FeatureHighlights`, `AudioToTextSection`, `ImageToTextSection`, `VideoToAudioSection`, `WorkflowPipeline`, `FinalCta`, `SignInModal`, `UploadModal` (fake progress with `setTimeout`), `StudyModeShowcase` and `WorkspaceShowcase`, plus their helpers `GradientRibbon`, `ThemeProvider` and `AudioWaveform`. They are left over from the earlier "Study Mode" concept.
- **Honesty gap in the UI and docs:** 10 catalog modules (PDF Studio, Image/Audio/Video Converter, OCR, Subtitles, Text-to-Image, TTS, Thumbnails, Multi-step Pipeline) carry the badge **"Integrated Utility"** even though no backend code exists. `PROJECT_STATUS.md` claims "Integrated Adapter" for Speech-to-Text and "4 tests" (there are 15). Both contradict the project's "zero fake success" principle.
- The old 20-module catalog doesn't match the new **5-format × 20-conversion** vision and will be replaced.
- Next.js **14.2.35** is out of active support. Plan an upgrade to the current LTS line during the UI phase, not before.
- [workspace/page.tsx](frontend/src/app/workspace/page.tsx) is a 600-line single component hard-coding two tools. It won't scale to 20 workflows, so a generic workspace driven by a tool registry is needed.
- The repo has no `LICENSE` file (see LICENSE_AUDIT.md §1).

---

## 5. Verification evidence

```text
Backend: python -m pytest -q (DATABASE_URL + STORAGE_DIR → scratch dir)
  15 passed, 1 warning in 7.05s
  (includes test_media_extractor_end_to_end — real FFmpeg 9.0.1 on this machine)
Frontend: node_modules/.bin/tsc --noEmit -p frontend   → exit 0, no errors
Environment: Python 3.11.9 venv; FastAPI 0.142.4; SQLAlchemy 2.1.4; Pydantic 2.13.5;
             Node 24.16.0; Next 14.2.35; FFmpeg 9.0.1 (WinGet Gyan essentials build)
```
I did not run `npm run build` or `docker compose` in this audit (no installs or containers were allowed).

---

## 6. What to keep, change and remove

| Keep as-is | Keep but harden | Replace / remove later (with your approval) |
|---|---|---|
| Entity model, Pydantic schemas | `StorageService`: add a pluggable S3/R2 backend | Old 20-module catalog → new 20-conversion registry |
| `FFmpegAdapter` (extend it) | `JobRunnerService` → move it into the worker and make it pipeline-step based | 12 unused landing-page components |
| `StoryboardAdapter` (as scene planner) | Download endpoint (§4.1) | Fake `SignInModal` / `UploadModal` |
| Test suite (add isolation) | DB fallback (dev-only) | Overclaiming text in `PROJECT_STATUS.md` |
| AppShell, `/projects`, `/jobs` pages | CORS, health, timeouts | — |
