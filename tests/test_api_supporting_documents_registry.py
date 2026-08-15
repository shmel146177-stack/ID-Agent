import pytest
from fastapi import HTTPException

import app.api.project_processor as api_module


def test_project_api_supporting_documents_registry_success_and_not_found(monkeypatch):

    project_name = "TEST_PROJECT"

    expected = {
        "project": project_name,
        "requirements_count": 2,
        "requirements": [
            {"code": "grounding_executive_scheme"},
            {"code": "grounding_resistance_protocol"},
        ],
    }

    monkeypatch.setattr(
        api_module.supporting_documents_registry,
        "analyze_project",
        lambda name: expected,
    )

    result = api_module.get_supporting_documents_registry(
        project_name
    )

    assert result == expected
    assert result["requirements_count"] == 2

    def raise_not_found(name):
        raise FileNotFoundError(
            f"Проект не найден: {name}"
        )

    monkeypatch.setattr(
        api_module.supporting_documents_registry,
        "analyze_project",
        raise_not_found,
    )

    with pytest.raises(HTTPException) as error:
        api_module.get_supporting_documents_registry(
            project_name
        )

    assert error.value.status_code == 404
    assert project_name in error.value.detail
