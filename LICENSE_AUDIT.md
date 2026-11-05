# LICENSE_AUDIT.md — Licence, Attribution and Compliance Audit

**Date:** 2026-11-06 · **Scope:** current dependencies, plus every candidate engine in GITHUB_REPOSITORY_RESEARCH.md.
**This is an engineering assessment, not legal advice.** Each model's licence must be re-checked on its model card at the moment of integration (marked ◐ below).

---

## 1. The project's own licence: **action needed**

The repository is **public on GitHub with no `LICENSE` file**. Legally that means "all rights reserved": others may look at the code but not reuse it. For a portfolio, that is either intentional or an oversight. **Your decision:**

| Option | Effect |
|---|---|
| **MIT** (common for portfolios) | Anyone may reuse with attribution. Compatible with every dependency below |
| Apache-2.0 | Same as MIT, plus an explicit patent grant and a NOTICE convention |
| No licence | Code visible but not reusable. Valid if you want to keep rights |

None of the recommended dependencies force a particular licence on your code, because the copyleft ones (FFmpeg-GPL build, espeak-ng, psycopg2-LGPL) are used as separate programs or dynamically linked libraries in a hosted service (see §4).

---

## 2. Current dependencies (actually in the repo today)

| Package | Licence | Obligations |
|---|---|---|
| FastAPI | MIT | Keep the notice |
| Uvicorn | BSD-3-Clause | Keep the notice |
| Pydantic / pydantic-settings | MIT | Keep the notice |
| SQLAlchemy | MIT | Keep the notice |
| psycopg2-binary | **LGPL-3.0** (with exceptions) | Dynamic linking from Python is fine. If distributing, allow relinking (wheel is replaceable) |
| redis-py | MIT | Keep the notice |
| httpx | BSD-3-Clause | Keep the notice |
| python-multipart | Apache-2.0 | Keep the notice |
| pytest (dev) | MIT | — |
| **FFmpeg** (Debian `apt` build in Dockerfiles; Gyan build locally) | **GPL-2.0+/3.0** (these builds enable GPL components such as x264) | Invoked as a **separate executable** (subprocess), so your code is not a derivative. Only if you **distribute** a Docker image must you offer FFmpeg's source and licence text |
| Next.js | MIT | Keep the notice |
| React / React-DOM | MIT | Keep the notice |
| lucide-react | ISC | Keep the notice |
| Tailwind CSS, PostCSS, Autoprefixer | MIT | Keep the notice |
| TypeScript | Apache-2.0 | — (dev) |
| ESLint / eslint-config-next | MIT | — (dev) |
| Inter font (via `next/font/google`) | SIL OFL 1.1 | Font may be used freely; don't sell the font alone |
| Docker base images: `python:3.11-slim` (Debian), `node` | Mixed OSS (Debian/PSF/MIT) | Only relevant if distributing images |

**Result: no current licence conflict.**

---

## 3. Candidate engines: licence verdicts

Legend: ✅ approved · ⚠️ approved with conditions · ❌ rejected

### 3.1 Code / runtime libraries

| Component | Licence | Verdict |
|---|---|---|
| faster-whisper, CTranslate2 | MIT ◐ | ✅ |
| whisper.cpp, llama.cpp, llama-cpp-python | MIT ◐ | ✅ |
| kokoro (code), kokoro-onnx | MIT ✔/◐ | ✅ |
| **espeak-ng** (pulled in by Kokoro's phonemiser for some languages, and by Piper) | **GPL-3.0** ✔ | ⚠️ OK for a hosted service (GPL is triggered by *distribution*, not network use). If you ever publish a Docker image, include espeak-ng's licence and a source offer. Never copy its code into this repo |
| **Piper** (`piper1-gpl`) | **GPL-3.0-or-later** ✔ | ⚠️ Fallback only; same conditions as espeak-ng. Each voice model has its own licence |
| RapidOCR, PaddleOCR models | Apache-2.0 ◐ | ✅ Keep the NOTICE |
| Tesseract, pytesseract | Apache-2.0 ◐ | ✅ |
| Diffusers, Transformers, Accelerate, Optimum | Apache-2.0 ◐ | ✅ |
| PyTorch | BSD-3-Clause ◐ | ✅ |
| ONNX Runtime | MIT ◐ | ✅ |
| OpenVINO | Apache-2.0 ◐ | ✅ |
| FastSD CPU | MIT ◐ | ✅ (use as a library/reference; don't vendor its UI) |
| OpenCV (≥ 4.5) | Apache-2.0 ◐ | ✅ |
| Pillow | MIT-CMU (HPND) ◐ | ✅ |
| librosa | ISC ◐ | ✅ |
| PySceneDetect | BSD-3-Clause ◐ | ✅ |
| MoviePy | MIT ◐ | ✅ |
| Real-ESRGAN | BSD-3-Clause ◐ | ✅ |
| Practical-RIFE | MIT ◐ | ✅ |
| procrastinate (optional) | MIT ◐ | ✅ |
| **gifski** | **AGPL-3.0** ◐ | ❌ AGPL reaches network use. Use FFmpeg `palettegen/paletteuse` instead |
| **ComfyUI** | GPL-3.0 ◐ | ❌ Not needed; Diffusers covers it |
| **AUTOMATIC1111 WebUI** | AGPL-3.0 ◐ | ❌ |

### 3.2 Model weights

| Model | Licence | Commercial use | Attribution / conditions | Verdict |
|---|---|---|---|---|
| Whisper (all sizes) | MIT ◐ | Yes | Notice | ✅ |
| **Kokoro-82M** | **Apache-2.0** ✔ | Yes | Notice | ✅ Primary TTS |
| Piper voices | **Varies per voice** ✔ (MIT, CC-BY, CC-BY-NC…) | Depends | Per voice | ⚠️ Only allow voices with permissive licences |
| Coqui XTTS-v2 | Coqui Public Model Licence ◐ | **No** | — | ❌ |
| F5-TTS weights | CC-BY-NC-4.0 ◐ | **No** | — | ❌ |
| **Florence-2** (base/large) | **MIT** ✔ (secondary source) | Yes | Notice | ✅ Primary captioner |
| **Moondream2** | **Apache-2.0** ✔ | Yes | Notice | ✅ |
| SmolVLM2 | Apache-2.0 ◐ | Yes | Notice | ✅ |
| Qwen3 (0.6B–32B dense) | Apache-2.0 ◐ | Yes | Notice | ✅ (check the specific size's card; some older Qwen2.5 sizes used a research licence) |
| PaddleOCR models (in RapidOCR) | Apache-2.0 ◐ | Yes | Notice | ✅ |
| YAMNet | Apache-2.0 ◐ | Yes | Notice | ✅ |
| **FLUX.1-schnell** | **Apache-2.0** ◐ | Yes | Notice | ✅ Primary GPU image model |
| FLUX.1-dev / FLUX Kontext-dev | FLUX.1 [dev] Non-Commercial ◐ | **No** | — | ❌ |
| Stable Diffusion 1.5 | **CreativeML OpenRAIL-M** ◐ | Yes | **Use-based restrictions must be passed on to users** (Attachment A) | ⚠️ Needs an Acceptable Use Policy (§5) |
| LCM-LoRA (SD1.5/SDXL) | OpenRAIL++ ◐ | Yes | Same pass-through | ⚠️ |
| SDXL base + SDXL-Lightning | CreativeML OpenRAIL++-M ◐ | Yes | Same pass-through | ⚠️ |
| SD-Turbo / SDXL-Turbo | Stability non-commercial research licence ◐ | **No** | — | ❌ |
| Stable Video Diffusion | Stability AI Community Licence ◐ | Only under $1M revenue | "Powered by Stability AI" | ❌ Not needed (Wan is better and Apache) |
| **Wan2.1 / Wan2.2** (T2V-1.3B, TI2V-5B) | **Apache-2.0** ✔ | Yes | Notice. The card also disclaims responsibility for generated content and lists prohibited uses | ✅ Primary video model |
| LTX-Video / LTX-2 | LTX-2 Open Weights Licence ✔ | Free **under $10M annual revenue** ✔ | Licence terms + notice; **not OSI open source** | ⚠️ Only as a fallback; document the threshold |
| CogVideoX-5B | CogVideoX licence ◐ | Restricted | — | ❌ |
| **AnimateDiff** motion modules | Apache-2.0 ◐ (+ base model's OpenRAIL-M) | Yes | Pass-through restrictions of SD1.5 | ⚠️ |
| **Depth-Anything-V2-Small** | **Apache-2.0** ◐ | Yes | Notice | ✅ |
| Depth-Anything-V2-Base/Large | CC-BY-NC-4.0 ◐ | **No** | — | ❌ (easy mistake: only **Small** is allowed) |
| Real-ESRGAN weights | BSD-3-Clause ◐ | Yes | Notice | ✅ |
| RIFE weights | MIT ◐ | Yes | Notice | ✅ |
| AnimeGANv2 (original weights) | Non-commercial ◐ | **No** | — | ❌ Use the OpenCV cartoon filter instead |
| MusicGen / AudioGen weights | CC-BY-NC-4.0 ◐ | **No** | — | ❌ (not needed) |

---

## 4. Copyleft analysis: why GPL items are acceptable here

1. **The service is hosted, not distributed.** GPL-2.0/3.0 and LGPL obligations trigger on *distribution*. Running FFmpeg, espeak-ng or psycopg2 on our own servers to serve users does not distribute them. (AGPL is different: it triggers on network use, which is why gifski, A1111 and AGPL tools are rejected.)
2. **FFmpeg is called as a separate process**, not linked, so our code is not a derivative work.
3. **The public GitHub repo contains only our own code.** It contains no FFmpeg/espeak source or binaries, so publishing it distributes nothing GPL.
4. **If you ever publish Docker images** (for example on Docker Hub or GHCR), add to the image: FFmpeg's and espeak-ng's licence texts plus a written source offer (or a link to the exact upstream source). THIRD_PARTY_NOTICES.md already covers this.

---

### 4.1 Phase 1 finding: phonemizer (GPL-3.0+) runs in-process
`kokoro-onnx` imports **phonemizer** (GPL-3.0-or-later) as a Python library, and it loads **espeak-ng** (GPL-3.0) through `espeakng-loader`. Unlike FFmpeg, this is in-process use, not a separate executable.
- **Hosted service (current plan):** no distribution happens, so there are no GPL obligations. Our repository contains none of their code, only a dependency declaration in `requirements.txt`.
- **If a Docker image is ever published:** the image distributes phonemizer and espeak-ng, so ship their licence texts and offer the corresponding source. A strict reading of GPL could also extend obligations to the combined Python application, so **do not publish images without revisiting this**. If needed, Piper (also GPL) would not help. The clean alternative would be a TTS stack with a non-GPL phonemiser.

## 5. Obligations the product must meet

| # | Obligation | Where |
|---|---|---|
| O1 | **THIRD_PARTY_NOTICES.md** listing every shipped dependency and model with its licence | Repo root (created) and linked from the site footer ("Open-source credits") |
| O2 | **Acceptable Use Policy** reproducing the OpenRAIL-M/++ use restrictions (no illegal content, harassment, impersonation, disinformation, sexual content involving minors, discrimination, and so on), plus Wan's prohibited-use statement | `/terms` page, accepted at sign-up |
| O3 | **AI-output labelling.** Every AI-generated asset is marked in its metadata (`metadata_json.engine`, `model`, `model_licence`), and the UI shows "AI-generated" | Job outputs and UI |
| O4 | **Per-model licence registry in code.** Each engine adapter declares `model_id`, `licence`, `licence_url` and `commercial_ok`. CI fails if an unapproved licence is added | `backend/app/adapters/*` (roadmap Phase 1) |
| O5 | **User-upload rights.** Terms say users must own or have the rights to what they upload. Add a takedown contact | `/terms` |
| O6 | **Privacy.** Uploads are processed only for the user's job and auto-deleted after N days; no training on user data | `/privacy`, plus a retention job |
| O7 | Weights are downloaded at deploy time from their official source with a pinned revision. **Weights are never committed to Git** (`.gitignore` already blocks storage; add `models/` when that folder is introduced) | Worker build |
| O8 | Only Piper voices with permissive licences, if Piper is ever enabled | Voice allow-list |

---

## 6. Summary
- **No current violations.**
- **One open decision:** the project's own licence (MIT recommended).
- **Main traps avoided:** FLUX-dev, SD/SDXL-Turbo, XTTS, F5-TTS, Depth-Anything Base/Large, AnimeGAN weights, gifski (AGPL), ComfyUI/A1111.
- **Recommended model stack is entirely Apache-2.0 / MIT / OpenRAIL** (the OpenRAIL ones need the AUP).
