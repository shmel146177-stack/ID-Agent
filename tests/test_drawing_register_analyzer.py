from app.services.drawing_register_analyzer import DrawingRegisterAnalyzer


def test_drawing_register_analyzer_restores_sheet_sequence():

    analyzer = DrawingRegisterAnalyzer()

    text = """
Ведомость рабочих чертежей основного комплекта

Общие данные
1
План строительства линий
2
Структурная схема электроснабжения
3
Устройство очага заземления
4
Узел ввода кабельной линии
5
Чертеж ограждения
6
"""

    result = analyzer.analyze_text(text)

    assert result["register_detected"] is True
    assert result["register_block_detected"] is True

    assert result["entries_count"] == 6
    assert result["numbered_entries_count"] == 6

    assert result["numbering_restored"] is True
    assert result["expected_sheet_count"] == 6

    assert result["number_evidence"] == [
        1,
        2,
        3,
        4,
        5,
        6,
    ]

    assert [
        entry["sheet_number"]
        for entry in result["entries"]
    ] == [
        1,
        2,
        3,
        4,
        5,
        6,
    ]

    assert all(
        entry["number_source"] == "restored_sequence"
        for entry in result["entries"]
    )

    assert result["entries"][0]["title"] == "Общие данные"

    assert result["entries"][2]["title"] == (
        "Структурная схема электроснабжения"
    )

    assert result["entries"][5]["title"] == "Чертеж ограждения"


def test_drawing_register_analyzer_reads_numbered_visual_ocr_rows():

    analyzer = DrawingRegisterAnalyzer()

    text = """
Ведомость рабочих чертежей основного комплекта
Стр. Наименование Примечание
1 Общие данные
2 Ситуационный план
3 План строительства Воздушных линио М1:500
4 Узел ввода кабельной линии
5 Общий вид временных опор
6 Структурная схема электроснабжения
7 Компановка ВРЩ-0,4кВ аё-та
8 Чзел монтажа ВРЩ-0,4кВ аб-та
9 Однолинебйная схема ВРЩ-0,4кВ территори
10 Компановка ВРЩ-0,4кВ территории
11 Чзел монтажа ВРЩ-0,4кВ территории
12 Чзел заземления ВРЩ-0,4кВ
13 Устройство очага заземления
14 Чертеж ограждения
"""

    result = analyzer.analyze_text(text)

    assert result["register_block_detected"] is True
    assert result["entries_count"] == 14
    assert result["numbering_restored"] is True
    assert result["expected_sheet_count"] == 14

    assert [
        entry["sheet_number"]
        for entry in result["entries"]
    ] == list(range(1, 15))

    assert result["entries"][1]["title"] == "Ситуационный план"
    assert result["entries"][7]["title"] == (
        "Узел монтажа ВРЩ-0,4кВ абонента"
    )


def test_drawing_register_analyzer_can_read_visual_titles_without_numbers():

    analyzer = DrawingRegisterAnalyzer()

    text = """
Ведомость рабочих чертежей основного комплекта
Общие данные
Ситуационный план
План строительства воздушных линио М1:500
Узел ввода кабельной линии
Общий вид временных опор
Структурная схема электроснабжения
Компанобка ВРЩ-0,4кВ аё-та
Чзел монтажа ВРЩ-0,4кВ аё-та
Однолинейная схема ВРЩ-0,4кВ территори
Компановка ВРЩ-0,4кВ территории
Узел монтажа ВРЩ-0,4кВ территории
Чзел заземления ВРЩ-0,4кВ
Устройство очага заземления
Чертеж ограждения
"""

    result = analyzer.analyze_text(
        text,
        allow_title_only=True,
    )

    assert result["entries_count"] == 14
    assert result["numbering_restored"] is False
    assert result["entries"][6]["title"] == (
        "Компоновка ВРЩ-0,4кВ абонента"
    )
    assert result["entries"][7]["title"] == (
        "Узел монтажа ВРЩ-0,4кВ абонента"
    )
