from pathlib import Path

from app.generators.project_document_set import ProjectDocumentSet


def test_project_document_set_adds_supporting_requirements_to_sections(
    monkeypatch,
    tmp_path,
):
    generator = ProjectDocumentSet()

    project_name = "TEST_PROJECT"

    folders = [
        {
            "number": "04",
            "code": "executive_schemes",
            "title": "Исполнительные схемы",
            "folder": "04_Исполнительные_схемы",
            "path": tmp_path / "04",
            "description": "Исполнительные схемы",
        },
        {
            "number": "05",
            "code": "tests",
            "title": "Протоколы и испытания",
            "folder": "05_Протоколы_и_испытания",
            "path": tmp_path / "05",
            "description": "Протоколы и испытания",
        },
        {
            "number": "06",
            "code": "quality_documents",
            "title": "Паспорта и сертификаты",
            "folder": "06_Паспорта_и_сертификаты",
            "path": tmp_path / "06",
            "description": "Паспорта и сертификаты",
        },
    ]

    supporting_documents = {
        "requirements_count": 3,
        "high_priority_count": 2,
        "requires_field_confirmation": True,
        "sections": [
            {
                "number": "04",
                "code": "executive_schemes",
                "required_count": 1,
                "high_priority_count": 1,
                "documents": [
                    {"code": "grounding_executive_scheme"},
                ],
            },
            {
                "number": "05",
                "code": "tests",
                "required_count": 1,
                "high_priority_count": 1,
                "documents": [
                    {"code": "grounding_resistance_protocol"},
                ],
            },
            {
                "number": "06",
                "code": "quality_documents",
                "required_count": 1,
                "high_priority_count": 0,
                "documents": [
                    {"code": "grounding_quality_documents"},
                ],
            },
        ],
    }

    monkeypatch.setattr(
        generator,
        "_detected_documents",
        lambda name: {},
    )

    monkeypatch.setattr(
        generator,
        "_list_section_files",
        lambda path: [],
    )

    sections = generator._build_sections(
        project_name,
        folders,
        {},
        supporting_documents,
    )

    by_code = {
        section["code"]: section
        for section in sections
    }

    assert by_code["executive_schemes"]["detected"]["required_count"] == 1
    assert by_code["tests"]["detected"]["required_count"] == 1
    assert by_code["quality_documents"]["detected"]["required_count"] == 1

    assert by_code["executive_schemes"]["detected"]["high_priority_count"] == 1
    assert by_code["tests"]["detected"]["high_priority_count"] == 1
    assert by_code["quality_documents"]["detected"]["high_priority_count"] == 0

    assert (
        by_code["executive_schemes"]["detected"]["documents"][0]["code"]
        == "grounding_executive_scheme"
    )
