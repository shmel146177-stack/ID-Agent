from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

import app.api.project_processor as api_module


def test_project_api_hidden_works_journal_success_and_missing(
    monkeypatch,
    tmp_path,
):

    project_name = "TEST_PROJECT"

    journal_file = tmp_path / "journal.docx"
    journal_file.write_bytes(b"DOCX")

    monkeypatch.setattr(
        api_module.hidden_works_journal_generator,
        "create",
        lambda name: str(journal_file),
    )

    response = api_module.download_hidden_works_journal(
        project_name
    )

    assert isinstance(response, FileResponse)
    assert Path(response.path) == journal_file

    missing_file = tmp_path / "missing.docx"

    monkeypatch.setattr(
        api_module.hidden_works_journal_generator,
        "create",
        lambda name: str(missing_file),
    )

    with pytest.raises(HTTPException) as error:
        api_module.download_hidden_works_journal(
            project_name
        )

    assert error.value.status_code == 404
