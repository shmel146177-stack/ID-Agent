import pytest

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

    assert result["object_name"] == ("Строительство трансформаторной подстанции ТП-101")

    assert result["customer"] == "ООО Заказчик"

    assert result["designer"] == 'ООО "ПроектСтрой"'

    assert result["chief_engineer"] == "Иванов И.И."

    assert result["address"] == ("г. Москва, ул. Тестовая, д. 10")

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


def test_project_metadata_analyzer_uses_stamp_values_before_labels():
    text = """Строительство новой трансформаторной подстанции ТП-101
Наименование объекта
АО «Заказчик»
Заказчик
г. Москва, улица Центральная, дом 10
Местоположение (адрес) объекта
Проектная организация: ИП Иванов И.И.
"""

    result = ProjectMetadataAnalyzer().analyze_text(text)

    assert (
        result["object_name"]
        == "Строительство новой трансформаторной подстанции ТП-101"
    )
    assert result["customer"] == "АО «Заказчик»"
    assert result["address"] == "г. Москва, улица Центральная, дом 10"
    assert result["designer"] == "ИП Иванов И.И."


def test_project_metadata_analyzer_prefers_title_page_values():
    text = """Общество с ограниченной ответственностью «Первый проект»
Заказчик — АО «Первый заказчик»
Строительство новой подстанции ТП-101 в Московской области
РАБОЧАЯ ДОКУМЕНТАЦИЯ
Строительство другого объекта
Наименование объекта
АО «Другой заказчик»
Заказчик
Проектная организация: ООО "Другой проект"
"""

    result = ProjectMetadataAnalyzer().analyze_text(text)

    assert (
        result["object_name"]
        == "Строительство новой подстанции ТП-101 в Московской области"
    )
    assert result["customer"] == "АО «Первый заказчик»"
    assert result["designer"] == "ООО «Первый проект»"


def test_project_metadata_analyzer_returns_empty_fields_for_unrecognized_text():
    result = ProjectMetadataAnalyzer().analyze_text("Текст без реквизитов")

    assert result == {
        "object_name": None,
        "address": None,
        "customer": None,
        "contractor": None,
        "designer": None,
        "chief_engineer": None,
        "contract_number": None,
    }


@pytest.mark.parametrize(
    "label",
    [
        "Генеральный подрядчик",
        "Подрядная организация",
        "Организация подрядчика",
        "Подрядчик",
    ],
)
def test_project_metadata_analyzer_accepts_contractor_labels(label):
    result = ProjectMetadataAnalyzer().analyze_text(f'{label}: ООО "Строй"')

    assert result["contractor"] == 'ООО "Строй"'


@pytest.mark.parametrize(
    "line",
    [
        "Договор подряда № 15/ТП-2026",
        "Контракт N 15/ТП-2026",
        "Договор No. 15/ТП-2026",
    ],
)
def test_project_metadata_analyzer_accepts_contract_markers(line):
    result = ProjectMetadataAnalyzer().analyze_text(line)

    assert result["contract_number"] == "15/ТП-2026"


def test_project_metadata_analyzer_reads_multiline_stamp_name():
    text = (
        "Наименование объекта: Строительство новой трансформаторной подстанции\n"
        "в микрорайоне Южный\n"
    )

    result = ProjectMetadataAnalyzer().analyze_text(text)

    assert result["object_name"] == (
        "Строительство новой трансформаторной подстанции в микрорайоне Южный"
    )
