from io import BytesIO

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

import app.api.project_processor as api_module


def test_project_api_upload_returns_404_for_missing_project(
    monkeypatch,
):

    project_name = "MISSING_PROJECT"

    def raise_not_found(name):
        raise FileNotFoundError(
            f"Проект не найден: {name}"
        )

    monkeypatch.setattr(
        api_module.project_manager,
        "get_project",
        raise_not_found,
    )

    upload = UploadFile(
        filename="drawing.pdf",
        file=BytesIO(b"TEST PDF"),
    )

    with pytest.raises(HTTPException) as error:
        api_module.upload_project_file(
            project_name,
            upload,
        )

    assert error.value.status_code == 404
    assert project_name in error.value.detail

    assert upload.file.closed is True
