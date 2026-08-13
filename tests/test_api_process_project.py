import pytest
from fastapi import HTTPException

import app.api.project_processor as api_module


def test_project_api_process_project_success_and_not_found(monkeypatch):

    project_name = "TEST_PROJECT"

    expected = {
        "project": project_name,
        "status": "Готово",
    }

    monkeypatch.setattr(
        api_module.project_processor,
        "process",
        lambda name: expected,
    )

    result = api_module.process_project(
        project_name
    )

    assert result == expected

    def raise_not_found(name):
        raise FileNotFoundError(
            f"Проект не найден: {name}"
        )

    monkeypatch.setattr(
        api_module.project_processor,
        "process",
        raise_not_found,
    )

    with pytest.raises(HTTPException) as error:
        api_module.process_project(
            project_name
        )

    assert error.value.status_code == 404
    assert project_name in error.value.detail
