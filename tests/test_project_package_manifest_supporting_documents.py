import json
from pathlib import Path

from app.services.project_package import ProjectPackage


def test_project_package_manifest_contains_supporting_documents(tmp_path):
    package = ProjectPackage()

    project_name = "TEST_PROJECT"
    destination_folder = tmp_path / "executive_docs"
    destination_folder.mkdir(parents=True)

    processor_result = {
        "status": "Готово",
        "completeness": {},
        "hidden_works_acts": {},
        "supporting_documents": {
            "status": "Сформирован предварительный перечень",
            "requirements_count": 3,
            "high_priority_count": 2,
            "requires_field_confirmation": True,
            "sections": [
                {
                    "number": "04",
                    "code": "executive_schemes",
                    "title": "Исполнительные схемы",
                    "required_count": 1,
                    "high_priority_count": 1,
                },
                {
                    "number": "05",
                    "code": "tests",
                    "title": "Протоколы и испытания",
                    "required_count": 1,
                    "high_priority_count": 1,
                },
                {
                    "number": "06",
                    "code": "quality_documents",
                    "title": "Паспорта и сертификаты",
                    "required_count": 1,
                    "high_priority_count": 0,
                },
            ],
        },
    }

    document_set_result = {
        "sections_count": 0,
        "sections_with_files": 0,
        "actual_files_count": 0,
        "sections": [],
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

    supporting = manifest["supporting_documents"]

    assert supporting["requirements_count"] == 3
    assert supporting["high_priority_count"] == 2
    assert supporting["requires_field_confirmation"] is True

    assert [
        section["number"]
        for section in supporting["sections"]
    ] == ["04", "05", "06"]

    assert supporting["sections"][0]["code"] == "executive_schemes"
    assert supporting["sections"][1]["code"] == "tests"
    assert supporting["sections"][2]["code"] == "quality_documents"
