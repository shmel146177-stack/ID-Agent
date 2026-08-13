from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

import app.api.project_processor as api_module


def test_project_api_package_download_success_and_missing(
    monkeypatch,
    tmp_path,
):

    project_name = "TEST_PROJECT"

    package_file = tmp_path / "package.zip"
    package_file.write_bytes(b"ZIP")

    monkeypatch.setattr(
        api_module.project_package,
        "create_zip",
        lambda name: str(package_file),
    )

    response = api_module.download_project_package(
        project_name
    )

    assert isinstance(response, FileResponse)
    assert Path(response.path).resolve() == package_file.resolve()
    assert response.media_type == "application/zip"

    missing_file = tmp_path / "missing.zip"

    monkeypatch.setattr(
        api_module.project_package,
        "create_zip",
        lambda name: str(missing_file),
    )

    with pytest.raises(HTTPException) as error:
        api_module.download_project_package(
            project_name
        )

    assert error.value.status_code == 404
