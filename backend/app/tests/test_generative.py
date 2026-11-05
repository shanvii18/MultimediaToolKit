"""
Generative conversions: every CPU mode is executed for real (FFmpeg / Pillow / Kokoro /
Whisper) and the produced files are decoded and checked. AI modes are exercised against a
mocked HTTP provider (httpx.MockTransport) to verify request format, response parsing,
error handling and pipeline wiring -- no live provider is contacted in tests.
"""
import base64
import io
import json
import subprocess

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.adapters.ai_provider import AIProviderError, ai_provider
from app.adapters.ffmpeg_adapter import ffmpeg_adapter
from app.adapters.tts_adapter import tts_adapter
from app.core.config import settings
from app.engines import availability

client = TestClient(app)
HAS_FFMPEG = ffmpeg_adapter.is_available()
HAS_TTS = HAS_FFMPEG and tts_adapter.availability() is None and tts_adapter._files_present()
pytestmark = pytest.mark.skipif(not HAS_FFMPEG, reason="FFmpeg not installed")
needs_tts = pytest.mark.skipif(not HAS_TTS, reason="Kokoro TTS model not available locally")


# ---------------- helpers ----------------
def ffmpeg(*args):
    res = subprocess.run([ffmpeg_adapter.get_ffmpeg_cmd(), "-y", "-hide_banner", "-loglevel", "error", *args],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, res.stderr


def upload(path, name=None):
    with open(path, "rb") as f:
        res = client.post("/api/v1/media", files={"file": (name or path.name, f, "application/octet-stream")})
    assert res.status_code == 200, res.text
    return res.json()["id"]


def run(worker, tool, inputs=(), **params):
    res = client.post("/api/v1/jobs", json={"tool": tool, "input_asset_ids": list(inputs), "params_json": params})
    assert res.status_code == 200, res.text
    worker.drain()
    job = client.get(f"/api/v1/jobs/{res.json()['id']}").json()
    return job


def ok(job):
    assert job["status"] == "succeeded", f"{job['error_code']}: {job['error_message']}"
    return {o["output_type"]: o["asset"] for o in job["outputs"]}


def fetch(asset) -> bytes:
    res = client.get(asset["download_url"])
    assert res.status_code == 200
    return res.content


def probe_bytes(data: bytes, suffix: str, tmp_path):
    path = tmp_path / f"probe{suffix}"
    path.write_bytes(data)
    return ffmpeg_adapter.probe(str(path))


@pytest.fixture(scope="module")
def media(tmp_path_factory):
    d = tmp_path_factory.mktemp("gen")
    ffmpeg("-f", "lavfi", "-i", "sine=frequency=330:duration=4", "-f", "lavfi", "-i", "sine=frequency=550:duration=4",
           "-filter_complex", "[0][1]amix=inputs=2,volume=3,tremolo=f=3:d=0.9", str(d / "music.mp3"))
    ffmpeg("-f", "lavfi", "-i", "testsrc2=duration=4:size=320x240:rate=15", "-f", "lavfi", "-i",
           "sine=frequency=440:duration=4", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
           str(d / "clip.mp4"))
    img = Image.new("RGB", (640, 400))
    for x in range(640):
        for y in range(0, 400, 4):
            img.putpixel((x, y), ((x * 3) % 255, (y * 2) % 255, 140))
    img.save(d / "photo.jpg")
    frames = [Image.new("RGB", (160, 120), c) for c in ("#ef4444", "#22c55e", "#3b82f6", "#eab308")]
    for i, f in enumerate(frames):
        f.paste((255, 255, 255), (20 + i * 25, 30, 60 + i * 25, 90))
    frames[0].save(d / "anim.gif", save_all=True, append_images=frames[1:], duration=150, loop=0)
    frames[0].save(d / "anim.webp", save_all=True, append_images=frames[1:], duration=150, loop=0)
    return d


@pytest.fixture
def ai_mock(monkeypatch):
    """Configure a fake Cloudflare Workers AI account served by an in-process mock transport."""
    calls = []
    png = io.BytesIO()
    Image.new("RGB", (512, 512), (90, 40, 160)).save(png, "PNG")
    png_b64 = base64.b64encode(png.getvalue()).decode()

    def handler(request: httpx.Request):
        calls.append(request)
        assert request.headers["authorization"] == "Bearer test-token"
        body = json.loads(request.content or b"{}")
        if "flux" in request.url.path:
            assert body["prompt"]
            return httpx.Response(200, json={"success": True, "result": {"image": png_b64}})
        if "llava" in request.url.path:
            assert isinstance(body["image"], list) and body["image"][:2] == [0xFF, 0xD8]  # JPEG bytes
            return httpx.Response(200, json={"success": True,
                                             "result": {"description": " a colourful scene with bright shapes."}})
        return httpx.Response(404)

    monkeypatch.setattr(settings, "AI_PROVIDER", "cloudflare")
    monkeypatch.setattr(settings, "CLOUDFLARE_ACCOUNT_ID", "acct123")
    monkeypatch.setattr(settings, "CLOUDFLARE_API_TOKEN", "test-token")
    monkeypatch.setattr(ai_provider, "_transport", httpx.MockTransport(handler))
    availability.reset_cache()
    yield calls
    availability.reset_cache()


# =====================================================================
# Catalogue: all 20 are runnable
# =====================================================================
def test_all_20_conversions_have_a_runnable_mode():
    items = client.get("/api/v1/conversions").json()
    assert len(items) == 20
    for c in items:
        assert c["status"] != "coming_soon", c["id"]
        assert any(m["status"] != "coming_soon" for m in c["modes"]), c["id"]


def test_ai_modes_report_configuration_needed_without_credentials(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "none")
    availability.reset_cache()
    res = client.post("/api/v1/jobs", json={"tool": "text_to_image", "params_json": {"mode": "ai", "text": "a fox"}})
    assert res.status_code == 503 and "not configured" in res.json()["detail"]
    availability.reset_cache()


# =====================================================================
# Text -> Image / Animation / Video
# =====================================================================
def test_text_to_image_poster(worker):
    outs = ok(run(worker, "text_to_image", mode="poster", text="Ideas become media", aspect="landscape",
                  style="ocean", image_format="jpg"))
    img = Image.open(io.BytesIO(fetch(outs["image_jpg"])))
    assert img.size == (1280, 720)
    assert outs["image_jpg"]["metadata_json"]["ai_generated"] is False


def test_text_to_image_ai_with_mocked_provider(worker, ai_mock):
    outs = ok(run(worker, "text_to_image", mode="ai", text="a red fox in snow", aspect="square"))
    assert Image.open(io.BytesIO(fetch(outs["image_png"]))).size == (512, 512)
    assert outs["image_png"]["metadata_json"]["ai_generated"] is True
    assert "/ai/run/@cf/black-forest-labs/flux-1-schnell" in str(ai_mock[0].url)


def test_ai_provider_errors_surface_honestly(worker, ai_mock, monkeypatch):
    monkeypatch.setattr(ai_provider, "_transport", httpx.MockTransport(lambda r: httpx.Response(429, text="limit")))
    job = run(worker, "text_to_image", mode="ai", text="a fox")
    assert job["status"] == "failed" and job["error_code"] == "AI_PROVIDER_ERROR"
    assert "allowance" in job["error_message"] and job["outputs"] == []


def test_huggingface_provider_request_format(monkeypatch):
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        return httpx.Response(200, content=b"\x89PNG\r\n\x1a\nfake", headers={"content-type": "image/png"})

    monkeypatch.setattr(settings, "AI_PROVIDER", "huggingface")
    monkeypatch.setattr(settings, "HF_API_TOKEN", "hf_x")
    monkeypatch.setattr(ai_provider, "_transport", httpx.MockTransport(handler))
    assert ai_provider.generate_image("cat").startswith(b"\x89PNG")
    assert seen["url"].endswith("/black-forest-labs/FLUX.1-schnell")
    monkeypatch.setattr(ai_provider, "_transport", httpx.MockTransport(lambda r: httpx.Response(401)))
    with pytest.raises(AIProviderError, match="credentials"):
        ai_provider.generate_image("cat")


@pytest.mark.parametrize("fmt", ["gif", "webp"])
def test_text_to_animation_kinetic(worker, fmt):
    outs = ok(run(worker, "text_to_animation", mode="kinetic", text="Make every format talk", animation_format=fmt))
    anim = Image.open(io.BytesIO(fetch(outs[f"animation_{fmt}"])))
    assert anim.is_animated and anim.n_frames > 10


def test_text_to_animation_ai_loop(worker, ai_mock):
    outs = ok(run(worker, "text_to_animation", mode="ai_loop", text="glowing jellyfish"))
    anim = Image.open(io.BytesIO(fetch(outs["animation_gif"])))
    assert anim.is_animated and anim.n_frames > 20


@needs_tts
def test_text_to_video_narrated(worker, tmp_path):
    script = "Welcome to the toolkit. Every format can become another. Thanks for watching."
    outs = ok(run(worker, "text_to_video", mode="slides", text=script, aspect="landscape", voice="af_bella"))
    info = probe_bytes(fetch(outs["video_mp4"]), ".mp4", tmp_path)
    assert info.has_video and info.has_audio and info.width == 1280 and info.duration > 4
    srt = fetch(outs["subtitles_srt"]).decode()
    assert "Every format can become another." in srt and srt.count("-->") == 3


def test_text_to_video_silent_ai_scenes(worker, ai_mock, tmp_path):
    outs = ok(run(worker, "text_to_video", mode="ai_scenes", text="A forest wakes up. Birds begin to sing.",
                  narrate=False, aspect="square"))
    info = probe_bytes(fetch(outs["video_mp4"]), ".mp4", tmp_path)
    assert info.width == 1080 and info.height == 1080 and info.duration > 5
    assert len([c for c in ai_mock if "flux" in c.url.path]) == 2


def test_text_to_video_rejects_too_many_scenes(worker):
    job = run(worker, "text_to_video", mode="slides", text=" ".join(f"Scene {i} here." * 12 for i in range(20))[:1800],
              narrate=False)
    assert job["status"] == "failed" and job["error_code"] == "INPUT_TOO_LONG"


# =====================================================================
# Audio -> Image / Video / Animation
# =====================================================================
@pytest.mark.parametrize("mode,suffix", [("waveform", "waveform"), ("spectrogram", "spectrogram")])
def test_audio_to_image_cpu_modes(worker, media, mode, suffix):
    outs = ok(run(worker, "audio_to_image", [upload(media / "music.mp3")], mode=mode))
    img = Image.open(io.BytesIO(fetch(outs["image_png"])))
    assert img.size[0] >= 1280 and suffix in outs["image_png"]["filename"]  # spectrogram legend adds margins


def test_audio_to_image_ai_cover(worker, media, ai_mock):
    outs = ok(run(worker, "audio_to_image", [upload(media / "music.mp3")], mode="ai_cover", prompt_hint="neon city"))
    meta = outs["image_png"]["metadata_json"]
    assert meta["ai_generated"] and "neon city" in meta["prompt"] and "Mood:" in meta["prompt"]


@pytest.mark.parametrize("style", ["waves", "spectrum", "bars"])
def test_audio_to_video_visualizer(worker, media, style, tmp_path):
    outs = ok(run(worker, "audio_to_video", [upload(media / "music.mp3")], mode="visualizer", visual_style=style,
                  aspect="square"))
    info = probe_bytes(fetch(outs["video_mp4"]), ".mp4", tmp_path)
    assert info.has_video and info.has_audio and (info.width, info.height) == (1080, 1080)
    assert 3.5 < info.duration < 4.6


def test_audio_to_video_rejects_file_without_audio(worker, media):
    job = run(worker, "audio_to_video", [upload(media / "anim.gif", "fake.mp3")], mode="visualizer")
    assert job["status"] == "failed"


@pytest.mark.parametrize("mode", ["waveform", "pulse"])
def test_audio_to_animation_cpu_modes(worker, media, mode):
    outs = ok(run(worker, "audio_to_animation", [upload(media / "music.mp3")], mode=mode, seconds=2))
    anim = Image.open(io.BytesIO(fetch(outs["animation_gif"])))
    assert anim.is_animated and anim.n_frames >= 10


def test_audio_to_animation_start_beyond_end(worker, media):
    job = run(worker, "audio_to_animation", [upload(media / "music.mp3")], mode="pulse", start=60)
    assert job["status"] == "failed" and "beyond the end" in job["error_message"]


# =====================================================================
# Image -> Video / Animation (+ AI description modes)
# =====================================================================
@pytest.mark.parametrize("motion_name", ["zoom_in", "pan_left"])
def test_image_to_video_ken_burns(worker, media, motion_name, tmp_path):
    outs = ok(run(worker, "image_to_video", [upload(media / "photo.jpg")], mode="ken_burns", motion=motion_name,
                  seconds=3, aspect="portrait"))
    info = probe_bytes(fetch(outs["video_mp4"]), ".mp4", tmp_path)
    assert (info.width, info.height) == (720, 1280) and 2.8 < info.duration < 3.3 and not info.has_audio


@needs_tts
def test_image_to_video_ai_narrated(worker, media, ai_mock, tmp_path):
    outs = ok(run(worker, "image_to_video", [upload(media / "photo.jpg")], mode="narrated"))
    info = probe_bytes(fetch(outs["video_mp4"]), ".mp4", tmp_path)
    assert info.has_audio and info.duration > 1.5
    assert "colourful scene" in outs["description_txt"]["metadata_json"]["preview_text"]


def test_image_to_animation_loop(worker, media):
    outs = ok(run(worker, "image_to_animation", [upload(media / "photo.jpg")], mode="loop", animation_format="webp"))
    anim = Image.open(io.BytesIO(fetch(outs["animation_webp"])))
    assert anim.is_animated and anim.n_frames > 30  # forward + reverse


def test_image_to_text_ai_describe(worker, media, ai_mock):
    outs = ok(run(worker, "image_to_text", [upload(media / "photo.jpg")], mode="describe"))
    assert fetch(outs["description_txt"]).decode().startswith("A colourful scene")


@needs_tts
def test_image_to_audio_ai_describe(worker, media, ai_mock):
    outs = ok(run(worker, "image_to_audio", [upload(media / "photo.jpg")], mode="describe", audio_format="mp3"))
    assert set(outs) == {"description_txt", "audio_mp3"}


# =====================================================================
# Video -> Animation / Image posters
# =====================================================================
@pytest.mark.parametrize("effect,fmt", [("none", "gif"), ("cartoon", "webp"), ("vintage", "gif")])
def test_video_to_animation(worker, media, effect, fmt):
    outs = ok(run(worker, "video_to_animation", [upload(media / "clip.mp4")], start=1, duration=2, fps=10, width=240,
                  effect=effect, animation_format=fmt))
    anim = Image.open(io.BytesIO(fetch(outs[f"animation_{fmt}"])))
    assert anim.is_animated and anim.width == 240 and 15 <= anim.n_frames <= 25


def test_video_to_animation_boomerang_doubles_frames(worker, media):
    outs = ok(run(worker, "video_to_animation", [upload(media / "clip.mp4")], duration=1, fps=10, width=200,
                  boomerang=True))
    assert Image.open(io.BytesIO(fetch(outs["animation_gif"]))).n_frames >= 18


def test_video_to_image_poster(worker, media):
    outs = ok(run(worker, "video_to_image", [upload(media / "clip.mp4")], mode="poster", title="Launch Night"))
    img = Image.open(io.BytesIO(fetch(outs["image_png"])))
    assert img.size == (720, 1280)


def test_video_to_image_ai_poster(worker, media, ai_mock):
    outs = ok(run(worker, "video_to_image", [upload(media / "clip.mp4")], mode="ai_poster", title="Launch Night"))
    paths = [c.url.path for c in ai_mock]
    assert any("llava" in p for p in paths) and any("flux" in p for p in paths)
    assert outs["image_png"]["metadata_json"]["ai_generated"] is True


# =====================================================================
# Animation -> Image / Video (+ AI describe/narrate)
# =====================================================================
@pytest.mark.parametrize("source", ["anim.gif", "anim.webp", "clip.mp4"])
def test_animation_to_image_modes(worker, media, source):
    asset = upload(media / source)
    best = ok(run(worker, "animation_to_image", [asset], mode="best_frame"))
    assert Image.open(io.BytesIO(fetch(best["image_png"]))).size[0] > 0
    sheet = ok(run(worker, "animation_to_image", [asset], mode="contact_sheet", frames=4, columns=2))
    assert Image.open(io.BytesIO(fetch(sheet["image_png"]))).size[0] == 2 * 320 + 3 * 8
    poster = ok(run(worker, "animation_to_image", [asset], mode="poster", title="Loop"))
    assert "poster" in poster["image_png"]["filename"]


@pytest.mark.parametrize("source,fmt,smooth", [("anim.gif", "mp4", False), ("anim.webp", "mp4", True),
                                               ("anim.gif", "webm", False), ("clip.mp4", "mp4", False)])
def test_animation_to_video(worker, media, source, fmt, smooth, tmp_path):
    outs = ok(run(worker, "animation_to_video", [upload(media / source)], loops=2, smooth=smooth, video_format=fmt))
    info = probe_bytes(fetch(outs[f"video_{fmt}"]), f".{fmt}", tmp_path)
    assert info.has_video and info.duration > 0.9
    if source.startswith("anim"):
        assert 1.0 <= info.duration <= 1.5  # 4 frames x 150 ms x 2 loops = 1.2 s


def test_animation_to_text_ai_describe(worker, media, ai_mock):
    outs = ok(run(worker, "animation_to_text", [upload(media / "anim.gif")], mode="describe"))
    assert fetch(outs["description_txt"]).decode().count("colourful scene") == 3


@needs_tts
def test_animation_to_audio_ai_narrate(worker, media, ai_mock):
    outs = ok(run(worker, "animation_to_audio", [upload(media / "anim.gif")], mode="narrate", audio_format="wav"))
    assert fetch(outs["audio_wav"])[:4] == b"RIFF"
