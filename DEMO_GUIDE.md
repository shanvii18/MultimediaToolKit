# Live demo guide (presentation, LinkedIn, resume)

- **Website:** https://multimedia-tool-kit.vercel.app
- **Backend API:** https://mtk-backend.onrender.com (health check: `/health`)
- **Hosting (all free):** Vercel Hobby (frontend), Render Free (FastAPI backend), Neon Free (PostgreSQL)

## 10 minutes before you present

1. **Wake the backend.** Render Free sleeps after 15 idle minutes, and the first request takes about a minute.
   Open https://mtk-backend.onrender.com/health and wait until it shows `{"status":"ok"}`.
2. **Sign in** with your email and password (`/login`). The site keeps you signed in on this browser for
   30 days. Classmates can create their own free account there (**Create account**). No invite is needed.
3. **Warm up the speech models.** Run one **Text → Audio** conversion. The first speech job after a restart
   downloads its model (about 1 minute). After that, speech jobs take seconds.
4. Keep the sample files in [`demo-files/`](demo-files) ready on your laptop.

## Suggested 5-minute demo (fast and reliable on the free server)

| # | Conversion | Input | What to show |
|---|---|---|---|
| 1 | Text → Audio | type a sentence | natural speech (Kokoro TTS), play it in the browser |
| 2 | Audio → Text | `speech.wav` | transcript plus SRT/VTT subtitles (Whisper) |
| 3 | Image → Text | `sign.png` | OCR reads "HELLO 2026" (Tesseract) |
| 4 | Text → Image | type a title | generated poster image |
| 5 | Audio → Video | `speech.wav` | music-visualiser video with captions |
| 6 | Video → Animation | `talk.mp4` | GIF made from a video clip |
| 7 | Animation → Image | `words.gif` | contact sheet of the frames |

Then open **History** (every job, with its status) and **Media library** (uploads and results).

## All 20 conversions and their sample inputs

Text→Audio, Text→Image, Text→Video (`script.txt` or typed text), Text→Animation · Audio→Text, Audio→Image,
Audio→Video, Audio→Animation (`speech.wav`) · Image→Text, Image→Audio, Image→Video, Image→Animation (`sign.png`) ·
Video→Text, Video→Audio, Video→Image, Video→Animation, plus Animation→Text and Animation→Audio (`talk.mp4`) ·
Animation→Image, Animation→Video (`words.gif`).

Every conversion has a CPU mode that works on the free server. The modes labelled **AI provider** need an
external API key and show "not configured". That is expected, and the app never fakes a result.

## Talking points

- 5 formats × 4 targets = **20 real conversions**, with no fake outputs. Failures are reported honestly.
- **Engines:** FFmpeg, faster-whisper (speech-to-text), Kokoro-82M (text-to-speech), Tesseract (OCR), Pillow, all on CPU.
- **Durable job queue in PostgreSQL:** jobs survive restarts, and a crashed job is recovered and retried.
- **Security:** public sign-up with scrypt-hashed passwords, expiring session tokens (stored hashed),
  rate-limited sign-in, signed expiring download links, strict CORS, and per-user data isolation.
- **Tuned for 512 MB RAM:** thread caps and model unloading cut peak memory from about 970 MB to about 450 MB.
- 149 automated backend tests (SQLite and PostgreSQL), and a TypeScript production build.

## Known free-tier behaviour (say it before someone asks)

- **First request after idle is slow** (about 1 minute, the server is waking up).
- **Generated files are temporary.** They disappear when the free server restarts or sleeps, and downloading
  an old file then says "gone". Job history stays in the database.
- **Keep inputs short** (under about 1 minute of audio or video, images under a few MB). Long media can exceed
  the free server's 512 MB memory or CPU time, and the job is then marked failed.

## If something goes wrong during the demo

| Symptom | Fix |
|---|---|
| Site says it cannot reach the server | The backend is waking up. Wait 60 s and retry. |
| "Please sign in" or redirected to sign in | Your session expired or you signed out. Sign in again. |
| A job stays "queued" for a long time | The server restarted. Wait; it recovers queued jobs automatically. |
| Download says "gone" (410) | The server restarted and temporary files were cleared. Run the conversion again. |
| A speech job is slow the first time | The model is downloading after a restart. Later jobs are fast. |
