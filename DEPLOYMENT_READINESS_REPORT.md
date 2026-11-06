# DEPLOYMENT_READINESS_REPORT.md

**Date:** 2026-11-06 · **Branch:** `dev/multimedia-toolkit-upgrade` · **PR:** #1 → `main` (open, mergeable, not merged)
**Machine:** Windows 11, i5-1235U, 8 GB RAM, Intel Iris Xe (no NVIDIA GPU), C: ≈ 4 GB free, D: ≈ 100 GB free.

Status legend: **COMPLETE** · **NEEDS MY APPROVAL** · **BLOCKED** · **FAILED** · **NOT TESTED**

> **Bottom line:** the code on the branch is tested and ready. **Production is not ready yet.** Merging PR #1 automatically redeploys the live site (Vercel and Render both deploy from `main`). That needs settings only you can enter, and Render Free's 512 MB of memory is too small for the speech and video workflows (measured, see §7).

---

## 1. Completed tasks

| Task | Status |
|---|---|
| Tesseract OCR installed (winget, approved by you) → `C:\Program Files\Tesseract-OCR`, v5.4.0, languages `eng`, `osd`; detected by the backend | **COMPLETE** |
| FFmpeg 9.0.1 + ffprobe detected | **COMPLETE** |
| Whisper (tiny, base) and Kokoro models on **D:\MultimediaToolKit\models**, no duplicates | **COMPLETE** |
| All 20 conversions run end to end over HTTP with real files | **COMPLETE** (20/20) |
| Backend suite on SQLite **and on a real PostgreSQL 16** | **COMPLETE** |
| Production start-up path on fresh PostgreSQL (migrations, auth enforced, CORS, health) | **COMPLETE** |
| Upgrade of an **old-schema PostgreSQL** database (like the live one) with data preserved | **COMPLETE** |
| Memory measured for Render sizing | **COMPLETE** |
| Frontend lint, type check, production build; Docker Compose config | **COMPLETE** |
| Secret scan of the working tree and the full Git history | **COMPLETE**: nothing found |
| Fixes made in this pass (below) | **COMPLETE** |

### Fixes made in this pass
1. **Neon cold start:** production start-up now retries the database 4× with a 10 s timeout and backoff. Neon's free tier suspends idle compute, and the old single 3-second probe could make Render refuse to boot.
2. **Connection pool for serverless Postgres:** `pool_pre_ping`, `pool_recycle=300`, bounded pool size.
3. **CORS for Vercel previews:** optional `ALLOWED_ORIGIN_REGEX` (default empty, so nothing changes unless you set it).
4. **Empty values copied from `.env.example`** (e.g. `STORAGE_DIR=`) now fall back to safe defaults instead of breaking start-up.
5. **`KEEP_MODELS_LOADED=false`** option unloads Whisper/Kokoro after each job (lower idle RAM).
6. **UI:** every mode now shows a **CPU** or **AI provider** badge; the frame picker also sets the start time for Video→Animation.
7. **Tests:** `TEST_DATABASE_URL` lets the suite run against a disposable PostgreSQL.
8. `.env.example` rewritten: every variable is documented, with placeholders only.

## 2. Pending tasks

| Task | Status | Why |
|---|---|---|
| Create the Neon database | **BLOCKED** | Needs your Neon login |
| Back up / migrate data from the existing Render database | **NEEDS MY APPROVAL** | Your data; I must not touch it |
| Set Render environment variables | **BLOCKED** | Needs your Render dashboard |
| Choose a Render instance size ≥ 1 GB (or a separate worker) | **NEEDS MY APPROVAL** | Paid plan decision (§7) |
| Verify Vercel's `NEXT_PUBLIC_API_URL` | **BLOCKED** | Needs your Vercel dashboard |
| Merge PR #1 (deploys to production) | **NEEDS MY APPROVAL** | Only after the items above |
| Live production verification of the new version | **NOT TESTED** | It isn't deployed yet |
| AI provider modes against a real provider | **NOT TESTED** | No credentials (tested with a mocked API only) |
| Durable file storage (S3/B2/R2) | **NEEDS MY APPROVAL** | Provider choice; Render Free disk is wiped on restart |
| Redis wake-up queue against a real Redis | **NOT TESTED** | No Redis server available locally (logic tested with a fake client; it's optional) |
| `docker build` of the images | **NOT TESTED** | Docker Desktop not running and C: is nearly full |

## 3. Tests and results

| Check | Result |
|---|---|
| Backend pytest (SQLite), final run on the committed code | **147 passed, 0 failed, 0 skipped** |
| Backend pytest on **PostgreSQL 16.2** (`TEST_DATABASE_URL`, disposable local server via `pgserver` on D:) | **145 passed, 0 failed, 0 skipped** (run before the final 4 platform tests were added) |
| Production start-up on fresh PostgreSQL | auth mode `access_key` · `/health` 200 · no key → 401 · CORS only allows the configured origin · Alembic `0002`, **schema drift: none** |
| Old-schema PostgreSQL upgrade | stamped + upgraded to `0002`, **rows preserved**, stuck legacy job recovered |
| End-to-end, real HTTP server, real files, one CPU mode per conversion | **20 / 20 produced real downloadable files** |
| AI modes without credentials | all 12 refuse with HTTP 503 and a clear "not configured" message, never a fake result |
| Frontend `next lint` | 0 errors (1 old warning in an unused component) |
| Frontend `tsc --noEmit` | passes |
| Frontend `next build` (production) | passes, 10 routes |
| Vercel preview build of this branch (GitHub deployment record) | **success**. The page is behind Vercel login (HTTP 302), so its content was not inspected |
| `docker compose config` | valid |

**Skipped tests:** none (the 4 OCR tests that used to skip now run because Tesseract is installed).

## 4. OCR and media processing status

| Engine | Status | Notes |
|---|---|---|
| Tesseract 5.4.0 | **COMPLETE** | Installed to `C:\Program Files\Tesseract-OCR` (the installer ignored the D: location; ~100 MB on C:). Docker image installs `tesseract-ocr` + English |
| FFmpeg / ffprobe 9.0.1 | **COMPLETE** | Docker image installs Debian `ffmpeg` |
| Whisper (faster-whisper int8) | **COMPLETE** | tiny + base cached on D: |
| Kokoro-82M TTS (int8 ONNX) | **COMPLETE** | model + voices on D: |

**Workflows that need Tesseract:** Image→Text (OCR mode), Image→Audio (read aloud), Animation→Audio (read on-screen text), and the on-screen-text part of Animation→Text.

## 5. AI provider status: honest classification

**Workflows that use only deterministic CPU processing (no AI model):** Video→Audio, Text→Image *poster*, Text→Animation *kinetic*, Audio→Image *waveform/spectrogram*, Audio→Video *visualiser*, Audio→Animation *waveform/pulse*, Image→Video *Ken Burns*, Image→Animation, Video→Image *frame/best frame/poster*, Video→Animation, Animation→Image, Animation→Video, Text→Video *typography scenes*.

**Workflows that use local machine-learning models on CPU (real AI, no provider needed):**
- **Whisper** speech recognition: Audio→Text, Video→Text, Animation→Text, and captions in Audio→Video.
- **Kokoro** neural speech: Text→Audio, Image→Audio, Animation→Audio, and narration in Text→Video.
- **Tesseract** OCR (an LSTM model).

**AI modes that call an external provider (12 modes, all need credentials):**

| Conversion | AI mode |
|---|---|
| Text→Image | AI image |
| Text→Video | AI-illustrated scenes |
| Text→Animation | AI image loop |
| Audio→Image | AI cover art |
| Audio→Video | Visualiser on AI art |
| Audio→Animation | AI art pulse |
| Image→Text | Describe |
| Image→Audio | Describe in speech |
| Image→Video | AI-narrated |
| Video→Image | AI poster |
| Animation→Text | Describe visuals |
| Animation→Audio | Narrate visuals |

| Adapter | Models | Status |
|---|---|---|
| Cloudflare Workers AI | `@cf/black-forest-labs/flux-1-schnell` (image, base64 JSON response), `@cf/llava-hf/llava-1.5-7b-hf` (description, image sent as byte array) | Request/response format and errors (401/403, 429, other) tested with a **mocked** API. **NOT TESTED live** |
| Hugging Face Inference | `black-forest-labs/FLUX.1-schnell`, `Salesforce/blip-image-captioning-large` via `router.huggingface.co/hf-inference` | Tested with a mock only. ⚠️ Hugging Face has been moving models between inference providers; the caption model may no longer be served there. **Cloudflare is the recommended provider.** |
| Missing credentials | — | **COMPLETE**: clear 503 "AI generation is not configured…" in the API and "needs configuration" in the UI |

**Required keys (only if you want the AI modes):**
- **Cloudflare:** Account ID (dashboard right sidebar) and an API token with the *Workers AI* permission (dash.cloudflare.com → My Profile → API Tokens). There is a free daily allowance; usage beyond it is billed to your account.
- **Hugging Face:** a fine-grained token with "Make calls to Inference Providers" (huggingface.co/settings/tokens). There is a small free credit, and usage beyond it is billed.
No paid credits were used.

## 6. Database status

| Item | Status |
|---|---|
| Alembic migrations (`0001_baseline`, `0002_job_progress_message`) | **COMPLETE**: verified on SQLite and PostgreSQL; auto-applied at start-up |
| Neon compatibility (SSL in URL, pooled endpoint, cold-start retries, `pool_pre_ping`/`pool_recycle`) | **COMPLETE** in code; **NOT TESTED** against Neon itself (no account access) |
| Neon database | **BLOCKED**: you need to create it |
| Existing Render database | **NEEDS MY APPROVAL**: untouched by me. ⚠️ The backend was first deployed around **10 Oct 2026**. If it uses Render's *free* PostgreSQL, Render deletes those about **30 days after creation**, which may be very soon. Check the expiry date in the Render dashboard and back it up (§11) |
| Old data visibility | After upgrading, rows created by the old version have no owner, so **invited users won't see them** (privacy by design). They aren't deleted |

## 7. Render configuration status

Live backend: **https://mtk-backend.onrender.com** (currently the **old** `main` code; `/health` = 200 after a 31 s cold start; `/api/v1/conversions` = 404).

| Item | Status | Detail |
|---|---|---|
| Dockerfile (FFmpeg + Tesseract, `$PORT`), start command, `/health` | **COMPLETE** | |
| Migrations | **COMPLETE** | Run automatically at start-up; old schema upgrade verified |
| Worker | **COMPLETE** | Embedded in the API (`EMBEDDED_WORKER=true`); jobs survive restarts and sleep |
| Redis | **COMPLETE (optional)** | Not required; leave `QUEUE_NOTIFY_REDIS=false` |
| `DATABASE_URL` | **BLOCKED** | Set to your Neon URL in the dashboard |
| `SIGNING_SECRET` | **BLOCKED** | Generated by the Blueprint, **or** add manually if the service isn't Blueprint-managed. **Without it, the new version refuses to start** |
| `ALLOWED_ORIGINS`, `FRONTEND_URL` | **BLOCKED** | Your Vercel production domain (I couldn't see it; deployment URLs are login-protected) |
| `AUTH_MODE=access_key`, `ENVIRONMENT=production` | **COMPLETE** in `render.yaml` | |
| File persistence | **NEEDS MY APPROVAL** | Render Free disk is temporary; downloads of lost files return an honest 410. Use `STORAGE_BACKEND=s3` with B2/R2 for persistence |
| **Memory** | **FAILED on Render Free** | Measured on this machine (process tree): idle 99 MB · Text→Audio peak **553 MB** · Audio→Text peak **824 MB** · Audio→Video peak **970 MB**. Render Free = **512 MB**, so speech, transcription and video jobs would be killed. Needs an instance with **≥ 1 GB** (2 GB recommended), or a separate worker service |
| `render.yaml` changes on merge | **NEEDS MY APPROVAL** | The new file no longer manages the free database and switches `DATABASE_URL` to "set in dashboard". If your service is Blueprint-synced, review the Blueprint diff in Render before syncing. Set the variables **before** merging |

## 8. Vercel configuration status

| Item | Status |
|---|---|
| Next.js build (standalone output, 10 routes) | **COMPLETE** (local build and Vercel preview build succeeded) |
| `NEXT_PUBLIC_API_URL` usage | **COMPLETE** in code; it's baked in at **build time**, so redeploy after changing it |
| `NEXT_PUBLIC_API_URL` value in Vercel | **BLOCKED**: verify it is `https://mtk-backend.onrender.com` (or your new backend URL) |
| CORS compatibility | **COMPLETE**: Bearer-token auth, no cookies; backend allows only `ALLOWED_ORIGINS` (+ optional regex for previews) |
| Authentication flow | **COMPLETE**: invite link or `/login` stores the key, `/api/v1/me` validates it, sign-out clears it |

## 9. Security issues

| Issue | Where | Status |
|---|---|---|
| **Live site is running the old, insecure version** | Production now | **OPEN until the new version is deployed**: CORS reflects any origin with credentials (verified: `https://evil.example` echoed back); project/asset/job lists are public; no ownership. Fixed on the branch |
| Secrets in Git (working tree + full history) | Repo | **COMPLETE**: none found; `.env` files are ignored |
| `phonemizer`/`espeak-ng` are GPL-3.0 (used by Kokoro) | Licences | Fine for hosting. Don't publish Docker images without reviewing LICENSE_AUDIT.md §4.1 |
| Leaked invite link = account access | Design | Accepted risk; revoke with `python -m app.cli revoke --email …` |
| No per-user rate limits / quotas yet | Backend | **OPEN** (low risk with 10–20 invited users) |
| Signed download links valid 1 h for anyone holding them | Design | Accepted (same model as S3 presigned URLs) |

## 10. Exact manual actions required from you

1. **Render:** open *mtk-backend* → check whether its database is a free one and its expiry date. **Back it up** (command 11.1) if it holds anything you need.
2. **Neon:** create a free project (console.neon.tech) → copy the **pooled** connection string (contains `-pooler` and `sslmode=require`).
3. **Render → mtk-backend → Environment:** set
   `DATABASE_URL` = Neon string · `SIGNING_SECRET` = output of command 11.2 · `ALLOWED_ORIGINS` = your Vercel production URL (e.g. `https://<your-app>.vercel.app`) · `FRONTEND_URL` = same · `ENVIRONMENT=production` · `AUTH_MODE=access_key` · `EMBEDDED_WORKER=true` · `WHISPER_DEFAULT_MODEL=tiny`.
4. **Render plan:** choose an instance with **≥ 1 GB RAM (2 GB recommended)**. On 512 MB, only image, animation and visualiser workflows will run reliably.
5. **Vercel → Project → Settings → Environment Variables:** confirm `NEXT_PUBLIC_API_URL` = the Render backend URL (Production + Preview).
6. *(Optional)* durable storage: create a Backblaze B2 or Cloudflare R2 bucket and set `STORAGE_BACKEND=s3`, `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`.
7. *(Optional)* AI modes: set `AI_PROVIDER=cloudflare`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`.
8. **Then** approve the merge of PR #1. Vercel and Render redeploy automatically. If the new backend fails its health check, Render keeps the previous version running.
9. Create invites (command 11.3) and send the links privately.
10. Send me the production URLs so I can verify the live site and run real conversions.

## 11. Exact commands

```powershell
# 11.1 Back up the existing Render database (URL from Render → database → "External Database URL")
#      Needs PostgreSQL client tools (pg_dump). Run from a folder on D:.
pg_dump "<EXTERNAL_DATABASE_URL>" --no-owner --format=custom --file D:\MultimediaToolKit\render-backup.dump

# 11.2 Generate a signing secret (paste the output into Render; never commit it)
python -c "import secrets; print(secrets.token_hex(32))"

# 11.3 Create invited users against the PRODUCTION database (run locally in backend/)
cd "C:\Users\verma\OneDrive\Desktop\MultimediaToolKit backup\MultimediaToolKit\backend"
$env:ENVIRONMENT="production"; $env:DATABASE_URL="<NEON_URL>"; $env:SIGNING_SECRET="<SAME_SECRET>"
$env:FRONTEND_URL="https://<your-app>.vercel.app"
.\.venv\Scripts\python.exe -m app.cli invite --email friend@example.com
Remove-Item Env:DATABASE_URL, Env:SIGNING_SECRET          # clear secrets from the shell afterwards

# 11.4 (Optional) restore old data into Neon BEFORE first start of the new version
pg_restore --no-owner --dbname "<NEON_URL>" D:\MultimediaToolKit\render-backup.dump

# 11.5 Verify after deployment
curl https://mtk-backend.onrender.com/health
curl https://mtk-backend.onrender.com/api/v1/conversions
```

## 12. Is PR #1 safe to merge?

**Code: yes. Timing: NEEDS MY APPROVAL.** The PR is open and GitHub reports it mergeable (clean). All tests pass and no secrets were found. However, merging **is** a production deployment (Vercel and Render auto-deploy `main`). Merge only after steps 1–5 in §10.

## 13. Is production deployment safe?

**Not yet: BLOCKED** on the database URL, the signing secret, the allowed origins and the memory size. Once those are set, deploying is safer than keeping the current live version, which has known security issues (§9).

---

### Local artefacts from this work
- `D:\MultimediaToolKit\testlib` (43 MB, `pgserver` test tool) and `D:\MultimediaToolKit\pgdata` (disposable test databases).
- `D:\MultimediaToolKit\pylib` (~1 GB, unused PyTorch from the install you stopped earlier).
- `D:\MultimediaToolKit\tmp`.

Nothing was deleted; you can remove these when you like.
