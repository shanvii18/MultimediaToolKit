# PROJECT_STATUS.md — MultimediaToolKit Engineering Status

**Last updated:** 2026-11-06 · **Branch:** `dev/multimedia-toolkit-upgrade`
**Current phase:** ✅ Phase 0 (hardening) complete · ✅ Phase 1 (storage, migrations, engine architecture, first 8 workflows) complete.
**Companion documents:** [PROJECT_AUDIT.md](PROJECT_AUDIT.md) · [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) · [GITHUB_REPOSITORY_RESEARCH.md](GITHUB_REPOSITORY_RESEARCH.md) · [LICENSE_AUDIT.md](LICENSE_AUDIT.md) · [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

> This file replaces the earlier status page, which over-stated progress. It claimed "Integrated Adapter" for features with no code and "4 tests". Everything below has been verified by reading the code and running the tests.

---

## 1. Product status: 20 target conversions

| # | Conversion | Status | Engine(s) | Verified on this machine |
|---|---|---|---|---|
| 1 | **Text → Audio** | ✅ Working | Kokoro-82M (kokoro-onnx, int8, CPU) + FFmpeg | ✅ real model |
| 2 | **Audio → Text** | ✅ Working (TXT, SRT, VTT, JSON) | faster-whisper tiny/base/small (int8, CPU) | ✅ real model |
| 3 | **Video → Text** | ✅ Working | FFmpeg → faster-whisper | ✅ real model |
| 4 | **Video → Audio** | ✅ Working (MP3/WAV/M4A/OGG/FLAC) | FFmpeg | ✅ |
| 5 | **Animation → Text** | ✅ Working: on-screen text (OCR) + speech (Whisper). *Visual description: coming soon* | Pillow/FFmpeg frames → Tesseract; Whisper | ✅ speech path real; OCR path via stub engine (Tesseract not installed here) |
| 6 | **Animation → Audio** | ✅ Working: soundtrack extraction, or read on-screen text aloud. *Narration: coming soon* | FFmpeg; Tesseract → Kokoro | ✅ soundtrack real; read-aloud via stub OCR + real TTS |
| 13 | **Image → Text** | ✅ OCR mode working. *AI description: coming soon* | Tesseract | ⚠️ needs Tesseract installed (tests skip, never fake) |
| 14 | **Image → Audio** | ✅ Read-aloud mode working. *Describe-in-speech: coming soon* | Tesseract → Kokoro | ⚠️ needs Tesseract; pipeline verified with stub OCR + real TTS |
| 17 | **Video → Image** | ✅ Frame picker + edits (rotate, crop, brightness, contrast, B&W, resize, PNG/JPG/WebP) and best-frame auto pick. *AI poster: coming soon* | FFmpeg + Pillow | ✅ |
| 7–12, 15, 16, 18–20 | Text→Image/Video/Animation, Audio→Image/Video/Animation, Image→Video/Animation, Video→Animation, Animation→Image/Video | ⬜ **Coming soon** (rejected by the API, labelled in the UI) | — | — |

**9 of 20 conversions run real engines.** Availability is computed live per server (`GET /api/v1/conversions`): if an engine is missing, the conversion shows **"Engine not installed"** and jobs are refused with 503. They never fake a result.

---

## 1b. Phase 1: what was built
- **Persistent storage abstraction** ([storage_service.py](backend/app/services/storage_service.py)): `LocalStorageBackend` (dev/tests) and `S3StorageBackend` (any S3-compatible bucket: Backblaze B2, Cloudflare R2, MinIO, AWS). Server-generated keys with strict validation, presigned downloads that force the content type and attachment, honest 410 when an object is gone. Switch with `STORAGE_BACKEND=s3`. **No paid service is activated.**
- **Alembic migrations** ([backend/migrations](backend/migrations)): `0001_baseline` plus `0002_job_progress_message`. They run automatically at API, worker and CLI start-up. Pre-Alembic databases are detected, completed and stamped, with no data loss (verified on a copy of the dev DB: 27 legacy jobs preserved). A test asserts models and migrations stay in sync (`alembic check` equivalent).
- **Conversion engine architecture** ([backend/app/engines](backend/app/engines)): a central **registry** of all 20 conversions (modes, parameters, accepted inputs, required engines), **reusable adapters** (FFmpeg, Whisper, Kokoro TTS, Tesseract OCR, Pillow image ops), composable **pipelines**, a `JobContext` (progress messages, input materialisation from storage, output registration, cleanup on failure), live engine availability, and the public catalogue `GET /api/v1/conversions`.
- **Frontend**: `/convert` (5-format catalogue with live status) and `/convert/[id]`, a generic workspace generated from the registry (modes, parameters, upload or text input, video scrubbing for frame picking, live progress, audio, image and text previews, downloads). The legacy `/modules` catalogue no longer claims "Integrated" for unbuilt modules. The existing `/workspace` (Video→Audio, Storyboard), `/projects` and `/jobs` are unchanged.
- **Models on D:** `backend/.env` (gitignored) sets `MODEL_CACHE_DIR=D:/MultimediaToolKit/models` and `WORK_DIR=D:/MultimediaToolKit/work`. Hugging Face caches are redirected there too. `python -m app.cli download-models` pre-fetches the weights.

**Measured on this laptop (i5-1235U, CPU only):** Text→Audio about 9 s for a 2-sentence MP3 (including model load); Audio→Text (Whisper base) about 8 s for that clip; the full test suite runs in about 66 s.

**Tests:** 95 passed, 4 skipped. The 4 skips are the real-Tesseract tests, because Tesseract isn't installed on this host.

## 2. Phase 0: what changed

### 2.1 Security fixes
| # | Issue (audit ref) | Fix |
|---|---|---|
| S1 | Client-controlled `Content-Type` stored and served back on download (4.1) | MIME type is now derived server-side from the allow-listed extension, at upload **and** at download (so old rows with bad values are also neutralised). Downloads add `X-Content-Type-Options: nosniff`, `Content-Security-Policy: default-src 'none'; sandbox` and `Content-Disposition: attachment`. SVG is served as a sandboxed attachment |
| S2 | No ownership: every visitor saw every project/asset/job (4.2) | Invite-only **personal access keys** (only SHA-256 hashes stored; created and revoked with a CLI). Every project/asset/job query is filtered by owner. Using another user's asset in a job returns 404. Production refuses to start without access-key mode |
| S3 | Downloads had no access control | **Short-lived signed download URLs** (HMAC-SHA256, 1 h default) returned as `download_url`, because `<a>` and `<audio>` can't send headers. Tampered, expired or cross-asset signatures return 403 |
| S4 | CORS `*` together with credentials (4.9) | Credentials are never allowed cross-origin (auth uses a header, not cookies); methods and headers restricted. `render.yaml` now requires explicit origins |
| S5 | Unsafe production configuration was possible | Startup validation: `SIGNING_SECRET` (≥ 32 chars) is required outside development, `dev_open` is forbidden outside development, SQLite is forbidden outside development |

### 2.2 Reliability fixes
| # | Issue (audit ref) | Fix |
|---|---|---|
| R1 | Jobs ran inside the web request (`BackgroundTasks`); lost on restart and stuck "running" forever (4.3) | **Durable DB-backed queue.** Jobs are persisted as `queued` and claimed atomically by a worker (`FOR UPDATE SKIP LOCKED` on Postgres, conditional UPDATE on SQLite). A `job_leases` table holds heartbeats. Abandoned jobs are re-queued (up to 2 attempts), then failed with `WORKER_LOST`. Legacy stuck jobs are recovered too. The worker runs **embedded** in the API (Render Free, local dev) or **standalone** (`python -m app.worker`, used by docker-compose) |
| R2 | Silent PostgreSQL → SQLite fallback in production (4.4) | The fallback works only when `ENVIRONMENT=development`. Production fails loudly at startup if Postgres is unreachable. `pool_pre_ping` added for serverless Postgres |
| R3 | `/health` always returned OK (4.8) | Returns **503** `{"status":"error","database":"unreachable"}` when the DB is down. Unchanged `{"status":"ok"}` when healthy |
| R4 | Video→Audio stream-copied non-MP3 formats into a `.mp3` file (4.6) | Per-format codec and container: mp3/libmp3lame, wav/pcm_s16le, m4a/aac, ogg/libvorbis, flac/flac. Correct extension, MIME type, `output_type` and metadata. Unsupported formats are rejected with 400 before queuing |
| R5 | No FFmpeg timeout (4.7) | Hard timeout (`FFMPEG_TIMEOUT_SECONDS`, default 600 s): the process is killed, partial output deleted, and the job fails with `error_code=TIMEOUT` |
| R6 | Missing files gave a confusing 404 | **410 Gone** with a clear message (ephemeral storage reset) |
| R7 | Tests wrote into the real dev DB and `storage/` (4.10) | `conftest.py` isolates every run in a temp DB and storage directory |

### 2.3 Files changed
**Backend (modified):** `app/main.py`, `app/core/config.py`, `app/core/database.py`, `app/api/v1/router.py`, `app/api/routes/health.py`, `app/models/entities.py`, `app/models/__init__.py`, `app/schemas/schemas.py`, `app/services/job_runner_service.py`, `app/adapters/ffmpeg_adapter.py`, `app/tests/test_api.py` (one test now runs the queued job explicitly)
**Backend (new):** `app/core/security.py`, `app/core/media_types.py`, `app/api/deps.py`, `app/services/job_queue.py`, `app/worker/{__init__,__main__,runner}.py`, `app/cli.py`, `app/tests/conftest.py`, `app/tests/test_phase0_regressions.py`
**Frontend (logic only, no design change):** `src/services/apiClient.ts` (access-key header, invite-link capture, signed download URLs), `src/types/index.ts` (`download_url`), `src/app/{jobs,projects,workspace}/page.tsx` (download links use the signed URL)
**Config / docs:** `docker-compose.yml` (worker now runs the real queue, shared media volume), `render.yaml` (no expiring free Postgres, generated signing secret, explicit origins), `.env.example`, `PROJECT_STATUS.md`, `PROJECT_AUDIT.md` (corrections)

**Database schema:** two **new tables** only (`access_keys`, `job_leases`), created automatically. No existing column changed, so existing databases keep working without migrations. A smoke test on a copy of the local dev DB confirmed this.

### 2.4 Test evidence
```text
Backend  pytest (isolated temp DB/storage)       50 passed, 0 failed, 0 skipped
         ├─ 15 original tests (incl. real FFmpeg end-to-end)    all pass
         └─ 35 new Phase 0 regression tests                      all pass
Frontend tsc --noEmit                                           exit 0
         next lint                                              0 errors (1 pre-existing warning in an unused component)
Compose  docker compose config                                  valid
Smoke    uvicorn on a COPY of the dev DB: legacy data visible to dev user, new tables created,
         embedded worker processed a job, hardened download headers present, missing legacy file → 410
Config   production refuses: missing secret · dev_open · SQLite · unreachable Postgres   (verified)
```
Not run: `next build` (the machine had < 1 GB free RAM) and `docker compose up` (no containers started).

---

## 3. How access works now

| Environment | Behaviour |
|---|---|
| Local development (`ENVIRONMENT=development`, default) | **dev_open**: requests without a key act as a single local developer user, who also sees legacy data created before ownership existed. Nothing changes for local use |
| Production (`ENVIRONMENT=production`) | **access_key** is enforced. Every API call needs a valid key; downloads use signed links |

Invite a user (run in `backend/` with the production `DATABASE_URL` set in your shell):
```bash
python -m app.cli invite --email friend@example.com     # prints a one-time invite link
python -m app.cli list-users
python -m app.cli revoke --email friend@example.com
```
The invite link (`https://<frontend>/?access_key=…`) stores the key in the browser and removes it from the address bar. **Not yet built (deliberately):** sign-up, login, password reset or an access-key entry screen. These are for discussion before Phase 1.

---

## 4. Hosting: Tier A (free-first) and its limitations

| Component | Free service | Limitation (✔ verified / ◐ to verify) | Mitigation in place |
|---|---|---|---|
| Frontend | Vercel Hobby | Non-commercial use ◐ | Portfolio use only |
| API + embedded worker | Render Free web service | 512 MB RAM, ~0.1 CPU, **sleeps after 15 min idle**, ~1 min cold start, 750 h/month ✔. **No persistent disk** | Jobs are durable in Postgres and resume after wake-up; lost files return 410 |
| Database | **Neon free** (recommended; not yet created) | ~0.5 GB, compute auto-suspends ◐ | `pool_pre_ping`; Render's free Postgres **removed** from `render.yaml` because it is deleted ~30 days after creation ✔ |
| File storage | none yet (`/tmp/storage` on Render) | **Ephemeral**: files vanish on restart/redeploy/sleep | Honest 410 + startup warning; plan in §5 |
| Redis | not required | — | The queue uses Postgres; Redis is optional |

Nothing has been purchased or activated.

## 5. Persistent file storage (S3-compatible backend implemented in Phase 1; provider choice is yours)
1. **Interface (Phase 1):** extend `StorageService` with a pluggable backend: `LocalStorage` (dev, tests) and `S3CompatibleStorage` (production). It will serve presigned GET URLs, so downloads go straight from the bucket.
2. **Provider options** (all S3-compatible, so the code is the same):

   | Provider | Free allowance ◐ | Card required? ◐ | Notes |
   |---|---|---|---|
   | Backblaze B2 | ~10 GB storage | Not for the free allowance ◐ | Egress free via Cloudflare/limits apply ◐ |
   | Cloudflare R2 | ~10 GB, free egress | Yes (payment method to enable) ◐ | Best fit technically; needs your approval |
   | Supabase Storage | ~1 GB | No ◐ | Free projects pause after inactivity ◐ |

3. **Retention:** user files auto-delete after 7–14 days (also limits free-tier usage). Files in the DB that expire are marked expired, never served as broken links.
4. **Until approved:** Tier A runs with ephemeral storage. That is acceptable only because each job's input and output are used within a session, and losses are reported honestly (410).

---

## 6. Local machine (inspected 2026-11-06)
| Item | Value | Implication |
|---|---|---|
| GPU | **Intel Iris Xe (integrated). No NVIDIA GPU**, so no CUDA | GPU models (FLUX, Wan, AnimateDiff) **cannot be developed or tested locally**. They need an approved cloud GPU (Phase 5) |
| CPU | Intel Core i5-1235U (10 cores / 12 threads) | Fine for FFmpeg, Whisper `base`, Kokoro TTS, OCR, Florence-2 |
| RAM | 7.7 GB total (**~0.8 GB free** during inspection) | Load one CPU model at a time; FastSD-CPU (4–6 GB) will be tight locally |
| Disk | **C: 7.2 GB free (critical)** · D: 100.9 GB free · E: 100.9 GB free | Model weights and caches must go to **D:** (set `HF_HOME`/model dir to D: in Phase 2) |

---

## 7. Remaining risks (known, accepted for now)
1. **Ephemeral storage on Render Free** until a storage provider is approved (§5).
2. **Access-key holders = account owners.** A leaked invite link grants access until revoked. Keys aren't scoped or expiring, and there is no rate limiting or quotas yet (planned for Phase 1, before any GPU feature).
3. **Signed download links** work for anyone who has the URL during their 1-hour lifetime (like S3 presigned URLs).
4. **No schema migrations yet** (`create_all` creates new tables only). Alembic is needed before any column change (Phase 1).
5. **Embedded worker shares the API's 512 MB.** Fine for FFmpeg; heavier engines need the separate worker (Roadmap Tier A/B).
6. In dev mode, the dev user sees all **legacy** rows (owner NULL). This never happens in production.
7. `datetime.utcnow()` deprecation, Next.js 14 support status, and the legacy `worker/` stub folder (no longer used by compose; kept, not deleted).
8. Frontend: there's no UI message for "invite required" beyond the existing error display. `/modules` badges still over-state (UI design was out of scope).
9. `next build` not verified in this phase (low RAM).

## 7b. Phase 1 remaining risks
1. **Tesseract is not installed on this laptop.** OCR-based modes show "Engine not installed" locally (they work in Docker, where the image installs `tesseract-ocr`). A UAC-free install was blocked, so this needs one manual install (§8).
2. **Render Free (512 MB)** cannot comfortably hold Whisper and Kokoro in memory together. `render.yaml` defaults to Whisper `tiny`, but heavy use needs a 2 GB instance or a separate worker. Models re-download after each restart unless baked into the image (`--build-arg PRELOAD_MODELS=1`).
3. **GPL in-process dependency**: `phonemizer` (via kokoro-onnx) is GPL-3.0+. That's fine for hosting; don't publish Docker images without revisiting it (LICENSE_AUDIT.md §4.1).
4. One job runs at a time per worker (CPU-bound by design). Long transcriptions queue up.
5. No per-user quotas or rate limits yet.
6. `next build` was not run (limited free RAM); `tsc` and `next lint` pass.

## 8. Manual actions required from you
1. **Review and commit** the Phase 0 changes on `dev/multimedia-toolkit-upgrade` (nothing has been committed or pushed).
2. **Before any production deploy:**
   a. Create a free **Neon** Postgres database and put its URL in Render's `DATABASE_URL` (dashboard only, never in Git).
   b. Set `ALLOWED_ORIGINS` and `FRONTEND_URL` in Render to your Vercel URL.
   c. Let Render generate `SIGNING_SECRET` (blueprint does this).
   d. If an old `mtk-postgres` free database exists on Render, export anything you need. It will expire, and the blueprint no longer manages it.
   e. Run `python -m app.cli invite --email …` for each invited user and send the link privately.
3. **Decide** on a storage provider (§5) and whether to approve any card-on-file free tier.
4. **Free disk space on C:** (7.2 GB free) before Phase 2. Model files will be directed to D:.
5. **Install Tesseract OCR (one time, needs your UAC approval)** to enable Image→Text, Image→Audio and on-screen-text modes locally:
   `winget install --id UB-Mannheim.TesseractOCR --location "D:\Tools\Tesseract-OCR"`
   It is auto-detected at `D:\Tools\Tesseract-OCR`. The installer already downloaded to `D:\MultimediaToolKit	mp	esseract-setup.exe` (SHA-256 `c885fff6…60c9`) can be used or deleted. Then re-run `pytest` (the 4 OCR tests will run).
6. **Local dev setup:** `cd backend && pip install -r requirements.txt` (already done in `.venv`). Models are already in `D:\MultimediaToolKit\models`.
7. To use durable storage: create a free B2 or R2 bucket (your decision; R2 needs a card on file) and set `STORAGE_BACKEND=s3` plus the `S3_*` variables.

---

## 9. Unused frontend components (verified, **not deleted**)
An import-graph check of all of `src/` (static imports, dynamic imports, `next/dynamic`, `React.lazy`, configs) found:
- **Reachable from a route:** only `components/shell/AppShell.tsx` (via `app/layout.tsx`).
- **No importers at all (13):** `cta/FinalCta`, `features/AudioToTextSection`, `features/FeatureHighlights`, `features/ImageToTextSection`, `features/VideoToAudioSection`, `features/WorkflowPipeline`, `hero/Hero`, `layout/Footer`, `layout/Navbar`, `modal/SignInModal`, `modal/UploadModal`, `study/StudyModeShowcase`, `workspace/WorkspaceShowcase`.
- **Imported only by unused components (3):** `hero/GradientRibbon` (← Hero), `theme/ThemeProvider` (← Navbar), `ui/AudioWaveform` (← AudioToTextSection, VideoToAudioSection, Hero, WorkspaceShowcase).
- They use no npm packages beyond `react`, `lucide-react` and `next/*`, which are all still used elsewhere, so deleting them would remove no dependency.

These 16 files can be removed safely in one commit when you approve. Git history keeps them.
