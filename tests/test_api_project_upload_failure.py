from io import BytesIO

from starlette.datastructures import UploadFile

import app.api.project_processor as api_module


def test_project_api_upload_keeps_file_when_processing_fails(
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

    def fail_processing(name):
        raise RuntimeError("Ошибка тестовой обработки")

    monkeypatch.setattr(
        api_module.project_processor,
        "process",
        fail_processing,
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

    automatic = result["automatic_processing"]

    assert automatic["result"] is None
    assert automatic["error"] == "Ошибка тестовой обработки"
    assert automatic["status"]
