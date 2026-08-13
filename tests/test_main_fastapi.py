from fastapi.testclient import TestClient

from main import app


def test_main_fastapi_app_and_routes():

    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["program"] == "ID-Agent"
    assert data["version"] == "0.5.7"

    response = client.get("/agent")

    assert response.status_code == 200

    agent_data = response.json()

    assert agent_data["agent"] == "ID-Agent"

    paths = set(app.openapi()["paths"].keys())

    assert "/upload" in paths
    assert "/generate" in paths
    assert "/projects" in paths
    assert "/projects/{project_name}/upload" in paths
    assert "/projects/{project_name}/process" in paths
    assert "/projects/{project_name}/card" in paths
    assert "/projects/{project_name}/package" in paths

