"""
Optional hosted AI provider for capabilities that need a GPU-class model:
  - text-to-image generation  (FLUX.1-schnell, Apache-2.0 weights)
  - image description         (LLaVA-1.5 on Cloudflare / BLIP on Hugging Face)

Nothing is called unless AI_PROVIDER is configured with credentials. Without them the
AI modes are reported as "needs configuration" and are never faked. CPU modes of every
workflow keep working.

Providers:
  cloudflare  -> POST https://api.cloudflare.com/client/v4/accounts/{id}/ai/run/{model}
  huggingface -> POST {HF_INFERENCE_BASE_URL}/{model}
"""
import base64
import io
import logging
import threading
import time
from typing import Optional, Tuple

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIProviderError(RuntimeError):
    pass



def _sniff_mime(data: bytes) -> str:
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


class AIProvider:
    engine_image = "ai_image"
    engine_caption = "ai_caption"

    engine_img2img = "ai_img2img"

    def __init__(self, transport: Optional[httpx.BaseTransport] = None):
        self._transport = transport  # injectable for tests
        self._issue: Optional[Tuple[float, str]] = None
        self._lock = threading.Lock()

    # ---- runtime health: a recent provider failure marks AI modes "temporarily unavailable" ----
    def _record_failure(self, message: str) -> None:
        with self._lock:
            self._issue = (time.monotonic(), message)

    def _record_success(self) -> None:
        with self._lock:
            self._issue = None

    def runtime_issue(self) -> Optional[str]:
        with self._lock:
            if not self._issue:
                return None
            at, message = self._issue
            if time.monotonic() - at > settings.AI_FAILURE_COOLDOWN_SECONDS:
                self._issue = None
                return None
            return message

    def img2img_availability(self) -> Optional[str]:
        reason = self.availability()
        if reason:
            return reason
        if self.provider != "cloudflare":
            return ("AI restyle needs AI_PROVIDER=cloudflare (the free Hugging Face inference tier has no "
                    "image-to-image model).")
        return None

    def _post(self, client: httpx.Client, url: str, what: str, **kwargs) -> httpx.Response:
        try:
            res = client.post(url, **kwargs)
        except httpx.TimeoutException:
            msg = f"{what} failed: the AI provider did not answer within {settings.AI_TIMEOUT_SECONDS} s."
            self._record_failure(msg)
            raise AIProviderError(msg)
        except httpx.HTTPError:
            msg = f"{what} failed: the AI provider could not be reached."
            self._record_failure(msg)
            raise AIProviderError(msg)
        self._raise_for(res, what)
        return res

    @property
    def provider(self) -> str:
        return (settings.AI_PROVIDER or "none").strip().lower()

    def availability(self) -> Optional[str]:
        p = self.provider
        if p == "cloudflare":
            if not (settings.CLOUDFLARE_ACCOUNT_ID and settings.CLOUDFLARE_API_TOKEN):
                return "AI provider 'cloudflare' needs CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN."
            return None
        if p == "huggingface":
            if not settings.HF_API_TOKEN:
                return "AI provider 'huggingface' needs HF_API_TOKEN."
            return None
        if p in ("", "none"):
            return ("AI generation is not configured on this server "
                    "(set AI_PROVIDER=cloudflare or huggingface with credentials).")
        return f"Unknown AI_PROVIDER '{settings.AI_PROVIDER}'."

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=settings.AI_TIMEOUT_SECONDS, transport=self._transport)

    def _raise_for(self, res: httpx.Response, what: str) -> None:
        if res.status_code >= 400:
            detail = res.text[:300].replace("\n", " ")
            if res.status_code in (401, 403):
                msg = f"{what} failed: the AI provider rejected the credentials ({res.status_code})."
                self._record_failure(msg)
                raise AIProviderError(msg)
            if res.status_code == 429:
                msg = f"{what} failed: the AI provider's free daily allowance or rate limit was reached."
                self._record_failure(msg)
                raise AIProviderError(msg)
            msg = f"{what} failed: provider returned HTTP {res.status_code}: {detail}"
            if res.status_code >= 500:
                self._record_failure(msg)
            raise AIProviderError(msg)

    # ---------------- speech (Cloudflare only) ----------------
    def cloudflare_ready(self) -> bool:
        return self.provider == "cloudflare" and self.availability() is None

    @staticmethod
    def gemini_enabled() -> bool:
        return bool((settings.GEMINI_API_KEY or "").strip())

    def speech_enabled(self) -> bool:
        return settings.CLOUD_SPEECH and (self.gemini_enabled() or self.cloudflare_ready())

    def caption_availability(self) -> Optional[str]:
        return None if self.gemini_enabled() else self.availability()

    def _gemini(self, client: httpx.Client, model: str, what: str, body: dict) -> list:
        res = self._quiet(lambda: self._post(
            client, f"{settings.GEMINI_BASE_URL.rstrip('/')}/{model}:generateContent", what,
            headers={"x-goog-api-key": settings.GEMINI_API_KEY.strip()}, json=body))
        try:
            return res.json()["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, TypeError, ValueError):
            raise AIProviderError(f"{what} failed: Gemini returned no content.")

    def _gemini_speak(self, client: httpx.Client, text: str, voice: str) -> bytes:
        parts = self._gemini(client, settings.GEMINI_TTS_MODEL, "Speech synthesis", {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}})
        data = next((p["inlineData"] for p in parts if "inlineData" in p), None)
        if not data:
            raise AIProviderError("Speech synthesis failed: Gemini returned no audio.")
        audio = base64.b64decode(data["data"])
        if audio[:4] == b"RIFF":
            return audio
        import re
        import wave

        m = re.search(r"rate=(\d+)", data.get("mimeType", ""))          # raw 16-bit PCM (audio/L16;rate=24000)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(int(m.group(1)) if m else 24000)
            w.writeframes(audio)
        return buf.getvalue()

    def _quiet(self, fn):
        """Speech has a local fallback, so its failures must not mark every AI mode unavailable."""
        with self._lock:
            before = self._issue
        try:
            return fn()
        except AIProviderError:
            with self._lock:
                self._issue = before
            raise

    def _cf_url(self, model: str) -> str:
        return f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/ai/run/{model}"

    def speak_wav(self, text: str, speaker: str, gemini_voice: str = "Kore") -> Tuple[bytes, str]:
        """Text -> WAV bytes. Returns (wav, engine label). Tries Gemini TTS, Deepgram Aura-2, then MeloTTS."""
        if not self.speech_enabled():
            raise AIProviderError("Cloud speech is not enabled.")
        auth = {"Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}"}
        errors = []
        with self._client() as client:
            if self.gemini_enabled():
                try:
                    wav = self._gemini_speak(client, text, gemini_voice)
                    return wav, f"Gemini TTS ({settings.GEMINI_TTS_MODEL}, voice {gemini_voice})"
                except AIProviderError as e:
                    errors.append(str(e))
            if not self.cloudflare_ready():
                raise AIProviderError("; ".join(errors) or "No speech provider is configured.")
            try:
                res = self._quiet(lambda: self._post(
                    client, self._cf_url(settings.CLOUDFLARE_TTS_MODEL), "Speech synthesis", headers=auth,
                    json={"text": text, "speaker": speaker, "encoding": "linear16", "container": "wav",
                          "sample_rate": 24000}))
                if res.content[:4] == b"RIFF":
                    return res.content, f"Deepgram Aura-2 ({speaker}, Cloudflare Workers AI)"
                errors.append("Aura returned no audio")
            except AIProviderError as e:
                errors.append(str(e))
            if settings.CLOUDFLARE_TTS_FALLBACK_MODEL:
                try:
                    res = self._quiet(lambda: self._post(
                        client, self._cf_url(settings.CLOUDFLARE_TTS_FALLBACK_MODEL), "Speech synthesis",
                        headers=auth, json={"prompt": text, "lang": "en"}))
                    audio = ((res.json() or {}).get("result") or {}).get("audio")
                    wav = base64.b64decode(audio) if audio else b""
                    if wav[:4] == b"RIFF":
                        return wav, "MeloTTS (Cloudflare Workers AI)"
                    errors.append("MeloTTS returned no audio")
                except (AIProviderError, ValueError) as e:
                    errors.append(str(e))
        raise AIProviderError("; ".join(errors))

    def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> dict:
        """Audio file bytes (any FFmpeg-readable format) -> Whisper large-v3-turbo result dict."""
        if not (settings.CLOUD_SPEECH and self.cloudflare_ready()):
            raise AIProviderError("Cloud speech is not enabled.")
        if len(audio_bytes) > settings.CLOUD_ASR_MAX_BYTES:
            raise AIProviderError("Audio is too large for the cloud transcriber.")
        body = {"audio": base64.b64encode(audio_bytes).decode(), "vad_filter": True,
                "condition_on_previous_text": False}
        if language:
            body["language"] = language
        with self._client() as client:
            res = self._quiet(lambda: self._post(
                client, self._cf_url(settings.CLOUDFLARE_ASR_MODEL), "Transcription",
                headers={"Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}"}, json=body))
        result = (res.json() or {}).get("result") or {}
        if "segments" not in result and "text" not in result:
            raise AIProviderError("Transcription failed: provider returned no transcript.")
        return result

    # ---------------- text -> image ----------------
    def generate_image(self, prompt: str, width: int = 1024, height: int = 1024, steps: int = 4) -> bytes:
        reason = self.availability()
        if reason:
            raise AIProviderError(reason)
        prompt = (prompt or "").strip()[:2000]
        if not prompt:
            raise AIProviderError("An image prompt is required.")
        with self._client() as client:
            if self.provider == "cloudflare":
                url = (f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}"
                       f"/ai/run/{settings.CLOUDFLARE_IMAGE_MODEL}")
                res = self._post(client, url, "Image generation",
                                 headers={"Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}"},
                                 json={"prompt": prompt, "steps": max(1, min(8, steps))})
                if res.headers.get("content-type", "").startswith("image/"):
                    return self._valid_image(res.content, "Image generation")
                data = res.json()
                image_b64 = (data.get("result") or {}).get("image")
                if not image_b64:
                    raise AIProviderError("Image generation failed: provider returned no image.")
                return self._valid_image(base64.b64decode(image_b64), "Image generation")

            url = f"{settings.HF_INFERENCE_BASE_URL.rstrip('/')}/{settings.HF_IMAGE_MODEL}"
            res = self._post(client, url, "Image generation",
                             headers={"Authorization": f"Bearer {settings.HF_API_TOKEN}", "Accept": "image/png"},
                             json={"inputs": prompt,
                                   "parameters": {"width": width, "height": height, "num_inference_steps": steps}})
            if not res.headers.get("content-type", "").startswith("image/"):
                raise AIProviderError("Image generation failed: provider did not return an image.")
            return self._valid_image(res.content, "Image generation")

    # ---------------- image -> description ----------------
    last_caption_engine: str = "AI image description"

    def describe_image(self, image_bytes: bytes,
                       instruction: str = "Describe this image in detail in 3-5 sentences.") -> str:
        gemini_error = None
        if self.gemini_enabled():
            try:
                with self._client() as client:
                    parts = self._gemini(client, settings.GEMINI_VISION_MODEL, "Image description", {"contents": [{"parts": [
                        {"inline_data": {"mime_type": _sniff_mime(image_bytes),
                                         "data": base64.b64encode(image_bytes).decode()}},
                        {"text": instruction + " Plain prose, no markdown."}]}]})
                text = " ".join(p.get("text", "") for p in parts).strip()
                if text:
                    self.last_caption_engine = f"Gemini ({settings.GEMINI_VISION_MODEL})"
                    text = text[:1500]
                    return text[0].upper() + text[1:]
                gemini_error = "Gemini returned no description."
            except AIProviderError as e:
                gemini_error = str(e)
        reason = self.availability()
        if reason:
            raise AIProviderError(gemini_error or reason)
        self.last_caption_engine = (f"LLaVA ({settings.CLOUDFLARE_CAPTION_MODEL}, Cloudflare)"
                                    if self.provider == "cloudflare" else f"{settings.HF_CAPTION_MODEL} (Hugging Face)")
        with self._client() as client:
            if self.provider == "cloudflare":
                url = (f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}"
                       f"/ai/run/{settings.CLOUDFLARE_CAPTION_MODEL}")
                res = self._post(client, url, "Image description",
                                 headers={"Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}"},
                                 json={"image": list(image_bytes), "prompt": instruction, "max_tokens": 300})
                text = ((res.json().get("result") or {}).get("description") or "").strip()
            else:
                url = f"{settings.HF_INFERENCE_BASE_URL.rstrip('/')}/{settings.HF_CAPTION_MODEL}"
                res = self._post(client, url, "Image description",
                                 headers={"Authorization": f"Bearer {settings.HF_API_TOKEN}",
                                          "Content-Type": "application/octet-stream"},
                                 content=image_bytes)
                data = res.json()
                item = data[0] if isinstance(data, list) and data else data
                text = (item.get("generated_text") if isinstance(item, dict) else "") or ""
                text = text.strip()
        if not text:
            raise AIProviderError("Image description failed: provider returned no text.")
        self._record_success()
        text = text[:1500]
        return text[0].upper() + text[1:]

    # ---------------- image -> image (restyle) ----------------
    def transform_image(self, image_bytes: bytes, prompt: str, strength: float = 0.6) -> bytes:
        """Restyle an image with a text prompt (img2img, DreamShaper 8 LCM on Cloudflare Workers AI)."""
        reason = self.img2img_availability()
        if reason:
            raise AIProviderError(reason)
        prompt = (prompt or "").strip()[:1000]
        if not prompt:
            raise AIProviderError("A style prompt is required.")
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((512, 512))                       # SD 1.5 works at ~512 px; keeps the request small
        buf = io.BytesIO()
        if min(img.size) < 256:                         # model minimum; upscale keeping the aspect ratio
            k = 256 / min(img.size)
            img = img.resize((round(img.width * k), round(img.height * k)))
        img = img.resize((img.width // 8 * 8, img.height // 8 * 8))  # model needs sizes divisible by 8
        img.save(buf, "PNG")
        # The UI slider is 0.2-0.9; this model already repaints heavily at 0.5, so map it to 0.1-0.5
        # (measured: 0.3 keeps the composition, 0.9 ignores the source entirely).
        s = max(0.2, min(0.9, float(strength)))
        effective = round(0.1 + (s - 0.2) * (0.4 / 0.7), 3)
        url = (f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}"
               f"/ai/run/{settings.CLOUDFLARE_IMG2IMG_MODEL}")
        with self._client() as client:
            res = self._post(client, url, "AI restyle",
                             headers={"Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}"},
                             json={"prompt": prompt, "image": list(buf.getvalue()), "strength": effective,
                                   "width": img.width, "height": img.height, "num_steps": 20})
        if res.headers.get("content-type", "").startswith("image/"):
            return self._valid_image(res.content, "AI restyle")
        image_b64 = ((res.json() or {}).get("result") or {}).get("image")
        if not image_b64:
            raise AIProviderError("AI restyle failed: provider returned no image.")
        return self._valid_image(base64.b64decode(image_b64), "AI restyle")

    def _valid_image(self, data: bytes, what: str) -> bytes:
        """Reject empty/corrupt payloads so a broken provider answer is never saved as a 'result'."""
        from PIL import Image

        try:
            with Image.open(io.BytesIO(data)) as im:
                im.verify()
        except Exception:
            raise AIProviderError(f"{what} failed: the provider returned data that is not a valid image.")
        self._record_success()
        return data


ai_provider = AIProvider()
