import os
import io
import json
import subprocess
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.job_runner_service import job_runner_service
from app.adapters.ffmpeg_adapter import ffmpeg_adapter
from app.adapters.storyboard_adapter import storyboard_adapter

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["health"] == "/health"


def test_project_lifecycle():
    # 1. Create project
    create_res = client.post("/api/v1/projects", json={
        "title": "Arctic Expedition Documentary",
        "description": "High-definition glacial exploration footage catalog"
    })
    assert create_res.status_code == 200
    proj = create_res.json()
    assert proj["title"] == "Arctic Expedition Documentary"
    project_id = proj["id"]

    # 2. List projects
    list_res = client.get("/api/v1/projects")
    assert list_res.status_code == 200
    assert any(p["id"] == project_id for p in list_res.json())

    # 3. Get single project
    get_res = client.get(f"/api/v1/projects/{project_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == project_id

    # 4. Get non-existent project returns 404
    missing_res = client.get("/api/v1/projects/non-existent-uuid-1234")
    assert missing_res.status_code == 404

    # 5. List assets for project
    assets_res = client.get(f"/api/v1/projects/{project_id}/assets")
    assert assets_res.status_code == 200
    assert isinstance(assets_res.json(), list)


def test_media_upload_validation_valid():
    # Valid mp4 upload
    fake_video_content = b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41"
    response = client.post(
        "/api/v1/media",
        files={"file": ("sample_clip.mp4", io.BytesIO(fake_video_content), "video/mp4")}
    )
    assert response.status_code == 200
    asset = response.json()
    assert asset["filename"] == "sample_clip.mp4"
    assert asset["media_type"] == "video/mp4"
    assert asset["size"] == len(fake_video_content)
    assert asset["checksum"] is not None


def test_media_upload_validation_empty_file_rejected():
    # Empty 0-byte file must be rejected with 400
    response = client.post(
        "/api/v1/media",
        files={"file": ("empty_file.mp4", io.BytesIO(b""), "video/mp4")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_media_upload_validation_invalid_extension_rejected():
    # Dangerous or unsupported extension rejected with 400
    response = client.post(
        "/api/v1/media",
        files={"file": ("malicious_payload.exe", io.BytesIO(b"MZ\x90\x00"), "application/x-msdownload")}
    )
    assert response.status_code == 400
    assert "not supported" in response.json()["detail"].lower()


def test_download_asset_not_found():
    # Non-existent asset ID returns 404
    res = client.get("/api/v1/assets/missing-asset-id-9999/download")
    assert res.status_code == 404


def test_storyboard_validation_empty_concept():
    # Empty concept in job submission rejected with 400
    job_res = client.post("/api/v1/jobs", json={
        "tool": "idea_to_storyboard",
        "params_json": {"concept": "   "}
    })
    assert job_res.status_code == 400
    assert "empty" in job_res.json()["detail"].lower()


def test_storyboard_validation_too_brief():
    # Vague or 1-word concept rejected with 400
    job_res = client.post("/api/v1/jobs", json={
        "tool": "idea_to_storyboard",
        "params_json": {"concept": "robot car"}
    })
    assert job_res.status_code == 400
    assert "brief" in job_res.json()["detail"].lower()


def test_storyboard_duration_arithmetic_exact():
    # Verify that scene durations sum exactly to target duration for diverse target durations
    for target_dur in [25, 45, 50, 60, 95, 120, 180]:
        res = storyboard_adapter.generate_storyboard(
            concept="Autonomous rover exploring volcanic hydrothermal vents on ocean floor",
            style="Cinematic Sci-Fi",
            target_duration_sec=target_dur
        )
        total_sum = sum(scene["duration_seconds"] for scene in res["scenes"])
        assert total_sum == target_dur, f"Sum {total_sum} does not equal target {target_dur}"
        assert res["actual_total_duration"] == target_dur
        assert len(res["scenes"]) >= 3


def test_storyboard_different_concepts_distinct_outputs():
    # Concept 1: Sci-Fi
    sb1 = storyboard_adapter.generate_storyboard(
        concept="Deep space exploration vessel discovering crystal asteroid rings around Saturn",
        style="Cinematic Sci-Fi",
        target_duration_sec=60
    )
    # Concept 2: Nature Documentary
    sb2 = storyboard_adapter.generate_storyboard(
        concept="Peregrine falcon family hunting across alpine crags in high altitude mountains",
        style="Documentary Realism",
        target_duration_sec=60
    )
    # Concept 3: Commercial Technology
    sb3 = storyboard_adapter.generate_storyboard(
        concept="Next-generation wearable health biometric sensor tracking cardiovascular performance",
        style="Commercial 3D",
        target_duration_sec=60
    )

    # Validate distinct themes detected
    assert sb1["detected_theme"] == "sci-fi"
    assert sb2["detected_theme"] == "nature"
    assert sb3["detected_theme"] == "commercial"

    # Validate that scenes are not identical copies
    assert sb1["scenes"][0]["visual_action"] != sb2["scenes"][0]["visual_action"]
    assert sb1["scenes"][0]["audio_cue"] != sb2["scenes"][0]["audio_cue"]
    assert sb2["scenes"][0]["composition"] != sb3["scenes"][0]["composition"]

    # Validate each scene has all required directorial dimensions
    for sb in [sb1, sb2, sb3]:
        for scene in sb["scenes"]:
            assert len(scene["narrative_purpose"]) > 10
            assert len(scene["visual_action"]) > 10
            assert len(scene["composition"]) > 10
            assert len(scene["audio_cue"]) > 10
            assert len(scene["voiceover_script"]) > 10
            assert scene["duration_seconds"] > 0


def test_storyboard_end_to_end_job_and_download():
    # Submit Idea-to-Storyboard job
    job_res = client.post("/api/v1/jobs", json={
        "tool": "idea_to_storyboard",
        "params_json": {
            "concept": "Submersible research submarine navigating bioluminescent trench abyss",
            "style": "Cinematic Sci-Fi",
            "duration": 45
        }
    })
    assert job_res.status_code == 200
    job_id = job_res.json()["id"]

    # Process job synchronously
    job_runner_service.process_job(job_id)

    # Inspect job status
    poll_res = client.get(f"/api/v1/jobs/{job_id}")
    assert poll_res.status_code == 200
    updated_job = poll_res.json()
    assert updated_job["status"] == "succeeded"
    assert updated_job["progress"] == 100
    assert len(updated_job["outputs"]) > 0

    output_asset_id = updated_job["outputs"][0]["asset_id"]

    # Verify download of generated storyboard JSON
    download_res = client.get(f"/api/v1/assets/{output_asset_id}/download")
    assert download_res.status_code == 200
    content = download_res.json()
    assert content["target_duration_seconds"] == 45
    assert len(content["scenes"]) >= 3
    assert content["model_engine"].startswith("MultimediaToolKit")


def test_media_extractor_end_to_end():
    # Test end-to-end media extraction with real FFmpeg
    ffmpeg_bin = ffmpeg_adapter.get_ffmpeg_cmd()
    if not ffmpeg_bin or not ffmpeg_adapter.is_available():
        pytest.skip("FFmpeg executable not available on this host environment.")

    # Generate a real mini test MP4 video containing video and audio streams
    test_video_path = "test_mini_video.mp4"
    gen_cmd = [
        ffmpeg_bin,
        "-y",
        "-f", "lavfi", "-i", "testsrc=duration=1:size=160x120:rate=10",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        test_video_path
    ]
    gen_res = subprocess.run(gen_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert gen_res.returncode == 0, f"FFmpeg failed to generate test video: {gen_res.stderr}"

    try:
        # 1. Upload the real test video
        with open(test_video_path, "rb") as f:
            upload_res = client.post(
                "/api/v1/media",
                files={"file": ("test_mini_video.mp4", f, "video/mp4")}
            )
        assert upload_res.status_code == 200
        video_asset = upload_res.json()
        assert video_asset["id"] is not None

        # 2. Submit extraction job
        job_res = client.post("/api/v1/jobs", json={
            "tool": "video_to_audio",
            "input_asset_ids": [video_asset["id"]],
            "params_json": {"audio_format": "mp3"}
        })
        assert job_res.status_code == 200
        job_id = job_res.json()["id"]

        # 3. Execute extraction job
        processed = job_runner_service.process_job(job_id)
        assert processed.status == "succeeded"
        assert processed.progress == 100

        # 4. Query job from API
        query_res = client.get(f"/api/v1/jobs/{job_id}")
        assert query_res.status_code == 200
        job_data = query_res.json()
        assert job_data["status"] == "succeeded"
        assert len(job_data["outputs"]) == 1
        output_output = job_data["outputs"][0]
        assert output_output["output_type"] == "audio_mp3"

        audio_asset_id = output_output["asset_id"]

        # 5. Download extracted audio and verify it is a real non-empty MP3
        download_res = client.get(f"/api/v1/assets/{audio_asset_id}/download")
        assert download_res.status_code == 200
        audio_bytes = download_res.content
        assert len(audio_bytes) > 500  # Real MP3 file is significantly larger than dummy header
        assert audio_bytes[:3] == b"ID3" or b"\xff\xfb" in audio_bytes[:10]  # Valid MP3 / ID3 frame header

    finally:
        if os.path.exists(test_video_path):
            os.remove(test_video_path)


def test_media_extractor_missing_asset_fails_honestly():
    # Submitting extraction for a non-existent asset ID must fail with 404
    job_res = client.post("/api/v1/jobs", json={
        "tool": "video_to_audio",
        "input_asset_ids": ["non-existent-asset-uuid"],
        "params_json": {"audio_format": "mp3"}
    })
    assert job_res.status_code == 404
    assert "not found" in job_res.json()["detail"].lower()


def test_media_extractor_malformed_file_fails_cleanly():
    # Upload an invalid / corrupt video file with .mp4 extension
    fake_corrupted = b"NOT_A_REAL_VIDEO_CORRUPT_BYTES_DATA"
    upload_res = client.post(
        "/api/v1/media",
        files={"file": ("corrupt_media.mp4", io.BytesIO(fake_corrupted), "video/mp4")}
    )
    assert upload_res.status_code == 200
    asset_id = upload_res.json()["id"]

    # Submit extraction job
    job_res = client.post("/api/v1/jobs", json={
        "tool": "video_to_audio",
        "input_asset_ids": [asset_id],
        "params_json": {"audio_format": "mp3"}
    })
    assert job_res.status_code == 200
    job_id = job_res.json()["id"]

    # Inspect job result: must fail honestly without reporting false success
    query_res = client.get(f"/api/v1/jobs/{job_id}")
    assert query_res.status_code == 200
    job_data = query_res.json()
    assert job_data["status"] == "failed"
    assert job_data["error_code"] == "PROCESSING_ERROR"
    assert len(job_data["error_message"]) > 0
