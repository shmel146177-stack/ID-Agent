import pytest
from fastapi import HTTPException

import app.api.project_processor as api_module


def test_project_api_create_project_duplicate_returns_400(
    monkeypatch,
):

    project_name = "TEST_PROJECT"

    def raise_duplicate(name):
        raise ValueError(
            f"Проект уже существует: {name}"
        )

    monkeypatch.setattr(
        api_module.project_manager,
        "create_project",
        raise_duplicate,
    )

    data = api_module.ProjectCreate(
        project_name=project_name,
    )

    with pytest.raises(HTTPException) as error:
        api_module.create_project(data)

    assert error.value.status_code == 400
    assert project_name in error.value.detail
