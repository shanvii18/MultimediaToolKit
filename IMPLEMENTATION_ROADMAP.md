# IMPLEMENTATION_ROADMAP.md — From 1 to 20 Working Conversions

**Date:** 2026-11-06 · **Based on:** PROJECT_AUDIT.md, GITHUB_REPOSITORY_RESEARCH.md, LICENSE_AUDIT.md
**Approach:** incremental. The existing code is kept and extended, video→audio keeps working at every step, and every phase ends with green tests and a demoable result.

---

## 1. Target architecture

```text
Vercel (Next.js)  ──HTTPS──►  API service (FastAPI, existing backend/)
                                 │  validates, creates Job rows, signs URLs
                                 ▼
                         PostgreSQL (Neon free) ◄──── jobs table = the queue
                                 ▲                  (SELECT … FOR UPDATE SKIP LOCKED)
              ┌──────────────────┴──────────────────┐
     CPU worker (existing worker/)          GPU worker (scale-to-zero, optional)
     E1 FFmpeg  E2 Whisper  E3 Kokoro       E7 FLUX-schnell  E8 Wan2.x
     E4 OCR  E5 Florence-2  E6 Qwen3        E9 AnimateDiff   E12 RIFE/ESRGAN
     E7-CPU FastSD  E9-CPU parallax
     E10 librosa/YAMNet  E11 SceneDetect
                                 │
                                 ▼
                   Object storage (R2/B2) ── or local disk in dev
```

**Key ideas:**
- **Tool registry.** One Python dict and one TypeScript file describe all 20 conversions: id, input/output format, modes, CPU/GPU, params schema and the licences of the models used. Both the API validation and the UI are generated from it, which replaces the hard-coded `if tool == …` branches and the old catalog.
- **Pipeline = an ordered list of engine steps.** Each step reports progress, and its intermediate outputs are stored as assets, so they are reusable and debuggable.
- **Jobs are claimed by workers by capability** (`requires: cpu|gpu`). The API never runs heavy work, so restarts are safe and stale `running` jobs are re-queued after a heartbeat timeout.
- **Honest modes.** If the GPU worker is offline or not approved, AI modes show "Unavailable" and Classic modes still work. No fake results.

---

## 2. Phases

Estimates are **focused developer-days** for one developer working with me. Part-time calendar time is roughly 2× these numbers.

### Phase 0: Hardening the foundation (4–6 days) — *no new features*
| Task | Fixes audit item |
|---|---|
| Test isolation: `conftest.py` with temp DB and storage fixtures | §4.10 |
| Safe downloads: server-side MIME, `attachment`, `nosniff`, drop or force-download SVG | §4.1 |
| FFmpeg: timeouts; correct codecs per format (mp3/wav/m4a/ogg); correct output extension and metadata | §4.6, §4.7 |
| DB fallback to SQLite only when `ENVIRONMENT=development`; `/health` reports DB state | §4.4, §4.8 |
| CORS: explicit origins in production; credentials only with explicit origins | §4.9 |
| Alembic baseline migration from the current models | P2 |
| `datetime.now(UTC)` | P2 |
| Make the catalog badges honest (all unbuilt items → "Planned") and correct PROJECT_STATUS.md | P2 honesty gap |
**Exit:** all 15 existing tests plus new security/format tests pass; video→audio works unchanged.

### Phase 1: Platform core (6–8 days)
- **Users and ownership:** email + password (argon2) or magic link, an httpOnly session cookie, and `owner_id` enforced on every query. Sign-up is invite-code gated (for a group of 10–20 trusted users).
- **Quotas and rate limits:** per-user daily job and GPU-second limits, recorded in the existing `usage_events` table.
- **Worker:** turn the `worker/` stub into a Postgres-polling executor. Move `JobRunnerService` logic there. Add heartbeats, retries (max 2), cancellation and stale-job recovery. Keep an in-process fallback for local dev.
- **Storage abstraction:** `LocalStorage` | `S3Storage` (R2/B2 compatible) behind the existing `StorageService` interface, with signed download URLs and retention (auto-delete after 7–14 days).
- **Tool registry and pipeline runner** (E-adapter interface: `run(inputs, params, progress_cb) -> outputs`, with licence metadata).
- **Generic workspace UI:** format picker (5×5 grid showing only the 20 valid arrows), upload, a params form generated from the schema, live progress, preview players, download. Route: `/convert/[from]-to-[to]`.
**Exit:** video→audio and storyboard run through the new worker; two users can't see each other's files.

### Phase 2: The six Normal conversions, CPU (6–8 days)
E2 faster-whisper, E3 Kokoro, plus E1 extensions → **#1 Text→Audio, #2 Audio→Text (TXT/SRT/VTT), #3 Video→Text, #4 Video→Audio (all formats), #5 Animation→Text (audio path), #6 Animation→Audio (audio path)**. The silent-animation paths of #5/#6 are completed in Phase 3, once E4/E5 exist.
**Exit:** 6/20 working (the silent-animation paths of #5/#6 follow in Phase 3).

### Phase 3: Understanding engines and special Image/Video workspaces, CPU (6–8 days)
E4 RapidOCR, E5 Florence-2 (+ Moondream Q&A), E11 PySceneDetect, E12 best-frame →
- **#13 Image→Text** (OCR | Describe), **#14 Image→Audio** (Read aloud | Describe in speech)
- **#17 Video→Image Mode A** (frame picker with thumbnail strip, exact seek, crop/rotate/adjust/text editor)
- **#19 Animation→Image** (best frame / chosen frame / contact sheet / sprite sheet)
- Silent paths of **#5 and #6** (OCR + caption → text → TTS)
**Exit:** 10/20 working. Everything so far is CPU-only and hostable at $0.

### Phase 4: Generative Classic modes, CPU compositional (8–12 days)
E7-CPU FastSD (SD1.5 + LCM), E9-CPU depth parallax (Depth-Anything-V2-Small), E10 librosa + YAMNet, E6 Qwen3 (optional, templates first) →
- **#7 Text→Image**, **#8 Text→Video** (storyboard → images → narration → Ken Burns + subtitles; **reuses `StoryboardAdapter`**), **#9 Text→Animation**
- **#10 Audio→Image**, **#11 Audio→Video** (visualiser + subtitles), **#12 Audio→Animation** (beat-reactive loop)
- **#15 Image→Video** (parallax/Ken Burns), **#16 Image→Animation** (parallax loop/boomerang)
- **#18 Video→Animation** (GIF/WebP + cartoon filter), **#20 Animation→Video** (MP4 + minterpolate)
**Exit: 20/20 conversions working in Classic mode.** This is the first fully complete, $0-hostable portfolio milestone.

### Phase 5: AI (GPU) modes (10–15 days) — *requires an approved GPU source*
GPU worker image (Diffusers + PyTorch, weights fetched at build time with pinned revisions) →
- E7 FLUX.1-schnell → AI mode for #7, #10, #19, and **#17 Mode B AI poster** (keyframes + transcript → summary → img2img poster + title overlay)
- E8 Wan2.2-TI2V-5B (or Wan2.1-1.3B) → AI mode for **#8, #15**, and #11 background
- E9 AnimateDiff → AI mode for **#9, #12, #16, #18**
- E12 RIFE / Real-ESRGAN → AI mode for **#20**
- GPU budget guard: per-user GPU-second quota and a global monthly cap that auto-disables AI modes before credits run out.

### Phase 6: Product polish and portfolio presentation (6–10 days)
Landing page that shows the 5-format graph; a gallery of sample outputs; job history; side-by-side input/output preview; mobile layout; accessibility pass; Next.js upgrade from 14 to the current supported major; remove the 12 dead components (after your approval); `/terms`, `/privacy`, `/credits` (from THIRD_PARTY_NOTICES); README with architecture diagram and demo GIFs.

### Phase 7: Deployment and operations (4–6 days, partly overlapping)
CI (GitHub Actions: pytest, tsc, lint, licence check), deploy pipelines, Sentry free tier or structured logs, uptime ping, backups (Neon point-in-time), smoke tests against production, a load test simulating 20 users.

### Totals

| Milestone | Cumulative dev-days | Result |
|---|---|---|
| After Phase 3 | ~22–30 | 10/20 conversions, fully free hosting |
| **After Phase 4** | **~30–42** | **20/20 conversions (Classic), $0 hosting** |
| After Phase 5 | ~40–57 | 20/20 with AI modes |
| After Phases 6–7 | **~50–73** | Polished, monitored, public portfolio product |

That is roughly **10–15 weeks full-time, or 4–6 months part-time.** The biggest uncertainty is GPU model behaviour on the chosen hardware (Phase 5).

---

## 3. Compute requirements by workflow

| Workload | Typical job | CPU time (2 vCPU) ◐ | GPU time ◐ | RAM / VRAM |
|---|---|---|---|---|
| Whisper `base` int8 | 5 min audio | ~1–3 min | ~10–20 s | ~0.5–1 GB RAM |
| Kokoro TTS | 1,000 characters | ~5–20 s | — | < 1 GB RAM |
| RapidOCR | 1 image | 1–3 s | — | ~0.3 GB RAM |
| Florence-2-base | 1 image | 3–10 s | < 1 s | ~1.5 GB RAM |
| FastSD CPU (SD1.5 + LCM, 512 px) | 1 image | ~5–30 s | — | 4–6 GB RAM |
| FLUX.1-schnell 1024 px | 1 image | ✗ | ~5–20 s (L4/A10) | 16–24 GB VRAM (12 with offload) |
| Wan2.2-TI2V-5B, ~5 s 720p | 1 clip | ✗ | ~4–10 min (L4/A10); faster on A100/H100 | 16–24 GB VRAM |
| AnimateDiff 16 frames 512 px | 1 loop | ✗ | ~30–90 s | 8–12 GB VRAM |
| Depth parallax (CPU) | 1 image → 4 s video | ~10–30 s | — | ~1 GB RAM |
| FFmpeg slideshow (Text→Video Classic) | 6 scenes, 30 s | ~20–60 s | — | < 1 GB |

◐ = engineering estimates. Each will be benchmarked on the real hardware at integration time and the table updated.

**Implication:** the CPU worker needs **~4–8 GB RAM** (Florence-2 + Whisper + FastSD loaded lazily, one job at a time). Render's free 512 MB instance **cannot** run the CPU worker; it can only host the API.

---

## 4. Hosting plan and cost tiers for 10–20 users

| Tier | Components | Monthly cost | What works |
|---|---|---|---|
| **A: Free** (recommended start) | Vercel Hobby (frontend) · Render Free (API, sleeps after 15 min) · **Neon Free** Postgres · CPU worker on **Oracle Always Free ARM (2 OCPU / 12 GB)** *or* your own PC during demos · storage on worker disk or **R2/B2 free** | **$0** | All 20 conversions in **Classic** mode. First request after idle takes ~1 min to wake |
| **B: Free + GPU credits** | Tier A + **Modal Starter** GPU worker (scale to zero, $30/month free credits ≈ 35–50 L4/T4 GPU-hours) | **$0** if under credits (card required) | Adds **AI modes**. Quotas keep you under the credit |
| **C: Reliable** | Render Starter API (~$7) or a small VPS (~$5–10) for API + CPU worker (no sleep) · Neon free · R2 · Modal pay-as-you-go | **~$10–25** | Same as B, with no cold starts and predictable latency |

**Not recommended:** Render free Postgres (expires after 30 days), relying on HF ZeroGPU for serving (≈ 5 min/day quota per account), and paid inference APIs (excluded by your rule).

**Approvals I need before Phase 5 / deployment** (listed again in §6): a GPU provider, a storage provider with a card on file, and a choice of Oracle/VPS vs. local PC for the CPU worker.

---

## 5. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Free-tier changes (Oracle halved its allowance in June 2026; Render DB expiry) | Everything containerised and provider-agnostic; storage/DB/worker are swappable via env vars |
| GPU credits exhausted by a few users | Per-user GPU-second quotas, a global monthly cap, and automatic fallback to Classic mode |
| Slow CPU jobs feel broken | Real progress per pipeline step, estimated-time display, email/notification on completion (optional) |
| Model licence changes upstream | Pinned model revisions plus the licence registry in code (LICENSE_AUDIT O4) |
| Abuse of public generative tools | Invite-only sign-up, AUP, rate limits, upload size and duration caps, retention auto-delete |
| Scope creep across 20 workflows | Engine reuse (E1–E5 cover half the product); Classic first, AI second |
| Breaking video→audio | Its end-to-end test runs in CI on every change from Phase 0 onward |

---

## 6. Decisions needed from you before coding starts

1. **Approve Phase 0** (hardening, no new features) as the first coding step.
2. **Project licence:** MIT (recommended), Apache-2.0, or none.
3. **Hardware:** do you have a local NVIDIA GPU (model / VRAM)? This decides whether Phase 5 can be developed locally.
4. **Hosting direction:** Tier A now and Tier B later (recommended), or a different mix.
5. **Accounts:** invite-only email sign-up for 10–20 users (recommended), or open sign-up.
6. **Old UI cleanup:** may I remove the 12 unused legacy components in Phase 6 (they stay in Git history)?
