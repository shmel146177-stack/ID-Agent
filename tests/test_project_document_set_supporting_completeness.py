from app.generators.project_document_set import ProjectDocumentSet


def test_project_document_set_calculates_supporting_document_completeness(
    monkeypatch,
    tmp_path,
):
    generator = ProjectDocumentSet()

    project_name = "TEST_PROJECT"
    section_path = tmp_path / "04"

    folders = [
        {
            "number": "04",
            "code": "executive_schemes",
            "title": "Исполнительные схемы",
            "folder": "04_Исполнительные_схемы",
            "path": section_path,
            "description": "Исполнительные схемы",
        },
    ]

    supporting_documents = {
        "sections": [
            {
                "number": "04",
                "code": "executive_schemes",
                "required_count": 2,
                "high_priority_count": 1,
                "documents": [
                    {"code": "scheme_1"},
                    {"code": "scheme_2"},
                ],
            },
        ],
    }

    actual_files = [
        {
            "name": "scheme_1.pdf",
            "path": str(section_path / "scheme_1.pdf"),
            "extension": ".pdf",
            "size_bytes": 100,
        },
    ]

    monkeypatch.setattr(
        generator,
        "_detected_documents",
        lambda name: {},
    )

    monkeypatch.setattr(
        generator,
        "_list_section_files",
        lambda path: actual_files,
    )

    sections = generator._build_sections(
        project_name,
        folders,
        {},
        supporting_documents,
    )

    section = sections[0]
    detected = section["detected"]

    assert detected["required_count"] == 2
    assert detected["found_count"] == 1
    assert detected["missing_count"] == 1
    assert section["status"] == "Неполный комплект"
