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


def test_drawing_title_block_is_not_approval():
    analyzer = PageAnalyzer()
    stamp = "Согласовано\nСтадия Р\nЛист 1\nРазработал\nПроверил\nПодпись Дата"
    cases = {
        "План выноса КЛ-6 кВ из пятна застройки": "План электроснабжения",
        "План на отм. 0.000": "Рабочий чертеж",
        "Общие данные. Ссылочные документы. Технические условия. Ситуационный план": "Общие данные",
        "Ведомость рабочих чертежей. Общие данные. Контур заземления": "Ведомость рабочих чертежей",
    }
    for title, expected in cases.items():
        assert analyzer.analyze_page(stamp + "\n" + title, 30)["page_type"] == expected


def test_real_approval_without_drawing_stamp_is_preserved():
    analyzer = PageAnalyzer()
    assert analyzer.analyze_page("Лист согласования к ТЗ. Согласовано начальником", 8)["page_type"] == "Согласование"
    assert analyzer.analyze_page("Технические условия на присоединение", 9)["page_type"] == "Технические условия"


def test_review_pages_are_classified_by_stable_markers():
    analyzer = PageAnalyzer()
    cases = [
        ("РАЗРЕШЕНИЕ на размещение объекта № 123", "Разрешение на размещение"),
        ("Схема границ на выдачу разрешения на размещение", "Схема границ"),
        ("Выписка из реестра членов СРО", "Документы СРО"),
        (
            "Сведения об обязательствах по договорам строительного подряда",
            "Документы СРО",
        ),
        (
            "Технические решения должны соответствовать требованиям ПУЭ и ГОСТ",
            "Техническое задание",
        ),
        ("План длагоустройства. М1:500", "План благоустройства"),
        (
            "Восстановление газона по ширине траншеи",
            "План благоустройства",
        ),
        ("11240/24-ЭП.ВОР Лист 2", "Ведомость объемов работ"),
        (
            "Ведомость документов основного комплекта рабочих чертежей марки АС",
            "Ведомость рабочих чертежей",
        ),
        ("Согласовано ТЕПЛОСЕТЬ", "Согласование"),
    ]

    for text, expected_type in cases:
        assert analyzer.analyze_page(text)["page_type"] == expected_type

    drawing_register = (
        "Стадия Р Лист 1 Разработал Проверил Подпись Инв. "
        "Общие данные. Ведомость документов основного комплекта рабочих чертежей"
    )
    assert analyzer.analyze_page(drawing_register)["page_type"] == (
        "Ведомость рабочих чертежей"
    )
