from app.models.project_card import ProjectCard


def test_project_card_model_defaults_and_values():

    empty_card = ProjectCard()

    assert empty_card.project_name == ""
    assert empty_card.project_mode == "production"
    assert empty_card.project_note == ""
    assert empty_card.object_name == ""
    assert empty_card.address == ""
    assert empty_card.customer == ""
    assert empty_card.contractor == ""
    assert empty_card.designer == ""
    assert empty_card.contract_number == ""
    assert empty_card.start_date == ""
    assert empty_card.finish_date == ""
    assert empty_card.chief_engineer == ""

    card = ProjectCard(
        project_name="TEST_PROJECT",
        project_mode="training",
        project_note="Используется для разработки ИИ-Агента",
        object_name="ТП-101",
        address="Москва, ул. Тестовая, д. 10",
        customer="ООО Заказчик",
        contractor="ООО Подрядчик",
        designer="ООО ПроектСтрой",
        contract_number="DOG-001",
        start_date="01.08.2026",
        finish_date="31.08.2026",
        chief_engineer="Иванов И.И.",
    )

    assert card.project_name == "TEST_PROJECT"
    assert card.project_mode == "training"
    assert card.project_note == "Используется для разработки ИИ-Агента"
    assert card.object_name == "ТП-101"
    assert card.address == "Москва, ул. Тестовая, д. 10"
    assert card.customer == "ООО Заказчик"
    assert card.contractor == "ООО Подрядчик"
    assert card.designer == "ООО ПроектСтрой"
    assert card.contract_number == "DOG-001"
    assert card.start_date == "01.08.2026"
    assert card.finish_date == "31.08.2026"
    assert card.chief_engineer == "Иванов И.И."
