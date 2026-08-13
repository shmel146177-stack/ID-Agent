import zipfile
from pathlib import Path

from app.services.project_package import ProjectPackage


def test_project_package_zip_includes_hidden_works_act(
    monkeypatch,
    tmp_path,
):

    package = ProjectPackage()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    package_folder = project_path / "executive_docs"

    acts_folder = (
        package_folder
        / "Исполнительная_документация"
        / "03_Акты_скрытых_работ"
    )

    acts_folder.mkdir(
        parents=True,
    )

    act_file = (
        acts_folder
        / "АОСР_Заземление_TEST_PROJECT.docx"
    )

    act_file.write_bytes(
        b"HIDDEN WORKS ACT"
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

        act_path = (
            "Исполнительная_документация/"
            "03_Акты_скрытых_работ/"
            "АОСР_Заземление_TEST_PROJECT.docx"
        )

        assert act_path in names

        assert archive.read(
            act_path
        ) == b"HIDDEN WORKS ACT"
