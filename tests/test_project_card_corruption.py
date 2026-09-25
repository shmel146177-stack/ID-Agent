import builtins
import logging

import pytest
from fastapi.testclient import TestClient

from app.services.project_manager import ProjectManager, project_manager
from app.services.project_service import ProjectStateCorruptionError
from main import app

CORRUPTED_CARDS = [
    pytest.param(b'{"customer": "private value",', id="truncated-json"),
    pytest.param(b"", id="empty-file"),
    pytest.param(b"\xff\xfe", id="invalid-utf8"),
    pytest.param(b"[]", id="array"),
    pytest.param(b"null", id="null"),
    pytest.param(b'"text"', id="string"),
    pytest.param(b"42", id="number"),
    pytest.param(b"true", id="boolean"),
]


@pytest.mark.parametrize("payload", CORRUPTED_CARDS)
def test_list_keeps_healthy_projects_and_reports_bad_card(tmp_path, caplog, payload):
    manager = ProjectManager()
    manager.projects_root = str(tmp_path)
    manager.create_project("A_GOOD")
    manager.create_project("Z_GOOD")
    bad_folder = tmp_path / "BAD"
    bad_folder.mkdir()
    bad_card = bad_folder / "project.json"
    bad_card.write_bytes(payload)

    with caplog.at_level(logging.WARNING, logger="app.services.project_manager"):
        projects = manager.list_projects()

    assert [project["project_name"] for project in projects] == ["A_GOOD", "Z_GOOD"]
    assert "Skipping unreadable project card 'BAD'" in caplog.text
    assert "private value" not in caplog.text
    assert bad_card.read_bytes() == payload
    with pytest.raises(ProjectStateCorruptionError, match="project card: BAD"):
        manager.get_project("BAD")


@pytest.mark.parametrize("payload", CORRUPTED_CARDS)
@pytest.mark.parametrize("operation", ["get", "update", "create"])
def test_card_api_reports_conflict_without_overwriting(
    tmp_path, monkeypatch, payload, operation
):
    monkeypatch.setattr(project_manager, "projects_root", str(tmp_path))
    bad_folder = tmp_path / "BAD"
    bad_folder.mkdir()
    bad_card = bad_folder / "project.json"
    bad_card.write_bytes(payload)
    project_manager.create_project("GOOD")
    client = TestClient(app)

    listing = client.get("/projects")
    assert listing.status_code == 200
    assert listing.json()["projects_count"] == 1
    assert listing.json()["projects"][0]["project_name"] == "GOOD"

    if operation == "get":
        response = client.get("/projects/BAD/card")
    elif operation == "update":
        response = client.put("/projects/BAD/card", json={"customer": "New customer"})
    else:
        response = client.post("/projects", json={"project_name": "BAD"})

    assert response.status_code == 409
    assert "project card: BAD" in response.json()["detail"]
    assert "private value" not in response.json()["detail"]
    assert bad_card.read_bytes() == payload
    assert not list(bad_folder.glob("*.tmp"))


def test_legacy_card_keeps_missing_and_unknown_fields(tmp_path):
    manager = ProjectManager()
    manager.projects_root = str(tmp_path)
    folder = tmp_path / "LEGACY"
    folder.mkdir()
    (folder / "project.json").write_text(
        '{"customer": null, "custom": {"keep": true}}', encoding="utf-8"
    )
    project = manager.get_project("LEGACY")
    assert project == {"customer": None, "custom": {"keep": True}}
    assert manager.list_projects()[0]["project_name"] == "LEGACY"
    manager.update_project("LEGACY", {"address": "New address"})
    assert manager.get_project("LEGACY")["custom"] == {"keep": True}


def test_list_skips_unreadable_card_with_warning(tmp_path, monkeypatch, caplog):
    manager = ProjectManager()
    manager.projects_root = str(tmp_path)
    manager.create_project("GOOD")
    manager.create_project("DENIED")
    bad_card = tmp_path / "DENIED" / "project.json"
    saved = bad_card.read_bytes()
    real_open = builtins.open

    def deny_card(path, *args, **kwargs):
        if str(path) == str(bad_card):
            raise PermissionError("Access denied")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", deny_card)
    with caplog.at_level(logging.WARNING, logger="app.services.project_manager"):
        projects = manager.list_projects()

    assert [project["project_name"] for project in projects] == ["GOOD"]
    assert "DENIED" in caplog.text
    assert "Access denied" in caplog.text
    assert bad_card.read_bytes() == saved
