from app.services.document_completeness import DocumentCompleteness


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
