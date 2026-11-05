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
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIProviderError(RuntimeError):
    pass


class AIProvider:
    engine_image = "ai_image"
    engine_caption = "ai_caption"

    def __init__(self, transport: Optional[httpx.BaseTransport] = None):
        self._transport = transport  # injectable for tests

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

    @staticmethod
    def _raise_for(res: httpx.Response, what: str) -> None:
        if res.status_code >= 400:
            detail = res.text[:300].replace("\n", " ")
            if res.status_code in (401, 403):
                raise AIProviderError(f"{what} failed: the AI provider rejected the credentials ({res.status_code}).")
            if res.status_code == 429:
                raise AIProviderError(f"{what} failed: the AI provider's free allowance or rate limit was reached.")
            raise AIProviderError(f"{what} failed: provider returned HTTP {res.status_code}: {detail}")

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
                res = client.post(url, headers={"Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}"},
                                  json={"prompt": prompt, "steps": max(1, min(8, steps))})
                self._raise_for(res, "Image generation")
                if res.headers.get("content-type", "").startswith("image/"):
                    return res.content
                data = res.json()
                image_b64 = (data.get("result") or {}).get("image")
                if not image_b64:
                    raise AIProviderError("Image generation failed: provider returned no image.")
                return base64.b64decode(image_b64)

            url = f"{settings.HF_INFERENCE_BASE_URL.rstrip('/')}/{settings.HF_IMAGE_MODEL}"
            res = client.post(url, headers={"Authorization": f"Bearer {settings.HF_API_TOKEN}",
                                            "Accept": "image/png"},
                              json={"inputs": prompt,
                                    "parameters": {"width": width, "height": height, "num_inference_steps": steps}})
            self._raise_for(res, "Image generation")
            if not res.headers.get("content-type", "").startswith("image/"):
                raise AIProviderError("Image generation failed: provider did not return an image.")
            return res.content

    # ---------------- image -> description ----------------
    def describe_image(self, image_bytes: bytes,
                       instruction: str = "Describe this image in detail in 3-5 sentences.") -> str:
        reason = self.availability()
        if reason:
            raise AIProviderError(reason)
        with self._client() as client:
            if self.provider == "cloudflare":
                url = (f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}"
                       f"/ai/run/{settings.CLOUDFLARE_CAPTION_MODEL}")
                res = client.post(url, headers={"Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}"},
                                  json={"image": list(image_bytes), "prompt": instruction, "max_tokens": 300})
                self._raise_for(res, "Image description")
                text = ((res.json().get("result") or {}).get("description") or "").strip()
            else:
                url = f"{settings.HF_INFERENCE_BASE_URL.rstrip('/')}/{settings.HF_CAPTION_MODEL}"
                res = client.post(url, headers={"Authorization": f"Bearer {settings.HF_API_TOKEN}",
                                                "Content-Type": "application/octet-stream"},
                                  content=image_bytes)
                self._raise_for(res, "Image description")
                data = res.json()
                item = data[0] if isinstance(data, list) and data else data
                text = (item.get("generated_text") if isinstance(item, dict) else "") or ""
                text = text.strip()
        if not text:
            raise AIProviderError("Image description failed: provider returned no text.")
        return text[0].upper() + text[1:] if text else text


ai_provider = AIProvider()
