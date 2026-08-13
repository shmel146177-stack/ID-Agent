from io import BytesIO

from starlette.datastructures import UploadFile

import app.api.project_processor as api_module


def test_project_api_upload_saves_file_and_processes_project(
    monkeypatch,
    tmp_path,
):

    monkeypatch.chdir(tmp_path)

    project_name = "TEST_PROJECT"

    monkeypatch.setattr(
        api_module.project_manager,
        "get_project",
        lambda name: {
            "project_name": name,
        },
    )

    processing_result = {
        "project": project_name,
        "status": "Готово",
    }

    monkeypatch.setattr(
        api_module.project_processor,
        "process",
        lambda name: processing_result,
    )

    upload = UploadFile(
        filename="drawing.pdf",
        file=BytesIO(b"TEST PDF DATA"),
    )

    result = api_module.upload_project_file(
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

    assert saved_file.exists()
    assert saved_file.read_bytes() == b"TEST PDF DATA"

    assert result["project"] == project_name
    assert result["filename"] == "drawing.pdf"
    assert result["extension"] == ".pdf"
    assert result["size_bytes"] == len(b"TEST PDF DATA")

    automatic = result["automatic_processing"]

    assert automatic["error"] is None
    assert automatic["result"] == processing_result
