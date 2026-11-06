"""
Phase 1 workflow tests: registry/API integration and every implemented conversion.

Real-engine tests run the actual models (Whisper, Kokoro, FFmpeg, Tesseract) and are
skipped -- never faked -- when an engine or model is not present on the host. OCR
pipeline-integration tests additionally use a stubbed OCR engine so the pipeline logic
(frame sampling, chaining OCR -> TTS, outputs) is verified even where Tesseract is absent.
"""
import io
import json
import os
import subprocess

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.adapters.ffmpeg_adapter import ffmpeg_adapter
from app.adapters.ocr_adapter import OcrResult, ocr_adapter
from app.adapters.tts_adapter import split_text, tts_adapter
from app.adapters.whisper_adapter import whisper_adapter
from app.engines import availability
from app.engines.registry import CONVERSION_IDS

client = TestClient(app)

IMPLEMENTED = {"text_to_audio", "audio_to_text", "video_to_text", "video_to_audio", "animation_to_text",
               "animation_to_audio", "image_to_text", "image_to_audio", "video_to_image"}
SPEECH = "The quick brown fox jumps over the lazy dog. Testing the multimedia toolkit."

HAS_FFMPEG = ffmpeg_adapter.is_available()
HAS_TTS = HAS_FFMPEG and tts_adapter.availability() is None and tts_adapter._files_present()
HAS_ASR = HAS_FFMPEG and whisper_adapter.availability() is None and whisper_adapter._is_cached("base")
HAS_OCR = ocr_adapter.availability() is None

needs_ffmpeg = pytest.mark.skipif(not HAS_FFMPEG, reason="FFmpeg not installed")
needs_tts = pytest.mark.skipif(not HAS_TTS, reason="Kokoro TTS model not available locally")
needs_asr = pytest.mark.skipif(not (HAS_ASR and HAS_TTS), reason="Whisper/Kokoro models not available locally")
needs_ocr = pytest.mark.skipif(not (HAS_OCR and HAS_FFMPEG), reason="Tesseract OCR not installed on this host")


# ---------------- helpers ----------------
def upload_file(path, name=None):
    with open(path, "rb") as f:
        res = client.post("/api/v1/media", files={"file": (name or os.path.basename(path), f, "application/octet-stream")})
    assert res.status_code == 200, res.text
    return res.json()


def upload_bytes(data: bytes, name: str):
    res = client.post("/api/v1/media", files={"file": (name, io.BytesIO(data), "application/octet-stream")})
    assert res.status_code == 200, res.text
    return res.json()


def create_job(tool, inputs=(), **params):
    return client.post("/api/v1/jobs", json={"tool": tool, "input_asset_ids": list(inputs), "params_json": params})


def run_job(worker, tool, inputs=(), **params):
    res = create_job(tool, inputs, **params)
    assert res.status_code == 200, res.text
    worker.drain()
    return client.get(f"/api/v1/jobs/{res.json()['id']}").json()


def outputs_by_type(job):
    return {o["output_type"]: o["asset"] for o in job["outputs"]}


def download(asset) -> bytes:
    res = client.get(asset["download_url"])
    assert res.status_code == 200
    return res.content


def ffmpeg(*args):
    res = subprocess.run([ffmpeg_adapter.get_ffmpeg_cmd(), "-y", "-hide_banner", "-loglevel", "error", *args],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, res.stderr


@pytest.fixture(scope="module")
def media_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("media")


@pytest.fixture(scope="module")
def speech_wav(media_dir):
    if not HAS_TTS:
        pytest.skip("Kokoro TTS model not available locally")
    path = str(media_dir / "speech.wav")
    tts_adapter.synthesize_to_wav(SPEECH, path, voice="am_michael")
    return path


@pytest.fixture(scope="module")
def speech_video(media_dir, speech_wav):
    path = str(media_dir / "talk.mp4")
    ffmpeg("-f", "lavfi", "-i", "testsrc=size=320x240:rate=15", "-i", speech_wav,
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", path)
    return path


@pytest.fixture(scope="module")
def silent_video(media_dir):
    if not HAS_FFMPEG:
        pytest.skip("FFmpeg not installed")
    path = str(media_dir / "silent.mp4")
    ffmpeg("-f", "lavfi", "-i", "testsrc=duration=3:size=320x240:rate=15", "-c:v", "libx264",
           "-pix_fmt", "yuv420p", path)
    return path


@pytest.fixture(scope="module")
def tone_wav(media_dir):
    if not HAS_FFMPEG:
        pytest.skip("FFmpeg not installed")
    path = str(media_dir / "tone.wav")
    ffmpeg("-f", "lavfi", "-i", "sine=frequency=440:duration=2", path)
    return path


@pytest.fixture(scope="module")
def text_image(media_dir):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (900, 260), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=72)
    draw.text((40, 30), "HELLO WORLD", fill="black", font=font)
    draw.text((40, 140), "MULTIMEDIA 2026", fill="black", font=font)
    path = str(media_dir / "sign.png")
    img.save(path)
    return path


@pytest.fixture(scope="module")
def text_gif(media_dir):
    from PIL import Image, ImageDraw, ImageFont

    frames = []
    for word in ("HELLO", "BRAVE", "NEW", "WORLD"):  # distinct frames (Pillow merges identical ones)
        img = Image.new("RGB", (480, 200), "white")
        ImageDraw.Draw(img).text((40, 50), word, fill="black", font=ImageFont.load_default(size=80))
        frames.append(img)
    path = str(media_dir / "words.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=400, loop=0)
    return path


@pytest.fixture
def fake_ocr(monkeypatch):
    """Stub OCR engine (used only where Tesseract is not installed) to test pipeline wiring."""
    monkeypatch.setitem(availability._CHECKS, "tesseract", lambda: None)
    monkeypatch.setattr(ocr_adapter, "languages", lambda: ["eng"])
    monkeypatch.setattr(ocr_adapter, "ocr", lambda image, language="eng", layout="auto": OcrResult(
        text="HELLO WORLD", word_count=2, mean_confidence=95.0, language=language, layout=layout))
    availability.reset_cache()
    yield
    availability.reset_cache()


@pytest.fixture
def no_ocr(monkeypatch):
    monkeypatch.setitem(availability._CHECKS, "tesseract", lambda: "Tesseract OCR is not installed on this server.")
    availability.reset_cache()
    yield
    availability.reset_cache()


# =====================================================================
# Registry & API integration
# =====================================================================
def test_catalogue_lists_exactly_20_conversions_with_honest_status():
    res = client.get("/api/v1/conversions")
    assert res.status_code == 200
    items = {c["id"]: c for c in res.json()}
    assert len(items) == 20 and set(items) == set(CONVERSION_IDS)
    assert {c["source"] for c in items.values()} == {"text", "image", "audio", "video", "animation"}
    for cid, item in items.items():
        assert item["status"] in ("available", "unavailable"), cid
        for m in item["modes"]:
            assert m["status"] in ("available", "unavailable"), (cid, m["id"])
            if m["status"] == "unavailable":
                assert m["reason"], (cid, m["id"])


def test_catalogue_is_public_even_in_access_key_mode(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "AUTH_MODE", "access_key")
    assert client.get("/api/v1/conversions").status_code == 200


def test_ai_mode_without_provider_is_refused_not_faked():
    img = upload_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, "x.png")
    res = create_job("image_to_text", [img["id"]], mode="describe")
    assert res.status_code == 503 and "not configured" in res.json()["detail"].lower()


def test_unknown_tool_and_bad_mode_rejected():
    assert create_job("teleport").status_code == 400
    img = upload_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, "x.png")
    res = create_job("image_to_text", [img["id"]], mode="nope")
    assert res.status_code == 400 and "unknown mode" in res.json()["detail"].lower()


def test_wrong_input_type_rejected():
    audio = upload_bytes(b"ID3" + b"\x00" * 64, "song.mp3")
    res = create_job("video_to_image", [audio["id"]], timestamp=0)
    assert res.status_code == 400 and "does not accept" in res.json()["detail"]


def test_parameter_validation():
    vid = upload_bytes(b"\x00" * 64, "clip.mp4")
    res = create_job("video_to_image", [vid["id"]], timestamp=-5)
    assert res.status_code == 400 and "at least" in res.json()["detail"]
    res = create_job("text_to_audio", text="hi", voice="robot")
    assert res.status_code == 400 and "voice" in res.json()["detail"].lower()
    res = create_job("text_to_audio", text="x" * 6000)
    assert res.status_code == 400 and "too long" in res.json()["detail"]
    assert create_job("text_to_audio").status_code == 400  # no text, no file


def test_unavailable_engine_returns_503(no_ocr):
    img = upload_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, "x.png")
    res = create_job("image_to_text", [img["id"]], mode="ocr")
    assert res.status_code == 503 and "tesseract" in res.json()["detail"].lower()
    item = next(c for c in client.get("/api/v1/conversions").json() if c["id"] == "image_to_text")
    assert item["status"] == "unavailable"


def test_text_chunking():
    chunks = split_text("Hello there. " * 100, max_chars=120)
    assert all(len(c) <= 120 for c in chunks)
    assert " ".join(chunks).count("Hello there.") == 100
    assert split_text("   ") == []


# =====================================================================
# Text -> Audio (Kokoro)
# =====================================================================
@needs_tts
def test_text_to_audio_mp3(worker):
    job = run_job(worker, "text_to_audio", text=SPEECH, voice="af_heart", speed=1.1, audio_format="mp3")
    assert job["status"] == "succeeded", job["error_message"]
    asset = outputs_by_type(job)["audio_mp3"]
    assert asset["filename"] == "speech.mp3" and asset["media_type"] == "audio/mpeg"
    assert asset["metadata_json"]["voice"] == "af_heart" and asset["metadata_json"]["duration_seconds"] > 1.5
    data = download(asset)
    assert data[:3] == b"ID3" or data[:2] in (b"\xff\xfb", b"\xff\xf3")
    assert job["progress"] == 100 and job["progress_message"] == "Completed"


@needs_tts
def test_text_to_audio_from_uploaded_txt_file(worker):
    txt = upload_bytes("Reading a text file aloud.".encode("utf-8"), "notes.txt")
    job = run_job(worker, "text_to_audio", [txt["id"]], audio_format="wav", voice="bm_george")
    assert job["status"] == "succeeded", job["error_message"]
    asset = outputs_by_type(job)["audio_wav"]
    assert asset["filename"] == "notes.wav"
    assert download(asset)[:4] == b"RIFF"


@needs_tts
def test_text_to_audio_rejects_non_utf8_file(worker):
    txt = upload_bytes(b"\xff\xfe\x00bad", "bad.txt")
    job = run_job(worker, "text_to_audio", [txt["id"]])
    assert job["status"] == "failed" and job["error_code"] == "INVALID_INPUT"
    assert job["outputs"] == []


# =====================================================================
# Audio -> Text and Video -> Text (Whisper)
# =====================================================================
def _assert_transcript(job, *words):
    assert job["status"] == "succeeded", job["error_message"]
    outs = outputs_by_type(job)
    assert set(outs) == {"transcript_txt", "subtitles_srt", "subtitles_vtt", "transcript_json"}
    text = download(outs["transcript_txt"]).decode("utf-8").lower()
    for word in words:
        assert word in text, f"'{word}' not in transcript: {text!r}"
    srt = download(outs["subtitles_srt"]).decode("utf-8")
    assert "-->" in srt and srt.startswith("1\n")
    assert download(outs["subtitles_vtt"]).decode("utf-8").startswith("WEBVTT")
    data = json.loads(download(outs["transcript_json"]))
    assert data["language"] == "en" and data["segments"]
    assert outs["transcript_txt"]["metadata_json"]["preview_text"]


@needs_asr
def test_audio_to_text_transcribes_real_speech(worker, speech_wav):
    audio = upload_file(speech_wav)
    job = run_job(worker, "audio_to_text", [audio["id"]], model="base", language="auto")
    _assert_transcript(job, "fox", "lazy dog")


@needs_asr
def test_audio_to_text_without_speech_fails_honestly(worker, tone_wav):
    audio = upload_file(tone_wav)
    job = run_job(worker, "audio_to_text", [audio["id"]], model="tiny")
    assert job["status"] == "failed" and job["error_code"] == "NO_SPEECH"
    assert job["outputs"] == []


@needs_asr
def test_video_to_text_transcribes_soundtrack(worker, speech_video):
    video = upload_file(speech_video)
    job = run_job(worker, "video_to_text", [video["id"]], model="base", language="en")
    _assert_transcript(job, "fox")


@needs_ffmpeg
def test_video_to_text_without_audio_fails_honestly(worker, silent_video):
    if not HAS_ASR:
        pytest.skip("Whisper model not available locally")
    video = upload_file(silent_video)
    job = run_job(worker, "video_to_text", [video["id"]])
    assert job["status"] == "failed" and job["error_code"] == "NO_AUDIO"


# =====================================================================
# Video -> Image (FFmpeg + Pillow)
# =====================================================================
@needs_ffmpeg
def test_video_to_image_frame_with_edits(worker, silent_video):
    from PIL import Image

    video = upload_file(silent_video)
    job = run_job(worker, "video_to_image", [video["id"]], mode="frame", timestamp=1.5, rotate="90",
                  crop_left=10, crop_right=10, grayscale=True, image_format="jpg")
    assert job["status"] == "succeeded", job["error_message"]
    asset = outputs_by_type(job)["image_jpg"]
    assert asset["media_type"] == "image/jpeg" and "_frame_1.50s" in asset["filename"]
    img = Image.open(io.BytesIO(download(asset)))
    # 320x240 rotated 90° -> 240x320, then 10% cropped from left and right -> 192 wide
    assert img.size == (192, 320)


@needs_ffmpeg
def test_video_to_image_best_frame(worker, silent_video):
    video = upload_file(silent_video)
    job = run_job(worker, "video_to_image", [video["id"]], mode="best_frame", image_format="png")
    assert job["status"] == "succeeded", job["error_message"]
    asset = outputs_by_type(job)["image_png"]
    assert download(asset)[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(asset["metadata_json"]["sharpness_candidates"]) == 12


@needs_ffmpeg
def test_video_to_image_timestamp_beyond_end_fails(worker, silent_video):
    video = upload_file(silent_video)
    job = run_job(worker, "video_to_image", [video["id"]], mode="frame", timestamp=99)
    assert job["status"] == "failed" and "beyond the end" in job["error_message"]


@needs_ffmpeg
def test_video_to_image_corrupt_file_fails_cleanly(worker):
    video = upload_bytes(b"not a video at all", "broken.mp4")
    job = run_job(worker, "video_to_image", [video["id"]], mode="frame", timestamp=0)
    assert job["status"] == "failed" and job["outputs"] == []


# =====================================================================
# Image -> Text and Image -> Audio (Tesseract OCR)
# =====================================================================
@needs_ocr
def test_image_to_text_real_ocr(worker, text_image):
    image = upload_file(text_image)
    job = run_job(worker, "image_to_text", [image["id"]], mode="ocr", ocr_language="eng", layout="auto")
    assert job["status"] == "succeeded", job["error_message"]
    outs = outputs_by_type(job)
    text = download(outs["ocr_txt"]).decode("utf-8").upper()
    assert "HELLO" in text and "WORLD" in text
    assert json.loads(download(outs["ocr_json"]))["word_count"] >= 3


@needs_ocr
def test_image_to_text_blank_image_fails_honestly(worker, media_dir):
    from PIL import Image
    path = str(media_dir / "blank.png")
    Image.new("RGB", (400, 300), "white").save(path)
    job = run_job(worker, "image_to_text", [upload_file(path)["id"]], mode="ocr")
    assert job["status"] == "failed" and job["error_code"] == "NO_TEXT_FOUND"


@needs_ocr
@needs_tts
def test_image_to_audio_real_ocr_and_tts(worker, text_image):
    job = run_job(worker, "image_to_audio", [upload_file(text_image)["id"]], mode="read_aloud", audio_format="mp3")
    assert job["status"] == "succeeded", job["error_message"]
    outs = outputs_by_type(job)
    assert "HELLO" in download(outs["ocr_txt"]).decode("utf-8").upper()
    assert outs["audio_mp3"]["metadata_json"]["pipeline"] == "Tesseract OCR → Kokoro TTS"


def test_image_to_text_pipeline_with_stub_ocr(worker, text_image, fake_ocr):
    job = run_job(worker, "image_to_text", [upload_file(text_image)["id"]], mode="ocr")
    assert job["status"] == "succeeded", job["error_message"]
    assert download(outputs_by_type(job)["ocr_txt"]).decode("utf-8").strip() == "HELLO WORLD"


@needs_tts
def test_image_to_audio_pipeline_with_stub_ocr(worker, text_image, fake_ocr):
    job = run_job(worker, "image_to_audio", [upload_file(text_image)["id"]], mode="read_aloud", audio_format="wav")
    assert job["status"] == "succeeded", job["error_message"]
    outs = outputs_by_type(job)
    assert set(outs) == {"ocr_txt", "audio_wav"}
    assert download(outs["audio_wav"])[:4] == b"RIFF"


def test_image_to_text_corrupt_image_fails(worker, fake_ocr):
    job = run_job(worker, "image_to_text", [upload_bytes(b"\x89PNG broken", "bad.png")["id"]], mode="ocr")
    assert job["status"] == "failed" and job["error_code"] == "INVALID_INPUT"


# =====================================================================
# Animation -> Text and Animation -> Audio
# =====================================================================
@needs_asr
def test_animation_to_text_transcribes_speech_in_clip(worker, speech_video, no_ocr):
    clip = upload_file(speech_video, "clip.mp4")
    job = run_job(worker, "animation_to_text", [clip["id"]], model="base", language="en")
    assert job["status"] == "succeeded", job["error_message"]
    outs = outputs_by_type(job)
    text = download(outs["animation_txt"]).decode("utf-8").lower()
    assert "speech transcript" in text and "fox" in text
    report = json.loads(download(outs["animation_json"]))
    assert any("On-screen text skipped" in n for n in report["notes"])


def test_animation_to_text_reads_gif_text_with_stub_ocr(worker, text_gif, fake_ocr):
    job = run_job(worker, "animation_to_text", [upload_file(text_gif)["id"]])
    assert job["status"] == "succeeded", job["error_message"]
    outs = outputs_by_type(job)
    text = download(outs["animation_txt"]).decode("utf-8")
    assert "ON-SCREEN TEXT" in text and "HELLO WORLD" in text
    report = json.loads(download(outs["animation_json"]))
    assert report["speech"] is None and report["frames_sampled"] == 4
    assert "No audio track" in report["notes"][0]


@needs_ocr
def test_animation_to_text_real_ocr_on_gif(worker, text_gif):
    job = run_job(worker, "animation_to_text", [upload_file(text_gif)["id"]])
    assert job["status"] == "succeeded", job["error_message"]
    text = download(outputs_by_type(job)["animation_txt"]).decode("utf-8").upper()
    assert "HELLO" in text and "WORLD" in text


def test_animation_to_text_with_nothing_to_read_fails_honestly(worker, media_dir, no_ocr):
    from PIL import Image
    frames = [Image.new("RGB", (64, 64), c) for c in ("red", "blue", "green")]
    path = str(media_dir / "colors.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=200, loop=0)
    job = run_job(worker, "animation_to_text", [upload_file(path)["id"]])
    assert job["status"] == "failed" and job["error_code"] == "NO_CONTENT"
    assert "coming soon" in job["error_message"].lower()


def test_animation_to_audio_soundtrack_of_gif_fails_honestly(worker, text_gif):
    job = run_job(worker, "animation_to_audio", [upload_file(text_gif)["id"]], mode="soundtrack")
    assert job["status"] == "failed" and job["error_code"] == "NO_AUDIO"
    assert "read on-screen text aloud" in job["error_message"].lower()


@needs_asr
def test_animation_to_audio_extracts_clip_soundtrack(worker, speech_video):
    clip = upload_file(speech_video, "clip.webm" if False else "clip.mp4")
    job = run_job(worker, "animation_to_audio", [clip["id"]], mode="soundtrack", audio_format="ogg")
    assert job["status"] == "succeeded", job["error_message"]
    asset = outputs_by_type(job)["audio_ogg"]
    assert asset["filename"] == "clip_soundtrack.ogg" and download(asset)[:4] == b"OggS"


@needs_tts
def test_animation_to_audio_reads_text_aloud_with_stub_ocr(worker, text_gif, fake_ocr):
    job = run_job(worker, "animation_to_audio", [upload_file(text_gif)["id"]], mode="read_text", audio_format="mp3")
    assert job["status"] == "succeeded", job["error_message"]
    outs = outputs_by_type(job)
    assert set(outs) == {"ocr_txt", "audio_mp3"}
    assert outs["audio_mp3"]["metadata_json"]["mode"] == "read_text"


def test_failed_job_leaves_no_orphan_outputs(worker, text_gif, fake_ocr, monkeypatch):
    """If a later pipeline step fails, outputs stored by earlier steps are removed."""
    from app.engines.pipelines import animation as animation_module
    from app.services.storage_service import storage_service

    def boom(*args, **kwargs):
        raise RuntimeError("TTS crashed")

    monkeypatch.setattr(animation_module, "speak_text", boom)
    before = set(os.listdir(storage_service.base_dir))
    job = run_job(worker, "animation_to_audio", [upload_file(text_gif)["id"]], mode="read_text")
    assert job["status"] == "failed" and job["outputs"] == []
    after = set(os.listdir(storage_service.base_dir))
    assert len(after - before) == 1  # only the uploaded GIF itself
