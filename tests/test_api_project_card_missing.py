import pytest
from fastapi import HTTPException

import app.api.project_processor as api_module


def test_project_api_update_card_missing_project_returns_404(
    monkeypatch,
):

    project_name = "MISSING_PROJECT"

    def raise_not_found(name, data):
        raise FileNotFoundError(
            f"Проект не найден: {name}"
        )

    monkeypatch.setattr(
        api_module.project_manager,
        "update_project",
        raise_not_found,
    )

    card = api_module.ProjectCardUpdate(
        object_name="ТП-101",
        address="Москва",
    )

    with pytest.raises(HTTPException) as error:
        api_module.update_project_card(
            project_name,
            card,
        )

    assert error.value.status_code == 404
    assert project_name in error.value.detail
