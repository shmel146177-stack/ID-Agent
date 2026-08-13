from app.services.project_metadata_analyzer import ProjectMetadataAnalyzer


def test_project_metadata_analyzer_extracts_project_fields():

    analyzer = ProjectMetadataAnalyzer()

    text = """
Организация заказчика: ООО Заказчик
Проектная организация: ООО "ПроектСтрой"
Главный инженер проекта Иванов И.И.
Адрес работ: г. Москва, ул. Тестовая, д. 10
Наименование объекта: Строительство трансформаторной подстанции ТП-101
"""

    result = analyzer.analyze_text(text)

    assert result["object_name"] == (
        "Строительство трансформаторной подстанции ТП-101"
    )

    assert result["customer"] == "ООО Заказчик"

    assert result["designer"] == 'ООО "ПроектСтрой"'

    assert result["chief_engineer"] == "Иванов И.И."

    assert result["address"] == (
        "г. Москва, ул. Тестовая, д. 10"
    )

    # Эти поля пока заявлены в структуре результата,
    # но текущий анализатор их ещё не извлекает.
    assert result["contractor"] is None
    assert result["contract_number"] is None
