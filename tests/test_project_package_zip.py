import zipfile
from pathlib import Path

from app.services.project_package import ProjectPackage


def test_project_package_create_zip_creates_real_archive(monkeypatch, tmp_path):

    package = ProjectPackage()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    package_folder = project_path / "executive_docs"

    package_folder.mkdir(parents=True)

    (package_folder / "report.docx").write_bytes(
        b"REPORT"
    )

    nested_folder = package_folder / "08_final"
    nested_folder.mkdir()

    (nested_folder / "registry.xlsx").write_bytes(
        b"REGISTRY"
    )

    (nested_folder / "package_manifest.json").write_text(
        '{"project": "TEST_PROJECT"}',
        encoding="utf-8",
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

    result = package.create_zip(project_name)

    zip_path = Path(result)

    assert zip_path.exists()
    assert zip_path.is_file()
    assert zip_path.suffix.lower() == ".zip"
    assert zip_path.stat().st_size > 0

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:

        names = set(
            archive.namelist()
        )

        assert "report.docx" in names
        assert "08_final/registry.xlsx" in names
        assert "08_final/package_manifest.json" in names

        assert archive.read(
            "report.docx"
        ) == b"REPORT"

        assert archive.read(
            "08_final/registry.xlsx"
        ) == b"REGISTRY"
