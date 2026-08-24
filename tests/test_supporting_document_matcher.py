from app.services.supporting_document_matcher import SupportingDocumentMatcher
from app.services.supporting_documents_registry import SupportingDocumentsRegistry


def test_matcher_matches_grounding_resistance_protocol_by_type_and_text():
    matcher = SupportingDocumentMatcher()

    requirement = {
        "code": "grounding_resistance_protocol",
        "document_types": ["Протокол"],
        "match_keywords": ["сопротивлен", "заземл"],
    }

    grounding_document = {
        "filename": "grounding_protocol.pdf",
        "classification": "Протокол",
        "text": "Протокол измерения сопротивления заземляющего устройства",
    }

    cable_document = {
        "filename": "cable_protocol.pdf",
        "classification": "Протокол",
        "text": "Протокол испытаний кабельной линии 10 кВ",
    }

    assert matcher.matches(requirement, grounding_document) is True
    assert matcher.matches(requirement, cable_document) is False


def test_matcher_rejects_wrong_document_type_even_with_keywords():
    matcher = SupportingDocumentMatcher()

    requirement = {
        "code": "grounding_resistance_protocol",
        "document_types": ["Протокол"],
        "match_keywords": ["сопротивлен", "заземл"],
    }

    document = {
        "filename": "scheme.pdf",
        "classification": "Исполнительная схема",
        "text": "Сопротивление заземляющего устройства",
    }

    assert matcher.matches(requirement, document) is False


def test_real_grounding_requirement_matches_only_grounding_protocol():
    matcher = SupportingDocumentMatcher()

    requirement = SupportingDocumentsRegistry.REQUIREMENTS[
        "grounding_device"
    ][1]

    grounding_document = {
        "filename": "grounding_protocol.pdf",
        "classification": "Протокол",
        "text": "Протокол измерения сопротивления заземляющего устройства",
    }

    cable_document = {
        "filename": "cable_protocol.pdf",
        "classification": "Протокол",
        "text": "Протокол испытаний кабельной линии 10 кВ",
    }

    assert matcher.matches(requirement, grounding_document) is True
    assert matcher.matches(requirement, cable_document) is False


def test_real_grounding_scheme_requirement_rejects_cable_scheme():
    matcher = SupportingDocumentMatcher()

    requirement = SupportingDocumentsRegistry.REQUIREMENTS[
        "grounding_device"
    ][0]

    grounding_scheme = {
        "filename": "grounding_scheme.pdf",
        "classification": "Исполнительная схема",
        "text": "Исполнительная схема заземляющего устройства",
    }

    cable_scheme = {
        "filename": "cable_entry_scheme.pdf",
        "classification": "Исполнительная схема",
        "text": "Исполнительная схема кабельного ввода",
    }

    assert matcher.matches(requirement, grounding_scheme) is True
    assert matcher.matches(requirement, cable_scheme) is False


def test_real_cable_scheme_requirement_rejects_grounding_scheme():
    matcher = SupportingDocumentMatcher()

    requirement = SupportingDocumentsRegistry.REQUIREMENTS[
        "cable_entry"
    ][0]

    cable_scheme = {
        "filename": "cable_entry_scheme.pdf",
        "classification": "Исполнительная схема",
        "text": "Исполнительная схема кабельного ввода",
    }

    grounding_scheme = {
        "filename": "grounding_scheme.pdf",
        "classification": "Исполнительная схема",
        "text": "Исполнительная схема заземляющего устройства",
    }

    assert matcher.matches(requirement, cable_scheme) is True
    assert matcher.matches(requirement, grounding_scheme) is False


def test_real_cable_protocol_requirement_rejects_grounding_protocol():
    matcher = SupportingDocumentMatcher()

    requirement = SupportingDocumentsRegistry.REQUIREMENTS[
        "cable_entry"
    ][1]

    cable_protocol = {
        "filename": "cable_protocol.pdf",
        "classification": "Протокол",
        "text": "Протокол испытаний кабельной линии 10 кВ",
    }

    grounding_protocol = {
        "filename": "grounding_protocol.pdf",
        "classification": "Протокол",
        "text": "Протокол измерения сопротивления заземляющего устройства",
    }

    assert matcher.matches(requirement, cable_protocol) is True
    assert matcher.matches(requirement, grounding_protocol) is False


def test_matcher_matches_requirements_to_distinct_documents():
    matcher = SupportingDocumentMatcher()

    requirements = [
        SupportingDocumentsRegistry.REQUIREMENTS["grounding_device"][0],
        SupportingDocumentsRegistry.REQUIREMENTS["cable_entry"][0],
    ]

    documents = [
        {
            "filename": "grounding_scheme.pdf",
            "classification": "Исполнительная схема",
            "text": "Исполнительная схема заземляющего устройства",
        },
        {
            "filename": "cable_entry_scheme.pdf",
            "classification": "Исполнительная схема",
            "text": "Исполнительная схема кабельного ввода",
        },
    ]

    result = matcher.match_requirements(
        requirements,
        documents,
    )

    assert result["required_count"] == 2
    assert result["found_count"] == 2
    assert result["missing_count"] == 0

    matched = {
        item["requirement_code"]: item["filename"]
        for item in result["matched"]
    }

    assert matched["grounding_executive_scheme"] == "grounding_scheme.pdf"
    assert matched["cable_entry_executive_scheme"] == "cable_entry_scheme.pdf"


def test_matcher_does_not_reuse_one_document_for_two_requirements():
    matcher = SupportingDocumentMatcher()

    requirements = [
        {
            "code": "requirement_1",
            "document_types": ["Протокол"],
            "match_keywords": ["кабельн"],
        },
        {
            "code": "requirement_2",
            "document_types": ["Протокол"],
            "match_keywords": ["кабельн"],
        },
    ]

    documents = [
        {
            "filename": "single_protocol.pdf",
            "classification": "Протокол",
            "text": "Протокол испытаний кабельной линии",
        },
    ]

    result = matcher.match_requirements(
        requirements,
        documents,
    )

    assert result["required_count"] == 2
    assert result["found_count"] == 1
    assert result["missing_count"] == 1
    assert len(result["matched"]) == 1
    assert len(result["missing"]) == 1


def test_matcher_builds_documents_from_project_and_page_analysis():
    matcher = SupportingDocumentMatcher()

    project_analysis = {
        "documents": [
            {
                "filename": "grounding_protocol.pdf",
                "path": "input/grounding_protocol.pdf",
                "classification": "Протокол",
            },
        ],
    }

    page_analysis = {
        "documents": [
            {
                "filename": "grounding_protocol.pdf",
                "pages": [
                    {
                        "page": 1,
                        "text": "Протокол измерения",
                    },
                    {
                        "page": 2,
                        "text": "сопротивления заземляющего устройства",
                    },
                ],
            },
        ],
    }

    documents = matcher.build_documents(
        project_analysis,
        page_analysis,
    )

    assert len(documents) == 1

    document = documents[0]

    assert document["filename"] == "grounding_protocol.pdf"
    assert document["classification"] == "Протокол"
    assert document["path"] == "input/grounding_protocol.pdf"
    assert "Протокол измерения" in document["text"]
    assert "сопротивления заземляющего устройства" in document["text"]


def test_matcher_matches_real_requirements_from_analysis_data():
    matcher = SupportingDocumentMatcher()

    requirements = [
        SupportingDocumentsRegistry.REQUIREMENTS["grounding_device"][0],
        SupportingDocumentsRegistry.REQUIREMENTS["grounding_device"][1],
        SupportingDocumentsRegistry.REQUIREMENTS["cable_entry"][0],
        SupportingDocumentsRegistry.REQUIREMENTS["cable_entry"][1],
    ]

    project_analysis = {
        "documents": [
            {
                "filename": "grounding_scheme.pdf",
                "path": "input/grounding_scheme.pdf",
                "classification": "Исполнительная схема",
            },
            {
                "filename": "grounding_protocol.pdf",
                "path": "input/grounding_protocol.pdf",
                "classification": "Протокол",
            },
            {
                "filename": "cable_protocol.pdf",
                "path": "input/cable_protocol.pdf",
                "classification": "Протокол",
            },
        ],
    }

    page_analysis = {
        "documents": [
            {
                "filename": "grounding_scheme.pdf",
                "pages": [
                    {"text": "Исполнительная схема заземляющего устройства"},
                ],
            },
            {
                "filename": "grounding_protocol.pdf",
                "pages": [
                    {"text": "Протокол измерения сопротивления заземляющего устройства"},
                ],
            },
            {
                "filename": "cable_protocol.pdf",
                "pages": [
                    {"text": "Протокол испытаний кабельной линии 10 кВ"},
                ],
            },
        ],
    }

    result = matcher.match_analysis(
        requirements,
        project_analysis,
        page_analysis,
    )

    assert result["required_count"] == 4
    assert result["found_count"] == 3
    assert result["missing_count"] == 1

    missing_codes = {
        item["requirement_code"]
        for item in result["missing"]
    }

    assert missing_codes == {"cable_entry_executive_scheme"}


def test_real_supports_scheme_requirement_rejects_cable_scheme():
    matcher = SupportingDocumentMatcher()

    requirement = SupportingDocumentsRegistry.REQUIREMENTS[
        "support_foundations"
    ][0]

    supports_scheme = {
        "filename": "supports_scheme.pdf",
        "classification": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430",
        "text": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430 \u0440\u0430\u0441\u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u044f \u0432\u0440\u0435\u043c\u0435\u043d\u043d\u044b\u0445 \u043e\u043f\u043e\u0440",
    }

    cable_scheme = {
        "filename": "cable_entry_scheme.pdf",
        "classification": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430",
        "text": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430 \u043a\u0430\u0431\u0435\u043b\u044c\u043d\u043e\u0433\u043e \u0432\u0432\u043e\u0434\u0430",
    }

    assert matcher.matches(requirement, supports_scheme) is True
    assert matcher.matches(requirement, cable_scheme) is False


def test_matcher_supports_any_keyword_group():
    matcher = SupportingDocumentMatcher()

    requirement = {
        "code": "grounding_quality",
        "document_types": ["Сертификат"],
        "match_any_keywords": [
            "заземл",
            "электрод",
            "полос",
        ],
    }

    grounding_certificate = {
        "filename": "grounding_certificate.pdf",
        "classification": "Сертификат",
        "text": "Сертификат соответствия на полосу стальную 40х5 мм",
    }

    cable_certificate = {
        "filename": "cable_certificate.pdf",
        "classification": "Сертификат",
        "text": "Сертификат соответствия на кабель силовой 10 кВ",
    }

    assert matcher.matches(requirement, grounding_certificate) is True
    assert matcher.matches(requirement, cable_certificate) is False


def test_real_grounding_quality_requirement_rejects_cable_certificate():
    matcher = SupportingDocumentMatcher()

    requirement = SupportingDocumentsRegistry.REQUIREMENTS[
        "grounding_device"
    ][2]

    grounding_certificate = {
        "filename": "grounding_strip_certificate.pdf",
        "classification": "Сертификат",
        "text": "Сертификат соответствия на полосу стальную 40х5 мм",
    }

    cable_certificate = {
        "filename": "cable_certificate.pdf",
        "classification": "Сертификат",
        "text": "Сертификат соответствия на кабель силовой 10 кВ",
    }

    assert matcher.matches(requirement, grounding_certificate) is True
    assert matcher.matches(requirement, cable_certificate) is False


def test_real_cable_quality_requirement_rejects_grounding_certificate():
    matcher = SupportingDocumentMatcher()

    requirement = SupportingDocumentsRegistry.REQUIREMENTS["cable_entry"][2]

    cable_certificate = {
        "filename": "cable_certificate.pdf",
        "classification": "Сертификат",
        "text": "Сертификат соответствия на кабель силовой 10 кВ",
    }

    grounding_certificate = {
        "filename": "grounding_strip_certificate.pdf",
        "classification": "Сертификат",
        "text": "Сертификат соответствия на полосу стальную 40х5 мм",
    }

    assert matcher.matches(requirement, cable_certificate) is True
    assert matcher.matches(requirement, grounding_certificate) is False


def test_real_supports_quality_requirement_rejects_cable_certificate():
    matcher = SupportingDocumentMatcher()

    requirement = SupportingDocumentsRegistry.REQUIREMENTS["support_foundations"][1]

    supports_certificate = {
        "filename": "supports_certificate.pdf",
        "classification": "Сертификат",
        "text": "Сертификат соответствия на элементы временных опор и фундаментов",
    }

    cable_certificate = {
        "filename": "cable_certificate.pdf",
        "classification": "Сертификат",
        "text": "Сертификат соответствия на кабель силовой 10 кВ",
    }

    assert matcher.matches(requirement, supports_certificate) is True
    assert matcher.matches(requirement, cable_certificate) is False


def test_matcher_matches_real_quality_filenames_from_project_analysis():
    matcher = SupportingDocumentMatcher()

    requirements = [
        {
            "code": "certificate",
            "title": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442",
            "document_types": [
                "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442"
            ],
            "match_keywords": [
                "\u0441\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442"
            ],
        },
        {
            "code": "passport",
            "title": "\u041f\u0430\u0441\u043f\u043e\u0440\u0442 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u044f",
            "document_types": [
                "\u041f\u0430\u0441\u043f\u043e\u0440\u0442 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u044f"
            ],
            "match_keywords": [
                "\u043f\u0430\u0441\u043f\u043e\u0440\u0442"
            ],
        },
    ]

    project_analysis = {
        "documents": [
            {
                "filename": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442.pdf",
                "path": "projects/test/input/certificate.pdf",
                "classification": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442",
            },
            {
                "filename": "\u043f\u0430\u0441\u043f\u043e\u0440\u0442.pdf",
                "path": "projects/test/input/passport.pdf",
                "classification": "\u041f\u0430\u0441\u043f\u043e\u0440\u0442 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u044f",
            },
        ]
    }

    page_analysis = {
        "documents": [
            {
                "filename": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442.pdf",
                "pages": [],
            },
            {
                "filename": "\u043f\u0430\u0441\u043f\u043e\u0440\u0442.pdf",
                "pages": [],
            },
        ]
    }

    result = matcher.match_analysis(
        requirements,
        project_analysis,
        page_analysis,
    )

    assert result["required_count"] == 2
    assert result["found_count"] == 2
    assert result["missing_count"] == 0
    assert result["missing"] == []

    assert result["matched"][0]["filename"] == "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442.pdf"
    assert result["matched"][0]["classification"] == "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442"

    assert result["matched"][1]["filename"] == "\u043f\u0430\u0441\u043f\u043e\u0440\u0442.pdf"
    assert result["matched"][1]["classification"] == "\u041f\u0430\u0441\u043f\u043e\u0440\u0442 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u044f"


def test_quality_keyword_does_not_match_inside_compound_word():
    matcher = SupportingDocumentMatcher()

    requirement = SupportingDocumentsRegistry.REQUIREMENTS[
        "cable_entry"
    ][2]

    false_certificate = {
        "filename": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442.pdf",
        "classification": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442",
        "text": (
            "\u041a\u043b\u0435\u043c\u043c\u0430 "
            "\u0434\u0432\u0443\u0445\u043f\u0440\u043e\u0445\u043e\u0434\u043d\u0430\u044f "
            "2x2,5 \u043a\u0432.\u043c\u043c."
        ),
    }

    assert matcher.matches(
        requirement,
        false_certificate,
    ) is False


def test_real_cable_quality_requirement_rejects_generic_passage_word():
    matcher = SupportingDocumentMatcher()

    requirement = SupportingDocumentsRegistry.REQUIREMENTS[
        "cable_entry"
    ][2]

    unrelated_certificate = {
        "filename": "equipment_certificate.pdf",
        "classification": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442",
        "text": (
            "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442 "
            "\u043d\u0430 \u0448\u043a\u0430\u0444 "
            "\u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f. "
            "\u0421\u0432\u043e\u0431\u043e\u0434\u043d\u044b\u0439 "
            "\u043f\u0440\u043e\u0445\u043e\u0434 "
            "\u0434\u043e\u043b\u0436\u0435\u043d "
            "\u0441\u043e\u0445\u0440\u0430\u043d\u044f\u0442\u044c\u0441\u044f."
        ),
    }

    assert matcher.matches(
        requirement,
        unrelated_certificate,
    ) is False
