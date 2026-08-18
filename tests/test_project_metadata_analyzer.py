from app.services.project_metadata_analyzer import ProjectMetadataAnalyzer


def test_project_metadata_analyzer_extracts_project_fields():

    analyzer = ProjectMetadataAnalyzer()

    text = """
Организация заказчика: ООО Заказчик
Генеральный подрядчик: ООО "МонтажСтрой"
Договор подряда № 15/ТП-2026 от 01.08.2026
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

    assert result["contractor"] == 'ООО "МонтажСтрой"'
    assert result["contract_number"] == "15/ТП-2026"
