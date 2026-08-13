from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

import app.api.project_processor as api_module


def test_project_api_executive_document_success_and_missing(
    monkeypatch,
    tmp_path,
):

    project_name = "TEST_PROJECT"

    executive_file = tmp_path / "executive.docx"
    executive_file.write_bytes(b"DOCX")

    monkeypatch.setattr(
        api_module.project_executive_generator,
        "create",
        lambda name: str(executive_file),
    )

    response = api_module.download_executive_document(
        project_name
    )

    assert isinstance(response, FileResponse)
    assert Path(response.path).resolve() == executive_file.resolve()

    missing_file = tmp_path / "missing.docx"

    monkeypatch.setattr(
        api_module.project_executive_generator,
        "create",
        lambda name: str(missing_file),
    )

    with pytest.raises(HTTPException) as error:
        api_module.download_executive_document(
            project_name
        )

    assert error.value.status_code == 404
