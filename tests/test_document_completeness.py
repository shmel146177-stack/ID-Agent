from app.services.document_completeness import DocumentCompleteness
import app.services.document_completeness as completeness_module


def test_document_completeness_equipment_profile():
    completeness = DocumentCompleteness()

    required = list(
        completeness.EQUIPMENT_REQUIRED_DOCUMENTS
    )

    fake_registry = {
        "documents": [
            {"classification": required[0]},
            {"classification": required[1]},
        ]
    }

    completeness._get_registry = lambda project_name: fake_registry

    result = completeness.check(
        "TEST_PROJECT",
        profile="equipment",
    )

    assert result["project"] == "TEST_PROJECT"
    assert result["profile"] == "equipment"
    assert result["required_count"] == len(required)
    assert result["found_count"] == 2
    assert result["missing_count"] == len(required) - 2
    assert result["completeness_percent"] == round(
        2 / len(required) * 100,
        1,
    )
    assert len(result["documents"]) == len(required)


def test_project_completeness_is_unknown_without_drawing_register(monkeypatch):
    completeness = DocumentCompleteness()
    monkeypatch.setattr(
        completeness_module.drawing_sheet_matcher,
        "analyze_project",
        lambda name: {
            "status": "Ведомость рабочих чертежей не найдена",
            "determined": False,
            "expected_count": 0,
            "found_count": 0,
            "missing_count": 0,
            "completeness_percent": None,
            "matches": [],
            "missing_sheets": [],
            "output_path": "drawing_sheet_match.json",
        },
    )
    result = completeness.check("TEST_PROJECT", profile="project")
    assert result["status"] == "Комплектность не определена"
    assert result["determined"] is False
    assert result["completeness_percent"] is None
    assert result["missing_count"] == 0
