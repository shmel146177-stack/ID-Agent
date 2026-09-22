import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.datastructures import UploadFile

import app.api.documents as documents
import app.api.project_processor as projects
from app.services.safe_paths import safe_project_path
from main import app


@pytest.mark.parametrize("name", [
    "../escaped-project", "..\\escaped-project", "/absolute", "C:\\escape",
    "C:escape", "a/b", "a\\b", ".", "..", "", "CON", "nul.pdf",
    "COM1", "LPT9.txt", "name.", "name ", "a:b", "a?b", "a\x00b",
])
def test_project_names_cannot_escape(tmp_path, monkeypatch, name):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError):
        safe_project_path(name)
    response = TestClient(app).post("/projects", json={"project_name": name})
    assert response.status_code == 400
    assert not (tmp_path / "escaped-project").exists()


def test_card_update_preserves_unspecified_fields(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    assert client.post("/projects", json={"project_name": "Объект-1"}).status_code == 200
    url = "/projects/Объект-1/card"
    client.put(url, json={"customer": "Заказчик", "contractor": "Подрядчик"})
    response = client.put(url, json={"project_note": "Примечание"})
    assert response.status_code == 200
    assert response.json()["customer"] == "Заказчик"
    assert response.json()["contractor"] == "Подрядчик"
    assert client.put(url, json={"customer": ""}).json()["customer"] == ""
    assert client.get(url).json()["contractor"] == "Подрядчик"


class BrokenStream(BytesIO):
    def read(self, size=-1):
        if self.tell():
            raise OSError("copy failure")
        return super().read(2)


@pytest.mark.parametrize("route", ["general", "project"])
@pytest.mark.parametrize("case,status", [
    ("duplicate", 409), ("empty", 400), ("oversized", 413),
    ("broken", 500), ("reserved", 400), ("ads", 400),
])
def test_both_uploaders_enforce_safe_storage(tmp_path, monkeypatch, route, case, status):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(projects.project_processor, "process", lambda name: {})
    monkeypatch.setattr(documents.document_service, "analyze", lambda path: {"extension": ".docx"})
    monkeypatch.setattr(documents, "UPLOAD_MAX_FILE_SIZE_BYTES", 4)
    monkeypatch.setattr(projects, "PROJECT_UPLOAD_MAX_FILE_SIZE_BYTES", 4)
    projects.project_manager.create_project("test")
    directory = tmp_path / ("uploads" if route == "general" else "projects/test/input")
    directory.mkdir(parents=True, exist_ok=True)
    filename = {"reserved": "CON.docx", "ads": "a:stream.docx"}.get(case, "file.docx")
    target = directory / filename
    if case == "duplicate":
        target.write_bytes(b"original")
    stream = BrokenStream(b"1234") if case == "broken" else BytesIO(
        b"" if case == "empty" else b"12345" if case == "oversized" else b"1234"
    )
    upload = UploadFile(filename=filename, file=stream)
    with pytest.raises(HTTPException) as error:
        if route == "general":
            asyncio.run(documents.upload_document(upload))
        else:
            projects.upload_project_file("test", upload)
    assert error.value.status_code == status
    assert stream.closed
    if case == "duplicate":
        assert target.read_bytes() == b"original"
    else:
        assert list(directory.iterdir()) == []


def test_project_symlink_escape(tmp_path):
    root = tmp_path / "projects"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (root / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks unavailable")
    with pytest.raises(ValueError):
        safe_project_path("linked", root)


@pytest.mark.parametrize("name", ["CON", "C:escape", "..%5Cescape"])
def test_project_routes_reject_invalid_names(tmp_path, monkeypatch, name):
    monkeypatch.chdir(tmp_path)
    assert TestClient(app).get(f"/projects/{name}/card").status_code == 400


@pytest.mark.parametrize("route", ["general", "project"])
def test_upload_at_limit_and_duplicate_api(tmp_path, monkeypatch, route):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(projects.project_processor, "process", lambda name: {})
    monkeypatch.setattr(documents.document_service, "analyze", lambda path: {"extension": ".docx"})
    monkeypatch.setattr(documents, "UPLOAD_MAX_FILE_SIZE_BYTES", 4)
    monkeypatch.setattr(projects, "PROJECT_UPLOAD_MAX_FILE_SIZE_BYTES", 4)
    projects.project_manager.create_project("test")
    url = "/upload" if route == "general" else "/projects/test/upload"
    client = TestClient(app)
    assert client.post(url, files={"file": ("a.docx", b"1234")}).status_code == 200
    assert client.post(url, files={"file": ("a.docx", b"5678")}).status_code == 409
    directory = "uploads" if route == "general" else "projects/test/input"
    assert (tmp_path / directory / "a.docx").read_bytes() == b"1234"
