from io import BytesIO

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

import app.api.project_processor as api_module


def test_project_api_upload_rejects_unsupported_extension(
    monkeypatch,
):

    project_name = "TEST_PROJECT"

    monkeypatch.setattr(
        api_module.project_manager,
        "get_project",
        lambda name: {
            "project_name": name,
        },
    )

    upload = UploadFile(
        filename="dangerous.exe",
        file=BytesIO(b"TEST"),
    )

    with pytest.raises(HTTPException) as error:
        api_module.upload_project_file(
            project_name,
            upload,
        )

    assert error.value.status_code == 400
    assert ".exe" in error.value.detail
