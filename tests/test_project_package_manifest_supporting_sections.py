import json
from pathlib import Path

from app.services.project_package import ProjectPackage


def test_project_package_manifest_contains_supporting_section_requirements(tmp_path):
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
        "sections_count": 3,
        "sections_with_files": 0,
        "actual_files_count": 0,
        "sections": [
            {
                "number": "04",
                "code": "executive_schemes",
                "title": "Исполнительные схемы",
                "status": "Ожидает документов",
                "path": destination_folder / "04_Исполнительные_схемы",
                "actual_files_count": 0,
                "actual_files": [],
                "detected": {
                    "required_count": 1,
                    "high_priority_count": 1,
                    "documents": [
                        {"code": "grounding_executive_scheme"},
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

    assert section["code"] == "executive_schemes"
    assert section["required_count"] == 1
    assert section["high_priority_count"] == 1
    assert section["required_documents"][0]["code"] == "grounding_executive_scheme"
