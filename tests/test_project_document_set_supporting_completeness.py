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


def test_project_document_set_does_not_count_wrong_supporting_document(
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
            "title": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0441\u0445\u0435\u043c\u044b",
            "folder": "04_executive_schemes",
            "path": section_path,
            "description": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0441\u0445\u0435\u043c\u044b",
        },
    ]

    supporting_documents = {
        "sections": [
            {
                "number": "04",
                "code": "executive_schemes",
                "required_count": 1,
                "high_priority_count": 1,
                "documents": [
                    {
                        "code": "grounding_executive_scheme",
                        "title": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430 \u0437\u0430\u0437\u0435\u043c\u043b\u0435\u043d\u0438\u044f",
                        "document_types": [
                            "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430"
                        ],
                        "match_keywords": ["\u0437\u0430\u0437\u0435\u043c\u043b"],
                    },
                ],
            },
        ],
    }

    actual_files = [
        {
            "name": "cable_entry_scheme.pdf",
            "relative_path": "cable_entry_scheme.pdf",
            "extension": ".pdf",
            "size_bytes": 100,
        },
    ]

    project_analysis = {
        "documents": [
            {
                "filename": "cable_entry_scheme.pdf",
                "path": "input/cable_entry_scheme.pdf",
                "classification": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430",
            },
        ],
    }

    page_analysis = {
        "documents": [
            {
                "filename": "cable_entry_scheme.pdf",
                "pages": [
                    {
                        "text": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430 \u043a\u0430\u0431\u0435\u043b\u044c\u043d\u043e\u0433\u043e \u0432\u0432\u043e\u0434\u0430",
                    },
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
        lambda path: actual_files,
    )

    def fake_load_json(path):
        if path.name == "project_analysis.json":
            return project_analysis
        if path.name == "page_analysis.json":
            return page_analysis
        return {}

    monkeypatch.setattr(
        generator,
        "_load_json",
        fake_load_json,
    )

    sections = generator._build_sections(
        project_name,
        folders,
        {},
        supporting_documents,
    )

    detected = sections[0]["detected"]

    assert detected["required_count"] == 1
    assert detected["found_count"] == 0
    assert detected["missing_count"] == 1
    assert sections[0]["status"] == "\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442"


def test_project_document_set_counts_matching_supporting_document(
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
            "title": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0441\u0445\u0435\u043c\u044b",
            "folder": "04_executive_schemes",
            "path": section_path,
            "description": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0441\u0445\u0435\u043c\u044b",
        },
    ]

    supporting_documents = {
        "sections": [
            {
                "number": "04",
                "code": "executive_schemes",
                "required_count": 1,
                "high_priority_count": 1,
                "documents": [
                    {
                        "code": "grounding_executive_scheme",
                        "title": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430 \u0437\u0430\u0437\u0435\u043c\u043b\u0435\u043d\u0438\u044f",
                        "document_types": [
                            "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430"
                        ],
                        "match_keywords": ["\u0437\u0430\u0437\u0435\u043c\u043b"],
                    },
                ],
            },
        ],
    }

    actual_files = [
        {
            "name": "grounding_scheme.pdf",
            "relative_path": "grounding_scheme.pdf",
            "extension": ".pdf",
            "size_bytes": 100,
        },
    ]

    project_analysis = {
        "documents": [
            {
                "filename": "grounding_scheme.pdf",
                "path": "input/grounding_scheme.pdf",
                "classification": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430",
            },
        ],
    }

    page_analysis = {
        "documents": [
            {
                "filename": "grounding_scheme.pdf",
                "pages": [
                    {
                        "text": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430 \u0437\u0430\u0437\u0435\u043c\u043b\u044f\u044e\u0449\u0435\u0433\u043e \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430",
                    },
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
        lambda path: actual_files,
    )

    def fake_load_json(path):
        if path.name == "project_analysis.json":
            return project_analysis
        if path.name == "page_analysis.json":
            return page_analysis
        return {}

    monkeypatch.setattr(
        generator,
        "_load_json",
        fake_load_json,
    )

    sections = generator._build_sections(
        project_name,
        folders,
        {},
        supporting_documents,
    )

    detected = sections[0]["detected"]

    assert detected["required_count"] == 1
    assert detected["found_count"] == 1
    assert detected["missing_count"] == 0
    assert sections[0]["status"] == "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442 \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d"
