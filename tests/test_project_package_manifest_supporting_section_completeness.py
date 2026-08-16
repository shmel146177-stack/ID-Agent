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


def test_project_package_manifest_keeps_unmatched_quality_documents_incomplete(
    tmp_path,
):
    package = ProjectPackage()

    project_name = "TEST_PROJECT"
    destination_folder = tmp_path / "executive_docs"
    destination_folder.mkdir(parents=True)

    processor_result = {
        "status": "\u0413\u043e\u0442\u043e\u0432\u043e",
        "completeness": {},
        "hidden_works_acts": {},
        "supporting_documents": {},
    }

    document_set_result = {
        "sections_count": 1,
        "sections_with_files": 1,
        "actual_files_count": 2,
        "sections": [
            {
                "number": "06",
                "code": "quality_documents",
                "title": "\u041f\u0430\u0441\u043f\u043e\u0440\u0442\u0430 \u0438 \u0441\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u044b",
                "status": "\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442",
                "path": destination_folder / "06_quality_documents",
                "actual_files_count": 2,
                "actual_files": [
                    {
                        "name": "\u043f\u0430\u0441\u043f\u043e\u0440\u0442.pdf",
                        "relative_path": "\u043f\u0430\u0441\u043f\u043e\u0440\u0442.pdf",
                        "extension": ".pdf",
                        "size_bytes": 100,
                    },
                    {
                        "name": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442.pdf",
                        "relative_path": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442.pdf",
                        "extension": ".pdf",
                        "size_bytes": 100,
                    },
                ],
                "detected": {
                    "required_count": 3,
                    "found_count": 0,
                    "missing_count": 3,
                    "high_priority_count": 2,
                    "documents": [],
                },
            },
        ],
    }

    manifest_path = package._create_manifest(
        project_name,
        destination_folder,
        processor_result,
        document_set_result,
        {"files": [], "folders": []},
        [],
    )

    manifest = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )

    section = manifest["document_sections"][0]

    assert section["actual_files_count"] == 2
    assert section["required_count"] == 3
    assert section["found_count"] == 0
    assert section["missing_count"] == 3
    assert section["status"] == "\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442"


def test_project_package_manifest_keeps_matching_quality_section_complete(
    tmp_path,
):
    package = ProjectPackage()

    project_name = "TEST_PROJECT"
    destination_folder = tmp_path / "executive_docs"
    destination_folder.mkdir(parents=True)

    processor_result = {
        "status": "\u0413\u043e\u0442\u043e\u0432\u043e",
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
                "number": "06",
                "code": "quality_documents",
                "title": "\u041f\u0430\u0441\u043f\u043e\u0440\u0442\u0430 \u0438 \u0441\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u044b",
                "status": "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442 \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d",
                "path": destination_folder / "06_quality_documents",
                "actual_files_count": 1,
                "actual_files": [
                    {
                        "name": "cable_certificate.pdf",
                        "relative_path": "cable_certificate.pdf",
                        "extension": ".pdf",
                        "size_bytes": 100,
                    },
                ],
                "detected": {
                    "required_count": 1,
                    "found_count": 1,
                    "missing_count": 0,
                    "high_priority_count": 1,
                    "documents": [
                        {
                            "code": "cable_quality_documents",
                        },
                    ],
                },
            },
        ],
    }

    manifest_path = package._create_manifest(
        project_name,
        destination_folder,
        processor_result,
        document_set_result,
        {"files": [], "folders": []},
        [],
    )

    manifest = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )

    section = manifest["document_sections"][0]

    assert section["code"] == "quality_documents"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 1
    assert section["missing_count"] == 0
    assert section["status"] == "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442 \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d"


def test_project_package_manifest_keeps_matching_cable_protocol_section_complete(
    tmp_path,
):
    package = ProjectPackage()

    project_name = "TEST_PROJECT"
    destination_folder = tmp_path / "executive_docs"
    destination_folder.mkdir(parents=True)

    processor_result = {
        "status": "\u0413\u043e\u0442\u043e\u0432\u043e",
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
                "number": "05",
                "code": "tests",
                "title": "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\u044b \u0438 \u0438\u0441\u043f\u044b\u0442\u0430\u043d\u0438\u044f",
                "status": "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442 \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d",
                "path": destination_folder / "05_tests",
                "actual_files_count": 1,
                "actual_files": [
                    {
                        "name": "cable_protocol.pdf",
                        "relative_path": "cable_protocol.pdf",
                        "extension": ".pdf",
                        "size_bytes": 100,
                    },
                ],
                "detected": {
                    "required_count": 1,
                    "found_count": 1,
                    "missing_count": 0,
                    "high_priority_count": 0,
                    "documents": [
                        {
                            "code": "cable_test_protocol",
                        },
                    ],
                },
            },
        ],
    }

    manifest_path = package._create_manifest(
        project_name,
        destination_folder,
        processor_result,
        document_set_result,
        {"files": [], "folders": []},
        [],
    )

    manifest = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )

    section = manifest["document_sections"][0]

    assert section["code"] == "tests"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 1
    assert section["missing_count"] == 0
    assert section["status"] == "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442 \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d"


def test_project_package_manifest_keeps_wrong_cable_protocol_section_incomplete(
    tmp_path,
):
    package = ProjectPackage()

    project_name = "TEST_PROJECT"
    destination_folder = tmp_path / "executive_docs"
    destination_folder.mkdir(parents=True)

    processor_result = {
        "status": "\u0413\u043e\u0442\u043e\u0432\u043e",
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
                "number": "05",
                "code": "tests",
                "title": "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\u044b \u0438 \u0438\u0441\u043f\u044b\u0442\u0430\u043d\u0438\u044f",
                "status": "\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442",
                "path": destination_folder / "05_tests",
                "actual_files_count": 1,
                "actual_files": [
                    {
                        "name": "grounding_protocol.pdf",
                        "relative_path": "grounding_protocol.pdf",
                        "extension": ".pdf",
                        "size_bytes": 100,
                    },
                ],
                "detected": {
                    "required_count": 1,
                    "found_count": 0,
                    "missing_count": 1,
                    "high_priority_count": 0,
                    "documents": [
                        {
                            "code": "cable_test_protocol",
                        },
                    ],
                },
            },
        ],
    }

    manifest_path = package._create_manifest(
        project_name,
        destination_folder,
        processor_result,
        document_set_result,
        {"files": [], "folders": []},
        [],
    )

    manifest = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )

    section = manifest["document_sections"][0]

    assert section["code"] == "tests"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 0
    assert section["missing_count"] == 1
    assert section["status"] == "\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442"


def test_project_package_manifest_keeps_matching_cable_entry_scheme_complete(
    tmp_path,
):
    package = ProjectPackage()

    project_name = "TEST_PROJECT"
    destination_folder = tmp_path / "executive_docs"
    destination_folder.mkdir(parents=True)

    processor_result = {
        "status": "\u0413\u043e\u0442\u043e\u0432\u043e",
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
                "title": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0441\u0445\u0435\u043c\u044b",
                "status": "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442 \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d",
                "path": destination_folder / "04_executive_schemes",
                "actual_files_count": 1,
                "actual_files": [
                    {
                        "name": "cable_entry_scheme.pdf",
                        "relative_path": "cable_entry_scheme.pdf",
                        "extension": ".pdf",
                        "size_bytes": 100,
                    },
                ],
                "detected": {
                    "required_count": 1,
                    "found_count": 1,
                    "missing_count": 0,
                    "high_priority_count": 1,
                    "documents": [
                        {
                            "code": "cable_entry_executive_scheme",
                        },
                    ],
                },
            },
        ],
    }

    manifest_path = package._create_manifest(
        project_name,
        destination_folder,
        processor_result,
        document_set_result,
        {"files": [], "folders": []},
        [],
    )

    manifest = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )

    section = manifest["document_sections"][0]

    assert section["code"] == "executive_schemes"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 1
    assert section["missing_count"] == 0
    assert section["status"] == "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442 \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d"


def test_project_package_manifest_keeps_wrong_cable_entry_scheme_incomplete(
    tmp_path,
):
    package = ProjectPackage()

    project_name = "TEST_PROJECT"
    destination_folder = tmp_path / "executive_docs"
    destination_folder.mkdir(parents=True)

    processor_result = {
        "status": "\u0413\u043e\u0442\u043e\u0432\u043e",
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
                "title": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0441\u0445\u0435\u043c\u044b",
                "status": "\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442",
                "path": destination_folder / "04_executive_schemes",
                "actual_files_count": 1,
                "actual_files": [
                    {
                        "name": "grounding_scheme.pdf",
                        "relative_path": "grounding_scheme.pdf",
                        "extension": ".pdf",
                        "size_bytes": 100,
                    },
                ],
                "detected": {
                    "required_count": 1,
                    "found_count": 0,
                    "missing_count": 1,
                    "high_priority_count": 1,
                    "documents": [
                        {
                            "code": "cable_entry_executive_scheme",
                        },
                    ],
                },
            },
        ],
    }

    manifest_path = package._create_manifest(
        project_name,
        destination_folder,
        processor_result,
        document_set_result,
        {"files": [], "folders": []},
        [],
    )

    manifest = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )

    section = manifest["document_sections"][0]

    assert section["code"] == "executive_schemes"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 0
    assert section["missing_count"] == 1
    assert section["status"] == "\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442"


def test_project_package_manifest_keeps_matching_supports_scheme_complete(
    tmp_path,
):
    package = ProjectPackage()

    project_name = "TEST_PROJECT"
    destination_folder = tmp_path / "executive_docs"
    destination_folder.mkdir(parents=True)

    processor_result = {
        "status": "\u0413\u043e\u0442\u043e\u0432\u043e",
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
                "title": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0441\u0445\u0435\u043c\u044b",
                "status": "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442 \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d",
                "path": destination_folder / "04_executive_schemes",
                "actual_files_count": 1,
                "actual_files": [
                    {
                        "name": "supports_scheme.pdf",
                        "relative_path": "supports_scheme.pdf",
                        "extension": ".pdf",
                        "size_bytes": 100,
                    },
                ],
                "detected": {
                    "required_count": 1,
                    "found_count": 1,
                    "missing_count": 0,
                    "high_priority_count": 0,
                    "documents": [
                        {
                            "code": "supports_executive_scheme",
                        },
                    ],
                },
            },
        ],
    }

    manifest_path = package._create_manifest(
        project_name,
        destination_folder,
        processor_result,
        document_set_result,
        {"files": [], "folders": []},
        [],
    )

    manifest = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )

    section = manifest["document_sections"][0]

    assert section["code"] == "executive_schemes"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 1
    assert section["missing_count"] == 0
    assert section["status"] == "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442 \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d"


def test_project_package_manifest_keeps_wrong_supports_scheme_incomplete(
    tmp_path,
):
    package = ProjectPackage()

    project_name = "TEST_PROJECT"
    destination_folder = tmp_path / "executive_docs"
    destination_folder.mkdir(parents=True)

    processor_result = {
        "status": "\u0413\u043e\u0442\u043e\u0432\u043e",
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
                "title": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0441\u0445\u0435\u043c\u044b",
                "status": "\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442",
                "path": destination_folder / "04_executive_schemes",
                "actual_files_count": 1,
                "actual_files": [
                    {
                        "name": "cable_entry_scheme.pdf",
                        "relative_path": "cable_entry_scheme.pdf",
                        "extension": ".pdf",
                        "size_bytes": 100,
                    },
                ],
                "detected": {
                    "required_count": 1,
                    "found_count": 0,
                    "missing_count": 1,
                    "high_priority_count": 0,
                    "documents": [
                        {
                            "code": "supports_executive_scheme",
                        },
                    ],
                },
            },
        ],
    }

    manifest_path = package._create_manifest(
        project_name,
        destination_folder,
        processor_result,
        document_set_result,
        {"files": [], "folders": []},
        [],
    )

    manifest = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )

    section = manifest["document_sections"][0]

    assert section["code"] == "executive_schemes"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 0
    assert section["missing_count"] == 1
    assert section["status"] == "\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442"


def test_project_package_manifest_keeps_matching_grounding_scheme_complete(
    tmp_path,
):
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
                "status": "Комплект сформирован",
                "path": destination_folder / "04_executive_schemes",
                "actual_files_count": 1,
                "actual_files": [
                    {
                        "name": "grounding_scheme.pdf",
                        "relative_path": "grounding_scheme.pdf",
                        "extension": ".pdf",
                        "size_bytes": 100,
                    },
                ],
                "detected": {
                    "required_count": 1,
                    "found_count": 1,
                    "missing_count": 0,
                    "high_priority_count": 1,
                    "documents": [
                        {
                            "code": "grounding_executive_scheme",
                        },
                    ],
                },
            },
        ],
    }

    manifest_path = package._create_manifest(
        project_name,
        destination_folder,
        processor_result,
        document_set_result,
        {"files": [], "folders": []},
        [],
    )

    manifest = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )

    section = manifest["document_sections"][0]

    assert section["code"] == "executive_schemes"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 1
    assert section["missing_count"] == 0
    assert section["status"] == "Комплект сформирован"


def test_project_package_manifest_keeps_wrong_grounding_scheme_incomplete(
    tmp_path,
):
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
                "path": destination_folder / "04_executive_schemes",
                "actual_files_count": 1,
                "actual_files": [
                    {
                        "name": "cable_entry_scheme.pdf",
                        "relative_path": "cable_entry_scheme.pdf",
                        "extension": ".pdf",
                        "size_bytes": 100,
                    },
                ],
                "detected": {
                    "required_count": 1,
                    "found_count": 0,
                    "missing_count": 1,
                    "high_priority_count": 1,
                    "documents": [
                        {
                            "code": "grounding_executive_scheme",
                        },
                    ],
                },
            },
        ],
    }

    manifest_path = package._create_manifest(
        project_name,
        destination_folder,
        processor_result,
        document_set_result,
        {"files": [], "folders": []},
        [],
    )

    manifest = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )

    section = manifest["document_sections"][0]

    assert section["code"] == "executive_schemes"
    assert section["actual_files_count"] == 1
    assert section["required_count"] == 1
    assert section["found_count"] == 0
    assert section["missing_count"] == 1
    assert section["status"] == "Неполный комплект"
