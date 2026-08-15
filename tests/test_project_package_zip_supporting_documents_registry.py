import zipfile
from pathlib import Path

from app.services.project_package import ProjectPackage


def test_project_package_zip_includes_supporting_documents_registry(
    monkeypatch,
    tmp_path,
):
    package = ProjectPackage()

    project_name = "TEST_PROJECT"
    project_path = tmp_path / project_name
    analysis_folder = project_path / "analysis"
    package_folder = project_path / "executive_docs"

    analysis_folder.mkdir(parents=True)

    source = analysis_folder / "supporting_documents_registry.json"
    source.write_text(
        '{"requirements_count": 3}',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        package,
        "_project_path",
        lambda name: project_path,
    )

    def fake_create(name):
        package_folder.mkdir(parents=True, exist_ok=True)

        copied = package._copy_analysis_files(
            name,
            package_folder,
        )

        expected = package_folder / "supporting_documents_registry.json"

        assert expected.exists()
        assert str(expected) in copied

        return {
            "project": name,
            "package_folder": str(package_folder),
        }

    monkeypatch.setattr(
        package,
        "create",
        fake_create,
    )

    result = package.create_zip(project_name)

    zip_path = Path(result)

    assert zip_path.is_file()

    with zipfile.ZipFile(zip_path, "r") as archive:
        names = set(archive.namelist())

        registry_path = "supporting_documents_registry.json"

        assert registry_path in names

        content = archive.read(registry_path).decode("utf-8")

        assert '"requirements_count": 3' in content
