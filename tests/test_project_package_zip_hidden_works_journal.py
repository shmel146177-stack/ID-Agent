import zipfile
from pathlib import Path

from app.services.project_package import ProjectPackage


def test_project_package_zip_includes_hidden_works_journal(
    monkeypatch,
    tmp_path,
):

    package = ProjectPackage()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    package_folder = project_path / "executive_docs"

    journal_folder = (
        package_folder
        / "Исполнительная_документация"
        / "07_Журналы_работ"
    )

    journal_folder.mkdir(
        parents=True,
    )

    journal_file = (
        journal_folder
        / "Журнал_скрытых_работ_TEST_PROJECT.docx"
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

    result = package.create_zip(
        project_name
    )

    zip_path = Path(result)

    assert zip_path.is_file()

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:

        names = set(
            archive.namelist()
        )

        journal_path = (
            "Исполнительная_документация/"
            "07_Журналы_работ/"
            "Журнал_скрытых_работ_TEST_PROJECT.docx"
        )

        assert journal_path in names

        assert archive.read(
            journal_path
        ) == b"HIDDEN WORKS JOURNAL"
