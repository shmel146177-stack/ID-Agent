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


def test_project_package_zip_preserves_unmatched_quality_section_manifest(
    monkeypatch,
    tmp_path,
):
    import json
    import zipfile
    from pathlib import Path

    package = ProjectPackage()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    package_folder = project_path / "executive_docs"

    package_folder.mkdir(parents=True)

    manifest = {
        "project": project_name,
        "document_sections": [
            {
                "number": "06",
                "code": "quality_documents",
                "title": "Паспорта и сертификаты",
                "status": "Неполный комплект",
                "actual_files_count": 2,
                "required_count": 3,
                "found_count": 0,
                "missing_count": 3,
            },
        ],
    }

    (package_folder / "package_manifest.json").write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
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

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:

        assert "package_manifest.json" in archive.namelist()

        archived_manifest = json.loads(
            archive.read(
                "package_manifest.json"
            ).decode("utf-8")
        )

    section = archived_manifest["document_sections"][0]

    assert section["code"] == "quality_documents"
    assert section["status"] == "Неполный комплект"
    assert section["actual_files_count"] == 2
    assert section["required_count"] == 3
    assert section["found_count"] == 0
    assert section["missing_count"] == 3


def test_project_package_zip_preserves_matching_quality_section_manifest(
    monkeypatch,
    tmp_path,
):
    import json
    import zipfile
    from pathlib import Path

    package = ProjectPackage()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    package_folder = project_path / "executive_docs"

    package_folder.mkdir(parents=True)

    manifest = {
        "project": project_name,
        "document_sections": [
            {
                "number": "06",
                "code": "quality_documents",
                "title": "Паспорта и сертификаты",
                "status": "Комплект сформирован",
                "actual_files_count": 1,
                "required_count": 1,
                "found_count": 1,
                "missing_count": 0,
            },
        ],
    }

    (package_folder / "package_manifest.json").write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
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

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:

        assert "package_manifest.json" in archive.namelist()

        archived_manifest = json.loads(
            archive.read(
                "package_manifest.json"
            ).decode("utf-8")
        )

    section = archived_manifest["document_sections"][0]

    assert section["code"] == "quality_documents"
    assert section["status"] == "Комплект сформирован"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 1
    assert section["missing_count"] == 0


def test_project_package_zip_preserves_matching_cable_protocol_section_manifest(
    monkeypatch,
    tmp_path,
):
    import json
    import zipfile
    from pathlib import Path

    package = ProjectPackage()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    package_folder = project_path / "executive_docs"

    package_folder.mkdir(parents=True)

    manifest = {
        "project": project_name,
        "document_sections": [
            {
                "number": "05",
                "code": "tests",
                "title": "Протоколы и испытания",
                "status": "Комплект сформирован",
                "actual_files_count": 1,
                "required_count": 1,
                "found_count": 1,
                "missing_count": 0,
            },
        ],
    }

    (package_folder / "package_manifest.json").write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
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

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:

        assert "package_manifest.json" in archive.namelist()

        archived_manifest = json.loads(
            archive.read(
                "package_manifest.json"
            ).decode("utf-8")
        )

    section = archived_manifest["document_sections"][0]

    assert section["code"] == "tests"
    assert section["status"] == "Комплект сформирован"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 1
    assert section["missing_count"] == 0


def test_project_package_zip_preserves_wrong_cable_protocol_section_incomplete(
    monkeypatch,
    tmp_path,
):
    import json
    import zipfile
    from pathlib import Path

    package = ProjectPackage()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    package_folder = project_path / "executive_docs"

    package_folder.mkdir(parents=True)

    manifest = {
        "project": project_name,
        "document_sections": [
            {
                "number": "05",
                "code": "tests",
                "title": "Протоколы и испытания",
                "status": "Неполный комплект",
                "actual_files_count": 1,
                "required_count": 1,
                "found_count": 0,
                "missing_count": 1,
            },
        ],
    }

    (package_folder / "package_manifest.json").write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
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

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:

        assert "package_manifest.json" in archive.namelist()

        archived_manifest = json.loads(
            archive.read(
                "package_manifest.json"
            ).decode("utf-8")
        )

    section = archived_manifest["document_sections"][0]

    assert section["code"] == "tests"
    assert section["status"] == "Неполный комплект"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 0
    assert section["missing_count"] == 1


def test_project_package_zip_preserves_matching_cable_entry_scheme_manifest(
    monkeypatch,
    tmp_path,
):
    import json
    import zipfile
    from pathlib import Path

    package = ProjectPackage()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    package_folder = project_path / "executive_docs"

    package_folder.mkdir(parents=True)

    manifest = {
        "project": project_name,
        "document_sections": [
            {
                "number": "04",
                "code": "executive_schemes",
                "title": "Исполнительные схемы",
                "status": "Комплект сформирован",
                "actual_files_count": 1,
                "required_count": 1,
                "found_count": 1,
                "missing_count": 0,
            },
        ],
    }

    (package_folder / "package_manifest.json").write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
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

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:

        assert "package_manifest.json" in archive.namelist()

        archived_manifest = json.loads(
            archive.read(
                "package_manifest.json"
            ).decode("utf-8")
        )

    section = archived_manifest["document_sections"][0]

    assert section["code"] == "executive_schemes"
    assert section["status"] == "Комплект сформирован"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 1
    assert section["missing_count"] == 0


def test_project_package_zip_preserves_wrong_cable_entry_scheme_incomplete(
    monkeypatch,
    tmp_path,
):
    import json
    import zipfile
    from pathlib import Path

    package = ProjectPackage()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    package_folder = project_path / "executive_docs"

    package_folder.mkdir(parents=True)

    manifest = {
        "project": project_name,
        "document_sections": [
            {
                "number": "04",
                "code": "executive_schemes",
                "title": "Исполнительные схемы",
                "status": "Неполный комплект",
                "actual_files_count": 1,
                "required_count": 1,
                "found_count": 0,
                "missing_count": 1,
            },
        ],
    }

    (package_folder / "package_manifest.json").write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
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

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:

        assert "package_manifest.json" in archive.namelist()

        archived_manifest = json.loads(
            archive.read(
                "package_manifest.json"
            ).decode("utf-8")
        )

    section = archived_manifest["document_sections"][0]

    assert section["code"] == "executive_schemes"
    assert section["status"] == "Неполный комплект"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 0
    assert section["missing_count"] == 1
