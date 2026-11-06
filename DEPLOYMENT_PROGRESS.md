# Deployment progress (Neon + Render Free + Vercel)

No credentials appear in this file. Secrets live only in the Render/Vercel dashboards and in a
private folder outside the repository.

## Status at a glance (2026-11-06)

| Area | Status |
|---|---|
| Old Render PostgreSQL (`mtk-postgres`, PG 18.6, Free, expires **2026-11-09 11:55 UTC**) | Backed up, verified, untouched |
| Neon (PG 18.6, us-west-2 Oregon, pooled) | Data migrated, schema upgraded to `0002_job_progress_message`, verified |
| Render `mtk-backend` (Free, Oregon, Docker, auto-deploys `main`) | **Live** on Neon (PR #1 merged as `c324c3b`) |
| Vercel `multimedia-tool-kit` (root `frontend`, prod branch `main`) | `NEXT_PUBLIC_API_URL` = `https://mtk-backend.onrender.com` (verified in live bundle). No change needed |
| PR #1 | **Merged** 2026-11-06 |

## Completed

1. **Backup**: `pg_dump` 18.6 (custom + plain SQL) of the Render database. 6 tables, 36 rows
   (assets 16, jobs 10, job_outputs 10, projects/users/usage_events 0). Restored into a throwaway local
   PostgreSQL 18: identical row counts in every table. The Render database was only read.
2. **Migration rehearsal** on local PostgreSQL 18: restore, then the app's Alembic upgrade (legacy database
   detected, stamped `0001_baseline`, upgraded to head). Row counts identical, **zero schema drift**,
   no orphaned job outputs.
3. **Neon migration**: the same procedure on the empty Neon database (restore refuses non-empty targets;
   single transaction). Result: identical row counts, Alembic head `0002_job_progress_message`, zero drift,
   all relationships intact, all 10 historical jobs `succeeded` (the worker will not re-run them).
4. **App on Neon (local, production mode)**:
   - `/health` returned 200, and `/api/v1/conversions` returned 200.
   - Requests with no key or a wrong key got 401.
   - CORS allowed the Vercel origin and rejected other origins.
   - A read/write test inside a rolled-back transaction worked, leaving no test data behind.
5. **512 MB tuning** (new settings, all default to the previous behaviour):
   - `FFMPEG_THREADS`: caps filter and encoder threads.
   - `TTS_CPU_THREADS`: ONNX Runtime threads, no memory arena.
   - `WHISPER_CPU_THREADS` and `KEEP_MODELS_LOADED=false`: unload models after each job.
6. **Render environment staged via API**:
   - The previous values were saved privately first.
   - New values: DATABASE_URL (Neon), SIGNING_SECRET (new random 64-hex value, never displayed), ALLOWED_ORIGINS and
     FRONTEND_URL (`https://multimedia-tool-kit.vercel.app`), ENVIRONMENT=production, AUTH_MODE=access_key,
     EMBEDDED_WORKER=true, STORAGE_BACKEND=local, STORAGE_DIR=/tmp/storage, WHISPER_DEFAULT_MODEL=tiny,
     KEEP_MODELS_LOADED=false, FFMPEG/WHISPER/TTS threads=2, AI_PROVIDER=none, PORT=8000.
   - The service stays on the **free** plan, and no deploy was triggered.
7. **Secret scan of PR #1**: no credentials in the diff or in the git history. `.gitignore` now also excludes
   dumps, backups and credential files.

## Tests (re-run on 2026-11-06 after the latest changes)

| Check | Result |
|---|---|
| Backend pytest, SQLite | **149 passed** |
| Backend pytest, PostgreSQL 18.6 (local) | **149 passed** |
| All 20 conversions over HTTP with real files, Render memory settings | **20/20 succeeded and downloaded** |
| Frontend `tsc --noEmit` | OK |
| Frontend `next build` (with the production API URL) | OK (10 routes) |
| Frontend lint | OK (1 old warning in AudioWaveform.tsx) |
| Vercel preview build of `5e03dda` | READY |

Peak memory per conversion (whole process tree, Windows, short test inputs, Render settings):
134–446 MB. The highest were text→video and text→animation (~446 MB), audio→video (~372 MB) and
audio/video→text (~360 MB). Before tuning, the peaks were up to 970 MB.

## Free-tier limitations (honest)

- **Memory**: 512 MB. Short inputs fit (measured above). **Long** audio or video (several minutes or more),
  large images or videos, and long text-to-video scripts can exceed 512 MB. Render then restarts the
  instance, and the job is retried and finally marked failed (`WORKER_LOST`). These measurements were
  taken on Windows; Linux usage is similar but has not been measured on Render itself.
- **CPU**: Render Free has a small CPU share, so conversions are several times slower than locally.
  Speech jobs on long audio can hit the 600 s FFmpeg timeout.
- **Storage is temporary**: uploaded and generated files live in `/tmp/storage`. They are **lost on every
  restart, redeploy or sleep** (after 15 idle minutes). Database records survive (Neon), and downloads of
  lost files return **410 Gone**, never a fake file. The 16 historical assets from the old database
  refer to files that no longer exist on Render (they will return 410). There is no durable free storage
  configured (an S3-compatible bucket would need a new account; not done without approval).
- **Cold start**: ~1 minute after sleep. Models download on the first speech job after each restart
  (Whisper tiny ~75 MB, Kokoro ~90 MB).
- **AI modes** (12 of them) need a Cloudflare or Hugging Face key and are reported as "not configured".
  All 20 conversions have a working CPU mode.

## Live verification (2026-11-06, deployed `c324c3b`)

Tested against https://mtk-backend.onrender.com from outside, using the real owner access key:
- `/health` 200; no key / wrong key -> 401; owner key -> `/me` 200 (user stored in Neon).
- CORS: the Vercel origin is allowed; other origins are rejected (400).
- Frontend: `/`, `/convert`, `/convert/[id]`, `/login`, `/jobs`, `/projects`, `/modules`, `/workspace` all return 200.
- Upload of 5 sample files (`demo-files/`) worked.
- **19 of 20 conversions succeeded live, with real downloadable outputs** (4–180 s each on Render's free CPU).
- **text_to_video failed live**: Render reported `oomKilled` (512Mi). The fix was committed after the merge
  (`5f1f889`): narrate first, release the model, then render, and return freed memory to the OS. Local peak
  dropped from 446 MB to 256 MB. It needs one more merge to `main`, then a live re-test of text_to_video.

## Pending / needs owner approval

- [x] PR #1 merged; live verification done (above). Owner invite key created (kept privately).
- [ ] Merge the OOM fix (`5f1f889`) to `main` and re-test text_to_video live.
- [ ] Old Render database: nothing to do. Render deletes it automatically on 2026-11-09, and the verified backup is kept.

## Rollback

- **Backend**: in Render, redeploy the previous deploy (commit `57bc6d4`). The previous environment values
  are saved privately. The old database remains available until 2026-11-09.
- **Database**: Neon keeps the migrated copy. The verified dump can be restored again at any time.
