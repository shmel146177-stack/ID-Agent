from app.services.page_analyzer import PageAnalyzer


def test_page_analyzer_priority_ocr_and_unknown():

    analyzer = PageAnalyzer()

    # ---------------------------------------------------------
    # 1. Пустая страница -> требуется OCR
    # ---------------------------------------------------------

    empty_result = analyzer.analyze_page(
        "",
        page_number=1,
    )

    assert empty_result["page"] == 1
    assert empty_result["page_type"] == "Требуется OCR"
    assert empty_result["score"] == 0
    assert empty_result["text_length"] == 0
    assert empty_result["preview"] == ""

    # ---------------------------------------------------------
    # 2. Приоритетный заголовок должен победить
    #    другие признаки на той же странице
    # ---------------------------------------------------------

    priority_text = """
Ведомость рабочих чертежей
Однолинейная схема электроснабжения
Контур заземления
"""

    priority_result = analyzer.analyze_page(
        priority_text,
        page_number=2,
    )

    assert priority_result["page"] == 2
    assert (
        priority_result["page_type"]
        == "Ведомость рабочих чертежей"
    )
    assert priority_result["score"] == 100
    assert priority_result["text_length"] == len(priority_text)
    assert priority_result["preview"]

    # ---------------------------------------------------------
    # 3. Отдельный признак заземления
    # ---------------------------------------------------------

    grounding_result = analyzer.analyze_page(
        "Рабочий чертеж. Контур заземления здания.",
        page_number=5,
    )

    assert grounding_result["page_type"] == "Заземление"
    assert grounding_result["score"] == 100

    # ---------------------------------------------------------
    # 4. Текст без известных признаков
    # ---------------------------------------------------------

    unknown_result = analyzer.analyze_page(
        "Совершенно неизвестный текст без проектных признаков.",
        page_number=10,
    )

    assert unknown_result["page_type"] == "Не определено"
    assert unknown_result["score"] < 5
