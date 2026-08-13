import zipfile
from pathlib import Path

from fastapi.responses import FileResponse

import app.api.project_processor as api_module


def test_project_api_package_creates_real_zip_with_hidden_works_documents(
    monkeypatch,
    tmp_path,
):

    project_name = "TEST_PROJECT"

    package = api_module.project_package

    project_path = tmp_path / project_name
    package_folder = project_path / "executive_docs"

    act_folder = (
        package_folder
        / "Исполнительная_документация"
        / "03_Акты_скрытых_работ"
    )

    journal_folder = (
        package_folder
        / "Исполнительная_документация"
        / "07_Журналы_работ"
    )

    act_folder.mkdir(
        parents=True,
    )

    journal_folder.mkdir(
        parents=True,
    )

    act_file = (
        act_folder
        / "АОСР_Заземление_TEST_PROJECT.docx"
    )

    journal_file = (
        journal_folder
        / "Журнал_скрытых_работ_TEST_PROJECT.docx"
    )

    act_file.write_bytes(
        b"HIDDEN WORKS ACT"
    )

    journal_file.write_bytes(
        b"HIDDEN WORKS JOURNAL"
    )

    monkeypatch.setattr(
        package,
        "create",
        lambda name: {
            "project": name,
            "package_folder": str(package_folder),
        },
    )

    monkeypatch.setattr(
        package,
        "_project_path",
        lambda name: project_path,
    )

    response = api_module.download_project_package(
        project_name
    )

    assert isinstance(
        response,
        FileResponse,
    )

    assert response.media_type == "application/zip"

    zip_path = Path(
        response.path
    )

    assert zip_path.is_file()

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:

        names = set(
            archive.namelist()
        )

        act_path = (
            "Исполнительная_документация/"
            "03_Акты_скрытых_работ/"
            "АОСР_Заземление_TEST_PROJECT.docx"
        )

        journal_path = (
            "Исполнительная_документация/"
            "07_Журналы_работ/"
            "Журнал_скрытых_работ_TEST_PROJECT.docx"
        )

        assert act_path in names
        assert journal_path in names

        assert archive.read(
            act_path
        ) == b"HIDDEN WORKS ACT"

        assert archive.read(
            journal_path
        ) == b"HIDDEN WORKS JOURNAL"
