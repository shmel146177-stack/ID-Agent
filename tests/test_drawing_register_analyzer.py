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
