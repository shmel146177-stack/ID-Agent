import zipfile
from pathlib import Path

from fastapi.responses import FileResponse

import app.api.project_processor as api_module


def test_project_api_package_includes_supporting_documents_registry(
    monkeypatch,
    tmp_path,
):
    project_name = "TEST_PROJECT"

    package = api_module.project_package

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

        package._copy_analysis_files(
            name,
            package_folder,
        )

        return {
            "project": name,
            "package_folder": str(package_folder),
        }

    monkeypatch.setattr(
        package,
        "create",
        fake_create,
    )

    response = api_module.download_project_package(
        project_name
    )

    assert isinstance(response, FileResponse)
    assert response.media_type == "application/zip"

    zip_path = Path(response.path)
    assert zip_path.is_file()

    with zipfile.ZipFile(zip_path, "r") as archive:
        names = set(archive.namelist())

        registry_path = "supporting_documents_registry.json"

        assert registry_path in names

        content = archive.read(registry_path).decode("utf-8")
        assert '"requirements_count": 3' in content
