import pytest
from fastapi import HTTPException

import app.api.project_processor as api_module


def test_project_api_hidden_works_registry_success_and_not_found(monkeypatch):

    project_name = "TEST_PROJECT"

    expected = {
        "project": project_name,
        "acts_count": 2,
        "acts": [
            {"act_code": "grounding_device"},
            {"act_code": "cable_entry"},
        ],
    }

    monkeypatch.setattr(
        api_module.hidden_works_registry,
        "analyze_project",
        lambda name: expected,
    )

    result = api_module.get_hidden_works_registry(
        project_name
    )

    assert result == expected
    assert result["acts_count"] == 2

    def raise_not_found(name):
        raise FileNotFoundError(
            f"Проект не найден: {name}"
        )

    monkeypatch.setattr(
        api_module.hidden_works_registry,
        "analyze_project",
        raise_not_found,
    )

    with pytest.raises(HTTPException) as error:
        api_module.get_hidden_works_registry(
            project_name
        )

    assert error.value.status_code == 404
    assert project_name in error.value.detail
