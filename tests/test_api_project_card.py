import app.api.project_processor as api_module


def test_project_api_gets_and_updates_project_card(monkeypatch):

    project_name = "TEST_PROJECT"

    existing_card = {
        "project_name": project_name,
        "object_name": "ТП-101",
        "address": "Москва",
    }

    monkeypatch.setattr(
        api_module.project_manager,
        "get_project",
        lambda name: existing_card,
    )

    result = api_module.get_project_card(
        project_name
    )

    assert result == existing_card
    assert result["object_name"] == "ТП-101"

    updated_card = {
        "project_name": project_name,
        "object_name": "ТП-202",
        "address": "Москва, ул. Тестовая",
    }

    received = {}

    def fake_update(name, data):
        received["name"] = name
        received["data"] = data
        return updated_card

    monkeypatch.setattr(
        api_module.project_manager,
        "update_project",
        fake_update,
    )

    card = api_module.ProjectCardUpdate(
        project_mode="training",
        project_note="Для разработки ИИ-Агента",
        object_name="ТП-202",
        address="Москва, ул. Тестовая",
        customer="ООО Заказчик",
    )

    update_result = api_module.update_project_card(
        project_name,
        card,
    )

    assert update_result == updated_card
    assert received["name"] == project_name
    assert received["data"]["object_name"] == "ТП-202"
    assert received["data"]["customer"] == "ООО Заказчик"
    assert received["data"]["project_mode"] == "training"
    assert received["data"]["project_note"] == "Для разработки ИИ-Агента"
