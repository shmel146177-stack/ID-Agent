from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

import app.api.project_processor as api_module


def test_project_api_registry_download_success_and_missing(
    monkeypatch,
    tmp_path,
):

    monkeypatch.chdir(tmp_path)

    project_name = "TEST_PROJECT"

    output_dir = (
        tmp_path
        / "projects"
        / project_name
        / "output"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    expected_file = output_dir / (
        f"Реестр_документов_{project_name}.xlsx"
    )

    expected_file.write_bytes(b"XLSX")

    response = api_module.download_registry(
        project_name
    )

    assert isinstance(response, FileResponse)
    assert Path(response.path).resolve() == expected_file.resolve()

    expected_file.unlink()

    with pytest.raises(HTTPException) as error:
        api_module.download_registry(
            project_name
        )

    assert error.value.status_code == 404

