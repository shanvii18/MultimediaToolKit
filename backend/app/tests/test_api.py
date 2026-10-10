import pytest
from fastapi.testclient import TestClient
from app.main import app

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


def test_project_lifecycle():
    # Create project
    create_res = client.post("/api/v1/projects", json={
        "title": "Test Documentary Project",
        "description": "A demo project testing backend architecture"
    })
    assert create_res.status_code == 200
    proj = create_res.json()
    assert proj["title"] == "Test Documentary Project"
    project_id = proj["id"]

    # List projects
    list_res = client.get("/api/v1/projects")
    assert list_res.status_code == 200
    assert any(p["id"] == project_id for p in list_res.json())

    # Get single project
    get_res = client.get(f"/api/v1/projects/{project_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == project_id


def test_storyboard_job_workflow():
    # Submit Idea-to-Storyboard job
    job_res = client.post("/api/v1/jobs", json={
        "tool": "idea_to_storyboard",
        "params_json": {
            "concept": "Deep sea exploration vehicle discovering underwater crystalline cavern",
            "style": "Cinematic Sci-Fi",
            "duration": 45
        }
    })
    assert job_res.status_code == 200
    job_data = job_res.json()
    assert job_data["tool"] == "idea_to_storyboard"
    job_id = job_data["id"]

    # Inspect job status
    poll_res = client.get(f"/api/v1/jobs/{job_id}")
    assert poll_res.status_code == 200
    updated_job = poll_res.json()
    assert updated_job["status"] in ["queued", "running", "succeeded"]
