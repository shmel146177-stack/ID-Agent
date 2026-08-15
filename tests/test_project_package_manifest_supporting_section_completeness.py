import json
from pathlib import Path

from app.services.project_package import ProjectPackage


def test_project_package_manifest_contains_supporting_section_completeness(tmp_path):
    package = ProjectPackage()

    project_name = "TEST_PROJECT"
    destination_folder = tmp_path / "executive_docs"
    destination_folder.mkdir(parents=True)

    processor_result = {
        "status": "Готово",
        "completeness": {},
        "hidden_works_acts": {},
        "supporting_documents": {},
    }

    document_set_result = {
        "sections_count": 1,
        "sections_with_files": 1,
        "actual_files_count": 1,
        "sections": [
            {
                "number": "04",
                "code": "executive_schemes",
                "title": "Исполнительные схемы",
                "status": "Неполный комплект",
                "path": destination_folder / "04_Исполнительные_схемы",
                "actual_files_count": 1,
                "actual_files": [],
                "detected": {
                    "required_count": 2,
                    "found_count": 1,
                    "missing_count": 1,
                    "high_priority_count": 1,
                    "documents": [
                        {"code": "scheme_1"},
                        {"code": "scheme_2"},
                    ],
                },
            },
        ],
    }

    inventory = {
        "files": [],
        "folders": [],
    }

    manifest_path = package._create_manifest(
        project_name,
        destination_folder,
        processor_result,
        document_set_result,
        inventory,
        [],
    )

    manifest = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )

    section = manifest["document_sections"][0]

    assert section["required_count"] == 2
    assert section["found_count"] == 1
    assert section["missing_count"] == 1
    assert section["status"] == "Неполный комплект"
