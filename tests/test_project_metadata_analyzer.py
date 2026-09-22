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


def test_project_metadata_analyzer_extracts_working_document_title_page():
    analyzer = ProjectMetadataAnalyzer()
    text = """
Общество с ограниченной ответственностью
«Альянс Энерго Групп»
Заказчик — АО «Мособлэнерго»
ТЗ №11240/24 от 24.01.2024г.

Строительство БКТП 6/0,4 кВ с тр-ми 2х400 кВА взамен ТП-737,
Московская область, г. Подольск, мкр. Климовск, ул. Коммунальная (0,8 МВА)

РАБОЧАЯ ДОКУМЕНТАЦИЯ
Основной комплект рабочих чертежей
"""
    result = analyzer.analyze_text(text)
    assert result["customer"] == "АО «Мособлэнерго»"
    assert result["designer"] == "ООО «Альянс Энерго Групп»"
    assert result["object_name"].startswith("Строительство БКТП")
    assert result["address"] == (
        "Московская область, г. Подольск, мкр. Климовск, ул. Коммунальная"
    )
