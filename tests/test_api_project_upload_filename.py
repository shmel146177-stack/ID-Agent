from io import BytesIO

from starlette.datastructures import UploadFile

import app.api.project_processor as api_module


def test_project_api_upload_sanitizes_filename_path(
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

    monkeypatch.setattr(
        api_module.project_processor,
        "process",
        lambda name: {
            "project": name,
            "status": "Готово",
        },
    )

    upload = UploadFile(
        filename=r"..\..\evil.pdf",
        file=BytesIO(b"SAFE PDF"),
    )

    result = api_module.upload_project_file(
        project_name,
        upload,
    )

    expected_file = (
        tmp_path
        / "projects"
        / project_name
        / "input"
        / "evil.pdf"
    )

    assert expected_file.exists()
    assert expected_file.read_bytes() == b"SAFE PDF"

    assert result["filename"] == "evil.pdf"
    assert ".." not in result["saved_to"]
