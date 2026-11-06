# GITHUB_REPOSITORY_RESEARCH.md — Open-Source Engines for the 20 Conversions

**Research date:** 2026-11-06
**Rules followed:** I cloned nothing, downloaded no weights, installed nothing, and used no paid APIs.

**How sure each fact is:**
- **✔ verified:** checked against a current web source during this research (links in §8).
- **◐ known:** from my prior knowledge (current to mid-2026). **Re-verify the model card and LICENSE file at integration time**, before any weights are downloaded.

---

## 1. Design principle: 12 reusable engines, 20 pipelines

Writing 20 separate integrations would mean 20 times the maintenance. Instead, every conversion is a **pipeline (a small DAG) of shared engines**. Each engine is one adapter class in `backend/app/adapters/`, the same pattern as the existing `ffmpeg_adapter.py`. Each engine runs on **CPU** or **GPU**, which is what decides hosting cost.

| ID | Engine | Primary choice | Fallback / alternative | Runs on |
|---|---|---|---|---|
| E1 | **Media I/O** (probe, extract, transcode, frames, GIF, slideshow, visualisers, mux) | **FFmpeg** (existing adapter) + ffprobe | MoviePy (MIT) for compositing | CPU |
| E2 | **ASR** (speech → text, SRT/VTT) | **faster-whisper** (CTranslate2, int8) | whisper.cpp | CPU (GPU optional) |
| E3 | **TTS** (text → speech) | **Kokoro-82M** via `kokoro-onnx` | Piper (GPL-3.0, see licence audit) | CPU |
| E4 | **OCR** | **RapidOCR** (ONNX PaddleOCR models) | Tesseract 5 | CPU |
| E5 | **Vision captioner / VQA** | **Florence-2-base** (captions, 0.23B) | Moondream2 (VQA, ~1.9B); SmolVLM2 (multi-frame/video) | CPU (slow but OK) / GPU |
| E6 | **Text LLM** (summaries, prompt writing, poster titles) | **Qwen3-1.7B/4B GGUF** via llama.cpp | Existing deterministic `StoryboardAdapter` / templates | CPU |
| E7 | **Image generator** | GPU: **FLUX.1-schnell** · CPU: **SD 1.5 + LCM-LoRA** via FastSD CPU / OpenVINO | SDXL + Lightning (GPU) | GPU / CPU (slow) |
| E8 | **Video generator** (text/image → video) | **Wan2.2-TI2V-5B** or **Wan2.1-T2V-1.3B** | LTX-Video (revenue-threshold licence) | **GPU only** |
| E9 | **Animator** (image → short loop) | GPU: **AnimateDiff** (SD1.5 motion module) · CPU: **depth parallax** (Depth-Anything-V2-**Small** + FFmpeg) | Wan I2V short clip | GPU / CPU |
| E10 | **Audio analysis** (tempo, energy, sound-event tags) | **librosa** + **YAMNet** (ONNX/TFLite) | PANNs | CPU |
| E11 | **Scene / keyframe detection** | **PySceneDetect** | FFmpeg `select='gt(scene,0.3)'` | CPU |
| E12 | **Enhancement** (upscale, frame interpolation, best-frame) | **Real-ESRGAN**, **Practical-RIFE**, OpenCV Laplacian sharpness | FFmpeg `minterpolate` (CPU, lower quality) | GPU (CPU possible) |

Supporting libraries: **Pillow** (image edit/crop/text overlay), **OpenCV** (frame analysis, cartoon filter), **Diffusers + PyTorch** (E7–E9 on GPU), **ONNX Runtime / OpenVINO** (CPU acceleration).

---

## 2. Candidate repositories per engine

| Engine | Repository | Licence (code / weights) | Maintenance | Hardware | Integration feasibility |
|---|---|---|---|---|---|
| E1 | [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) | LGPL-2.1+ (Debian build is **GPL** because of x264) ◐ | Very active | CPU | ✅ Already integrated |
| E2 | [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | MIT / Whisper weights MIT ◐ | Active | `base` int8 ≈ 0.5 GB RAM; `small` ≈ 1 GB; real-time-ish on 2 vCPU for `base` | ✅ pip, pure Python API |
| E2 alt | [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | MIT ◐ | Very active | CPU-optimised | ⚠️ Needs a binary/bindings; use only if faster-whisper is too slow |
| E3 | [hexgrad/kokoro](https://github.com/hexgrad/kokoro) + [thewh1teagle/kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) | Weights **Apache-2.0** ✔; inference code MIT ✔; uses **espeak-ng (GPL-3.0)** for some phonemisation ✔ | Active | 82M params, CPU OK (<1 GB) | ✅ Best quality/licence/CPU balance |
| E3 alt | [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) | **GPL-3.0** ✔ (old rhasspy/piper MIT repo archived Oct 2025 ✔); voice licences vary per voice ✔ | Active | Very light CPU | ⚠️ Fallback only, because of GPL plus per-voice licences |
| E4 | [RapidAI/RapidOCR](https://github.com/RapidAI/RapidOCR) | Apache-2.0 (PaddleOCR models Apache-2.0) ◐ | Active | CPU, ~200 MB | ✅ pip `rapidocr-onnxruntime` |
| E4 alt | [tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract) + `pytesseract` | Apache-2.0 ◐ | Active | CPU, apt package | ✅ Simplest; weaker on photos/scene text |
| E4 alt | [JaidedAI/EasyOCR](https://github.com/JaidedAI/EasyOCR) | Apache-2.0 ◐ | Slow maintenance | Pulls in PyTorch | ❌ Heavier than RapidOCR for the same job |
| E5 | [microsoft/Florence-2-base](https://huggingface.co/microsoft/Florence-2-base) | **MIT** ✔ (secondary source) | Stable (no longer updated) | 0.23B, CPU feasible (seconds per image) | ✅ `transformers`; also does OCR-with-regions |
| E5 alt | [vikhyat/moondream](https://github.com/vikhyat/moondream) | **Apache-2.0** ✔ | Active | ~1.9B, CPU slow, GPU fast | ✅ Good for "ask about this image" |
| E5 alt | [HuggingFaceTB/SmolVLM2](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct) | Apache-2.0 ◐ | Active | 256M / 500M / 2.2B; accepts multiple frames | ✅ Best fit for Video/Animation→Text visual description |
| E6 | [QwenLM/Qwen3](https://github.com/QwenLM/Qwen3) + [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) / `llama-cpp-python` | Apache-2.0 / MIT ◐ | Very active | 1.7B Q4 ≈ 1.2 GB RAM, CPU usable | ✅ Optional; templates work without it |
| E7 | [black-forest-labs/flux](https://github.com/black-forest-labs/flux) — **FLUX.1-schnell only** | **Apache-2.0** (schnell) ◐ — **FLUX.1-dev is non-commercial, do not use** | Active | ≥ 16 GB VRAM comfortable; 12 GB with offload/fp8 | ✅ via Diffusers |
| E7 CPU | [rupeshs/fastsdcpu](https://github.com/rupeshs/fastsdcpu) (SD 1.5 + LCM-LoRA, OpenVINO) | MIT code; SD1.5 **CreativeML OpenRAIL-M**; LCM-LoRA openrail++ ◐ | Active | 4–8 GB RAM, ~2–10 s/image on modern CPU ◐ | ✅ Makes Text→Image possible with no GPU (lower quality, 512 px) |
| E7 alt | SDXL-base + [ByteDance/SDXL-Lightning](https://huggingface.co/ByteDance/SDXL-Lightning) | CreativeML OpenRAIL++-M ◐ | Stable | 10–12 GB VRAM | ✅ via Diffusers |
| E8 | [Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2) — **TI2V-5B** | **Apache-2.0** ✔ | Active | ~8 GB VRAM with offload/quantisation, 16 GB+ comfortable at 720p ✔ (estimates vary) | ✅ Diffusers support; text→video *and* image→video in one model |
| E8 alt | [Wan-Video/Wan2.1](https://github.com/Wan-Video/Wan2.1) — **T2V-1.3B** | Apache-2.0 ◐ | Maintained | ~8 GB VRAM, 480p ◐ | ✅ Cheapest GPU option |
| E8 alt | [Lightricks/LTX-Video](https://github.com/Lightricks/LTX-Video) / LTX-2 | **LTX-2 Open Weights License**: free under **$10M annual revenue** ✔, *not* OSI open source | Very active | Fast; 12–24 GB VRAM ◐ | ⚠️ Usable for a portfolio, but needs licence-notice handling |
| E8 avoid | Stable Video Diffusion | Stability AI Community Licence (<$1M revenue, attribution) ◐ | Superseded | 16 GB+ | ❌ Wan is better and Apache |
| E8 avoid | CogVideoX-5B | Custom CogVideoX licence ◐ (2B variant Apache-2.0) | Superseded | 12 GB+ | ❌ |
| E9 | [guoyww/AnimateDiff](https://github.com/guoyww/AnimateDiff) | Apache-2.0 (motion modules) ◐ + SD1.5 OpenRAIL-M | Stable/quiet | 8–12 GB VRAM | ✅ via Diffusers `AnimateDiffPipeline` |
| E9 CPU | [DepthAnything/Depth-Anything-V2](https://github.com/DepthAnything/Depth-Anything-V2) — **Small only** | **Small = Apache-2.0; Base/Large = CC-BY-NC-4.0** ◐ | Active | Small (25M) runs on CPU | ✅ Depth map → 2.5D parallax via OpenCV + FFmpeg |
| E10 | [librosa/librosa](https://github.com/librosa/librosa) | ISC ◐ | Active | CPU | ✅ |
| E10 | [YAMNet](https://github.com/tensorflow/models/tree/master/research/audioset/yamnet) (ONNX export) | Apache-2.0 ◐ | Stable | CPU, tiny | ✅ 521 AudioSet sound labels → prompt words |
| E11 | [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | BSD-3-Clause ◐ | Active | CPU | ✅ |
| E12 | [xinntao/Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) | BSD-3-Clause ◐ | Quiet but stable | GPU preferred | ⚠️ Optional polish feature |
| E12 | [hzwer/Practical-RIFE](https://github.com/hzwer/Practical-RIFE) | MIT ◐ | Active | GPU preferred | ⚠️ Optional (GIF → smooth MP4) |
| — | [huggingface/diffusers](https://github.com/huggingface/diffusers), `transformers`, PyTorch | Apache-2.0 / Apache-2.0 / BSD-3 ◐ | Very active | — | ✅ Single runtime for E5/E7/E8/E9 |
| — | [Zulko/moviepy](https://github.com/Zulko/moviepy) | MIT ◐ | Active | CPU | Optional (FFmpeg alone is enough) |

**Rejected on licence grounds** (details in LICENSE_AUDIT.md): Coqui **XTTS-v2** (CPML, non-commercial), **F5-TTS** weights (CC-BY-NC), **FLUX.1-dev** (non-commercial), **SD-Turbo / SDXL-Turbo** (non-commercial research licence), **Depth-Anything-V2 Base/Large** (CC-BY-NC), original **AnimeGANv2** weights (non-commercial), **MusicGen** weights (CC-BY-NC), **gifski** (AGPL-3.0; FFmpeg `palettegen` gives comparable GIFs).

**Rejected on architecture grounds:** **ComfyUI** (GPL-3.0, a node-graph app rather than a library, heavy to embed), **Automatic1111** (AGPL-3.0, a UI app), **Celery** (overkill for 10–20 users, and poor Windows dev support).

---

## 3. The 20 pipelines

Notation: `→` is a sequential step, `‖` runs in parallel, and `[CPU]`/`[GPU]` shows the hardware needed. Every generative workflow gets a **Classic (CPU, always available)** mode and, where it adds real value, an **AI (GPU)** mode. The UI labels which mode produced each output.

### NORMAL (all CPU, all $0-hostable)

| # | Conversion | Pipeline |
|---|---|---|
| 1 | **Text → Audio** | text → sentence split → E3 Kokoro (voice, speed) → E1 encode MP3/WAV `[CPU]` |
| 2 | **Audio → Text** | E1 normalise to 16 kHz mono WAV → E2 faster-whisper → TXT + SRT + VTT + JSON (word timestamps) `[CPU]` |
| 3 | **Video → Text** | E1 extract audio (**reuse existing video_to_audio**) → E2 transcript. Optional "visual summary": E11 keyframes → E5 captions → E6 merge `[CPU]` |
| 4 | **Video → Audio** ✅ | Existing. Add: fix the format bug, a timeout, and WAV/M4A/OGG output with correct codecs `[CPU]` |
| 5 | **Animation → Text** | E1 probe. **If an audio stream exists** → E2. Plus E11/even sampling of N frames → E4 OCR (text inside the animation) ‖ E5 caption → merged description `[CPU]` |
| 6 | **Animation → Audio** | E1 probe. **If an audio stream exists** → extract (same as #4). **Otherwise** → #5 description → E3 narration. The UI states which path ran `[CPU]` |

> ⚠️ Note: GIF/WebP animations usually have **no audio**, so #5 and #6 rely on vision models, not pure conversion. They are still CPU-feasible.

### GENERATIVE AI

| # | Conversion | Classic mode `[CPU]` | AI mode `[GPU]` |
|---|---|---|---|
| 7 | **Text → Image** | E7 FastSD-CPU (SD1.5 + LCM, 512 px) | E7 FLUX.1-schnell (1024 px, 4 steps) |
| 8 | **Text → Video** | **Storyboard pipeline:** existing `StoryboardAdapter` (or E6) → scenes → E7 image per scene → E3 narration per scene → E1 Ken-Burns slideshow + burned subtitles + crossfades | E8 Wan2.2-TI2V-5B / Wan2.1-1.3B (≈5 s clip, 480–720p) |
| 9 | **Text → Animation** | E7 image → E9 depth-parallax loop → E1 GIF/WebP (palettegen) | E9 AnimateDiff 16-frame loop → GIF/WebP/MP4 |
| 10 | **Audio → Image** | E2 transcript ‖ E10 tags + tempo/energy/key → prompt builder (template or E6) → E7. Bonus artistic option: E1 `showspectrumpic` / waveform art | Same prompt → E7 FLUX |
| 11 | **Audio → Video** | E1 visualiser (`showwaves` / `showfreqs` / `avectorscope`) over a background (#10 image or gradient) + E2 subtitles burned in | Background loop from E9/E8 synced to the audio |
| 12 | **Audio → Animation** | E10 beat grid → audio-reactive frames (pulse/zoom on beats) over the #10 image → E1 GIF/WebP | AnimateDiff loop with motion strength driven by energy |
| 13 | **Image → Text** ★ | **Mode A, OCR:** E4 RapidOCR (layout-ordered text, copy/export TXT/JSON). **Mode B, Describe:** E5 Florence-2 detailed caption (+ optional Moondream Q&A) | Larger VLM on GPU for richer descriptions |
| 14 | **Image → Audio** ★ | **Mode A, Read aloud:** E4 → clean-up → E3. **Mode B, Describe in speech:** E5 → E6 natural phrasing (optional) → E3 | — |
| 15 | **Image → Video** | E9 depth parallax / Ken-Burns zoompan → MP4 (+ optional music bed / TTS caption) | E8 Wan2.2-TI2V-5B image-to-video |
| 16 | **Image → Animation** | E9 depth-parallax loop, boomerang, or cinemagraph mask → GIF/WebP | E9 AnimateDiff / Wan I2V short loop → GIF |
| 17 | **Video → Image** ★ | **Mode A, Frame picker & editor:** E1 thumbnail strip + exact-timestamp frame (`-ss` accurate seek) → crop/rotate/brightness/contrast/text (Pillow on server, canvas preview on client). Auto-suggest the sharpest frame (E12 Laplacian) | **Mode B, AI poster:** E11 keyframes ‖ E2 transcript → E5 captions → E6 summary → poster prompt → E7 (img2img from the best keyframe, keeping its composition) → Pillow title overlay → PNG |
| 18 | **Video → Animation** | Trim → E1 GIF/WebP (palettegen, fps/size control) + optional OpenCV cartoon filter (`stylization` / edge-preserving) | AnimateDiff video-to-video restyle (SD1.5), short clips only |
| 19 | **Animation → Image** | Best frame (E12 sharpness), any chosen frame, contact sheet, or sprite sheet (E1 `tile`) | #5 description → E7 "poster of this animation" |
| 20 | **Animation → Video** | GIF → MP4/WebM (loop N×, scale, pad, optional audio track) + FFmpeg `minterpolate` smoothing | E12 RIFE interpolation + Real-ESRGAN upscale; or E8 extend from the last frame |

★ = special workspace.

### Engine reuse: why this is tractable

| Engine | Used by # of conversions |
|---|---|
| E1 FFmpeg | **20 / 20** |
| E7 Image gen | 8 (7, 8, 9, 10, 11, 12, 17B, 19B) |
| E5 Captioner | 6 (3, 5, 6, 13B, 14B, 17B) |
| E3 TTS | 5 (1, 6, 8, 14, 15) |
| E2 ASR | 6 (2, 3, 5, 10, 11, 17B) |
| E9 Animator | 6 (9, 12, 15, 16, 18, 20) |

Building **E1 + E2 + E3 + E4 + E5** (all CPU) covers the 6 Normal conversions, both special Image workspaces and the Classic mode of most others.

---

## 4. Job orchestration (worker) options

| Option | Licence | Fit |
|---|---|---|
| **Own Postgres poller on the existing `jobs` table** (`SELECT … FOR UPDATE SKIP LOCKED`) | — (no dependency) | ✅ **Recommended.** Reuses the existing `Job` model, needs no Redis in production (one fewer free-tier service), and survives restarts. Fine at 10–20 users |
| [procrastinate-org/procrastinate](https://github.com/procrastinate-org/procrastinate) | MIT ◐ | ✅ Same idea, packaged (Postgres-native queue) |
| RQ | BSD-2 ◐ | ⚠️ Needs Redis and `fork`, so no Windows dev |
| Dramatiq | LGPL-3.0 ◐ | ⚠️ OK, but adds Redis/RabbitMQ |
| Celery | BSD-3 ◐ | ❌ Overkill |

Redis remains useful **optionally** for rate limiting and live progress pub/sub, but it should not be required.

---

## 5. Hosting feasibility findings

| Platform | Free allowance (verified ✔ / known ◐) | Use for | Caveat |
|---|---|---|---|
| **Vercel Hobby** | Free Next.js hosting ◐ | Frontend | Hobby is for non-commercial use, which suits a portfolio |
| **Render Free web service** | 512 MB RAM, ~0.1 CPU, **sleeps after 15 min idle, ~1 min cold start**, 750 h/month ✔ | Light API only | Too small for ASR/VLM/diffusion; no free background workers |
| **Render Free Postgres** | **Expires 30 days after creation** (some sources say 90) ✔ | — | ❌ Not suitable for a lasting portfolio |
| **Neon / Supabase Postgres free** | ~0.5 GB, does not expire ◐ | Database | ✅ Recommended replacement |
| **Cloudflare R2** / **Backblaze B2** | ~10 GB free storage, R2 has free egress ◐ | Durable media storage | May require a card on file → **your approval** |
| **Oracle Cloud Always Free (Ampere ARM)** | **Halved to 2 OCPU / 12 GB on 2026-06-15** ✔ (was 4/24) | CPU worker (ASR, TTS, OCR, Florence-2, FastSD-CPU) | Capacity often unavailable; ARM wheels needed; trial-expiry deletion rule ✔ |
| **Modal Starter** | **$30/month free compute credits**, scale-to-zero GPUs (T4 ≈ $0.59/h) ✔ | GPU worker (E7 FLUX, E8 Wan, E9 AnimateDiff) | A paid platform with free credits, so it **needs your approval**; a card is required |
| **Hugging Face ZeroGPU Spaces** | Free accounts can host 2 Spaces; daily GPU quota ≈ 5 min free / 40 min PRO ✔ | Demo/backup GPU endpoint | Quota is too small to serve 10–20 users from one account; PRO ≈ $9/month |
| **Cloudflare Workers AI** | 10,000 "neurons"/day free, shared across models ✔ | Possible hosted Whisper/FLUX/TTS | External inference API: **needs your approval**; per-model cost unverified |

See IMPLEMENTATION_ROADMAP.md §4 for the recommended combination and cost tiers.

---

## 6. Questions that change the plan

1. **Do you have a local NVIDIA GPU?** With ≥ 8 GB VRAM, GPU models can be developed and tested locally for free. Without one, GPU work has to wait for an approved cloud GPU (for example Modal's free credits).
2. **Will you approve one GPU provider** (Modal Starter's $30/month free credits is my recommendation), or should the public site ship with **Classic (CPU) modes only** at first?
3. **Will you approve a card-on-file free tier** for durable storage (R2/B2), or should storage stay in Postgres/Neon with small size limits?

---

## 7. Not researched / out of scope
- Music generation (not among the 20 conversions; most good models are non-commercial).
- Voice cloning (licence and ethics risks; not required).
- Paid APIs (OpenAI, Replicate, ElevenLabs and so on) are excluded per your rule.

## 8. Sources used for ✔ items
- Piper licence move: <https://www.cekura.ai/discover/piper-tts>, <https://www.promptquorum.com/power-local-llm/piper-tts-review>, <https://localaimaster.com/blog/best-local-tts-models>
- Kokoro-82M: <https://huggingface.co/hexgrad/Kokoro-82M/blob/main/README.md>, <https://docs.clore.ai/guides/audio-and-voice/kokoro-tts>
- Wan2.2 TI2V-5B: <https://en.immers.cloud/ai/wan-ai/Wan2.2-TI2V-5B-Diffusers/>, <https://hardwarepedia.com/ai/wan-2-2>, <https://dev.to/thurmon_demich/best-gpu-for-wan-22-in-2026-5-picks-ranked-14b-ready-120l>
- LTX-2 licence: <https://static.lightricks.com/legal/ltx-2-open-weights-license-0.X.pdf>, <https://ltx.io/model/license>, <https://ltx.io/blog/free-ai-video-generation>
- Moondream2 / Florence-2: <https://huggingface.co/vikhyatk/moondream2/blob/dffbe5f2716222b0784a2847698cd7f199d99d76/README.md>, <https://roboflow.com/model/moondream-2>, <https://playground.roboflow.com/models/compare/florence-2-vs-moondream-2>
- Render free tier: <https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026.md>, <https://temps.sh/blog/render-pricing-2026>, <https://livemy.app/blog/render-pricing>
- Modal: <https://modal.com/pricing>, <https://freetier.co/directory/products/modal>, <https://www.morphllm.com/modal-pricing>
- HF ZeroGPU: <https://huggingface.co/docs/hub/en/spaces-zerogpu>
- Oracle Always Free change: <https://buttondown.com/freetierwatch/archive/oracle-quietly-halved-its-famous-free-tier-and/>, <https://terminalbytes.com/oracle-cloud-free-tier-changes-2026>
- Cloudflare Workers AI: <https://developers.cloudflare.com/workers-ai/platform/pricing/>
