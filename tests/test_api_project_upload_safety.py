from io import BytesIO

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

import app.api.project_processor as api_module


def _prepare_project(monkeypatch):
    monkeypatch.setattr(
        api_module.project_manager,
        "get_project",
        lambda name: {"project_name": name},
    )
    monkeypatch.setattr(
        api_module.project_processor,
        "process",
        lambda name: {
            "project": name,
            "status": "READY",
        },
    )


def test_project_upload_does_not_overwrite_existing_file(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)
    _prepare_project(monkeypatch)

    project_name = "TEST_PROJECT"
    input_path = tmp_path / "projects" / project_name / "input"
    input_path.mkdir(parents=True)

    existing_file = input_path / "drawing.pdf"
    existing_file.write_bytes(b"ORIGINAL")

    upload = UploadFile(
        filename="drawing.pdf",
        file=BytesIO(b"NEW DATA"),
    )

    with pytest.raises(HTTPException) as error:
        api_module.upload_project_file(
            project_name,
            upload,
        )

    assert error.value.status_code == 409
    assert existing_file.read_bytes() == b"ORIGINAL"
    assert upload.file.closed is True


def test_project_upload_rejects_oversized_file_and_removes_partial(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)
    _prepare_project(monkeypatch)

    monkeypatch.setattr(
        api_module,
        "PROJECT_UPLOAD_MAX_FILE_SIZE_BYTES",
        8,
        raising=False,
    )

    project_name = "TEST_PROJECT"

    upload = UploadFile(
        filename="drawing.pdf",
        file=BytesIO(b"123456789"),
    )

    with pytest.raises(HTTPException) as error:
        api_module.upload_project_file(
            project_name,
            upload,
        )

    saved_file = (
        tmp_path
        / "projects"
        / project_name
        / "input"
        / "drawing.pdf"
    )

    assert error.value.status_code == 413
    assert not saved_file.exists()
    assert upload.file.closed is True


def test_project_upload_rejects_empty_file(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)
    _prepare_project(monkeypatch)

    project_name = "TEST_PROJECT"

    upload = UploadFile(
        filename="drawing.pdf",
        file=BytesIO(b""),
    )

    with pytest.raises(HTTPException) as error:
        api_module.upload_project_file(
            project_name,
            upload,
        )

    saved_file = (
        tmp_path
        / "projects"
        / project_name
        / "input"
        / "drawing.pdf"
    )

    assert error.value.status_code == 400
    assert not saved_file.exists()
    assert upload.file.closed is True


class FailingStream(BytesIO):
    def __init__(self):
        super().__init__(b"PARTIAL")
        self.read_calls = 0

    def read(self, size=-1):
        self.read_calls += 1

        if self.read_calls == 1:
            return super().read(4)

        raise OSError("copy failure")


def test_project_upload_removes_partial_file_on_copy_failure(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)
    _prepare_project(monkeypatch)

    project_name = "TEST_PROJECT"

    upload = UploadFile(
        filename="drawing.pdf",
        file=FailingStream(),
    )

    with pytest.raises(HTTPException) as error:
        api_module.upload_project_file(
            project_name,
            upload,
        )

    saved_file = (
        tmp_path
        / "projects"
        / project_name
        / "input"
        / "drawing.pdf"
    )

    assert error.value.status_code == 500
    assert not saved_file.exists()
    assert upload.file.closed is True
