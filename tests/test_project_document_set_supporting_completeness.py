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


def test_project_document_set_does_not_count_unrelated_quality_documents(
    monkeypatch,
    tmp_path,
):
    generator = ProjectDocumentSet()

    project_name = "TEST_PROJECT"
    section_path = tmp_path / "06"

    folders = [
        {
            "number": "06",
            "code": "quality_documents",
            "title": "Паспорта и сертификаты",
            "folder": "06_Паспорта_и_сертификаты",
            "path": section_path,
            "description": "Документы качества",
        },
    ]

    supporting_documents = {
        "sections": [
            {
                "number": "06",
                "code": "quality_documents",
                "required_count": 1,
                "high_priority_count": 1,
                "documents": [
                    {
                        "code": "cable_quality_documents",
                        "title": "Документы качества на кабель",
                        "document_types": [
                            "Паспорт оборудования",
                            "Сертификат",
                            "Декларация",
                        ],
                        "match_any_keywords": [
                            "кабел",
                            "труб",
                            "проход",
                        ],
                    },
                ],
            },
        ],
    }

    actual_files = [
        {
            "name": "Сертификат.pdf",
            "relative_path": "Сертификат.pdf",
            "extension": ".pdf",
            "size_bytes": 100,
        },
        {
            "name": "паспорт.pdf",
            "relative_path": "паспорт.pdf",
            "extension": ".pdf",
            "size_bytes": 100,
        },
    ]

    project_analysis = {
        "documents": [
            {
                "filename": "Сертификат.pdf",
                "classification": "Сертификат",
            },
            {
                "filename": "паспорт.pdf",
                "classification": "Паспорт оборудования",
            },
        ],
    }

    page_analysis = {
        "documents": [
            {
                "filename": "Сертификат.pdf",
                "pages": [
                    {
                        "text": "Клемма двухпроходная 2x2,5 кв.мм.",
                    },
                ],
            },
            {
                "filename": "паспорт.pdf",
                "pages": [
                    {
                        "text": "Паспорт шкафа управления и электрического оборудования.",
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

    section = sections[0]
    detected = section["detected"]

    assert section["actual_files_count"] == 2
    assert detected["required_count"] == 1
    assert detected["found_count"] == 0
    assert detected["missing_count"] == 1
    assert section["status"] == "Неполный комплект"


def test_project_document_set_counts_matching_quality_document(
    monkeypatch,
    tmp_path,
):
    generator = ProjectDocumentSet()

    project_name = "TEST_PROJECT"
    section_path = tmp_path / "06"

    folders = [
        {
            "number": "06",
            "code": "quality_documents",
            "title": "\u041f\u0430\u0441\u043f\u043e\u0440\u0442\u0430 \u0438 \u0441\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u044b",
            "folder": "06_quality_documents",
            "path": section_path,
            "description": "\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u0430",
        },
    ]

    supporting_documents = {
        "sections": [
            {
                "number": "06",
                "code": "quality_documents",
                "required_count": 1,
                "high_priority_count": 1,
                "documents": [
                    {
                        "code": "cable_quality_documents",
                        "title": "\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u0430 \u043d\u0430 \u043a\u0430\u0431\u0435\u043b\u044c",
                        "document_types": [
                            "\u041f\u0430\u0441\u043f\u043e\u0440\u0442 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u044f",
                            "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442",
                            "\u0414\u0435\u043a\u043b\u0430\u0440\u0430\u0446\u0438\u044f",
                        ],
                        "match_any_keywords": [
                            "\u043a\u0430\u0431\u0435\u043b",
                            "\u0442\u0440\u0443\u0431",
                            "\u043f\u0440\u043e\u0445\u043e\u0434",
                        ],
                    },
                ],
            },
        ],
    }

    actual_files = [
        {
            "name": "cable_certificate.pdf",
            "relative_path": "cable_certificate.pdf",
            "extension": ".pdf",
            "size_bytes": 100,
        },
    ]

    project_analysis = {
        "documents": [
            {
                "filename": "cable_certificate.pdf",
                "classification": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442",
            },
        ],
    }

    page_analysis = {
        "documents": [
            {
                "filename": "cable_certificate.pdf",
                "pages": [
                    {
                        "text": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442 \u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0438\u044f \u043d\u0430 \u043a\u0430\u0431\u0435\u043b\u044c \u0441\u0438\u043b\u043e\u0432\u043e\u0439 10 \u043a\u0412",
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

    section = sections[0]
    detected = section["detected"]

    assert section["actual_files_count"] == 1
    assert detected["required_count"] == 1
    assert detected["found_count"] == 1
    assert detected["missing_count"] == 0
    assert section["status"] == "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442 \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d"


def test_project_document_set_counts_matching_cable_test_protocol(
    monkeypatch,
    tmp_path,
):
    generator = ProjectDocumentSet()

    project_name = "TEST_PROJECT"
    section_path = tmp_path / "05"

    folders = [
        {
            "number": "05",
            "code": "tests",
            "title": "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\u044b \u0438 \u0438\u0441\u043f\u044b\u0442\u0430\u043d\u0438\u044f",
            "folder": "05_tests",
            "path": section_path,
            "description": "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\u044b \u0438 \u0438\u0441\u043f\u044b\u0442\u0430\u043d\u0438\u044f",
        },
    ]

    supporting_documents = {
        "sections": [
            {
                "number": "05",
                "code": "tests",
                "required_count": 1,
                "high_priority_count": 0,
                "documents": [
                    {
                        "code": "cable_test_protocol",
                        "title": "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b \u0438\u0441\u043f\u044b\u0442\u0430\u043d\u0438\u0439 \u043a\u0430\u0431\u0435\u043b\u044c\u043d\u043e\u0439 \u043b\u0438\u043d\u0438\u0438",
                        "document_types": [
                            "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b",
                        ],
                        "match_keywords": [
                            "\u043a\u0430\u0431\u0435\u043b\u044c\u043d",
                        ],
                    },
                ],
            },
        ],
    }

    actual_files = [
        {
            "name": "cable_protocol.pdf",
            "relative_path": "cable_protocol.pdf",
            "extension": ".pdf",
            "size_bytes": 100,
        },
    ]

    project_analysis = {
        "documents": [
            {
                "filename": "cable_protocol.pdf",
                "classification": "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b",
            },
        ],
    }

    page_analysis = {
        "documents": [
            {
                "filename": "cable_protocol.pdf",
                "pages": [
                    {
                        "text": "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b \u0438\u0441\u043f\u044b\u0442\u0430\u043d\u0438\u0439 \u043a\u0430\u0431\u0435\u043b\u044c\u043d\u043e\u0439 \u043b\u0438\u043d\u0438\u0438 10 \u043a\u0412",
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

    section = sections[0]
    detected = section["detected"]

    assert section["actual_files_count"] == 1
    assert detected["required_count"] == 1
    assert detected["found_count"] == 1
    assert detected["missing_count"] == 0
    assert section["status"] == "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442 \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d"


def test_project_document_set_rejects_wrong_cable_test_protocol(
    monkeypatch,
    tmp_path,
):
    generator = ProjectDocumentSet()

    project_name = "TEST_PROJECT"
    section_path = tmp_path / "05"

    folders = [
        {
            "number": "05",
            "code": "tests",
            "title": "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\u044b \u0438 \u0438\u0441\u043f\u044b\u0442\u0430\u043d\u0438\u044f",
            "folder": "05_tests",
            "path": section_path,
            "description": "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\u044b \u0438 \u0438\u0441\u043f\u044b\u0442\u0430\u043d\u0438\u044f",
        },
    ]

    supporting_documents = {
        "sections": [
            {
                "number": "05",
                "code": "tests",
                "required_count": 1,
                "high_priority_count": 0,
                "documents": [
                    {
                        "code": "cable_test_protocol",
                        "title": "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b \u0438\u0441\u043f\u044b\u0442\u0430\u043d\u0438\u0439 \u043a\u0430\u0431\u0435\u043b\u044c\u043d\u043e\u0439 \u043b\u0438\u043d\u0438\u0438",
                        "document_types": [
                            "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b",
                        ],
                        "match_keywords": [
                            "\u043a\u0430\u0431\u0435\u043b\u044c\u043d",
                        ],
                    },
                ],
            },
        ],
    }

    actual_files = [
        {
            "name": "grounding_protocol.pdf",
            "relative_path": "grounding_protocol.pdf",
            "extension": ".pdf",
            "size_bytes": 100,
        },
    ]

    project_analysis = {
        "documents": [
            {
                "filename": "grounding_protocol.pdf",
                "classification": "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b",
            },
        ],
    }

    page_analysis = {
        "documents": [
            {
                "filename": "grounding_protocol.pdf",
                "pages": [
                    {
                        "text": "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b \u0438\u0437\u043c\u0435\u0440\u0435\u043d\u0438\u044f \u0441\u043e\u043f\u0440\u043e\u0442\u0438\u0432\u043b\u0435\u043d\u0438\u044f \u0437\u0430\u0437\u0435\u043c\u043b\u044f\u044e\u0449\u0435\u0433\u043e \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430",
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

    section = sections[0]
    detected = section["detected"]

    assert section["actual_files_count"] == 1
    assert detected["required_count"] == 1
    assert detected["found_count"] == 0
    assert detected["missing_count"] == 1
    assert section["status"] == "\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442"


def test_project_document_set_counts_matching_cable_entry_scheme(
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
                        "code": "cable_entry_executive_scheme",
                        "title": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430 \u043a\u0430\u0431\u0435\u043b\u044c\u043d\u043e\u0433\u043e \u0432\u0432\u043e\u0434\u0430",
                        "document_types": [
                            "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430",
                        ],
                        "match_keywords": [
                            "\u043a\u0430\u0431\u0435\u043b\u044c\u043d",
                            "\u0432\u0432\u043e\u0434",
                        ],
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

    section = sections[0]
    detected = section["detected"]

    assert section["actual_files_count"] == 1
    assert detected["required_count"] == 1
    assert detected["found_count"] == 1
    assert detected["missing_count"] == 0
    assert section["status"] == "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442 \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d"
