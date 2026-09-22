import json

from app.services.drawing_sheet_matcher import DrawingSheetMatcher


def test_designation_in_stamp_matches_changed_title():
    matcher = DrawingSheetMatcher()
    entry = {
        'title': 'Название из ведомости', 'designation': '11240/24-АС-Ч6',
        'register_filename': 'АС.pdf',
    }
    for suffix, found in [
        ('Заказчик: АО Заказчик 11240/24-АС-Ч6', True),
        ('11240/24-АС-Ч6', True),
        ('См. 11240/24-АС-Ч6', False),
        ('11240/24-АС-Ч60', False),
    ]:
        page = {
            'filename': 'АС.pdf', 'page': 32,
            'text': 'Лист Подпись Разработал\nДругое название\n' + suffix,
        }
        result = matcher._match_entry(entry, [page], set())
        assert result['found'] is found
        assert not matcher._match_entry(entry, [page], {('АС.pdf', 32)})['found']
        page['filename'] = 'ЭП.pdf'
        assert not matcher._match_entry(entry, [page], set())['found']


def test_drawing_sheet_matcher_matches_and_detects_missing(monkeypatch, tmp_path):

    matcher = DrawingSheetMatcher()

    drawing_register = {
        "registers": [
            {
                "page": 1,
                "entries": [
                    {
                        "sheet_number": 1,
                        "number_source": "register",
                        "title": "Структурная схема электроснабжения",
                    },
                    {
                        "sheet_number": 2,
                        "number_source": "register",
                        "title": "Чертеж ограждения",
                    },
                ],
            }
        ]
    }

    page_analysis = {
        "documents": [
            {
                "filename": "project.pdf",
                "pages": [
                    {
                        "page": 1,
                        "page_type": "Ведомость рабочих чертежей",
                        "source": "text",
                        "text": "Ведомость рабочих чертежей",
                        "preview": "",
                    },
                    {
                        "page": 2,
                        "page_type": "Электрическая схема",
                        "source": "text",
                        "text": "Структурная схема электроснабжения",
                        "preview": "",
                    },
                ],
            }
        ]
    }

    monkeypatch.setattr(
        matcher,
        "_load_register",
        lambda project_name: drawing_register,
    )

    monkeypatch.setattr(
        matcher,
        "_load_page_analysis",
        lambda project_name: page_analysis,
    )

    output_path = tmp_path / "drawing_sheet_match.json"

    monkeypatch.setattr(
        matcher,
        "_analysis_path",
        lambda project_name, filename: output_path,
    )

    result = matcher.analyze_project("TEST_PROJECT")

    assert result["project"] == "TEST_PROJECT"

    assert result["expected_count"] == 2
    assert result["found_count"] == 1
    assert result["missing_count"] == 1
    assert result["completeness_percent"] == 50.0

    assert result["register_pages"] == [1]

    first = result["matches"][0]

    assert first["sheet_number"] == 1
    assert first["found"] is True
    assert first["matched_page"] == 2
    assert first["matched_filename"] == "project.pdf"
    assert first["score"] >= matcher.MIN_MATCH_SCORE

    second = result["matches"][1]

    assert second["sheet_number"] == 2
    assert second["found"] is False
    assert second["matched_page"] is None

    assert len(result["missing_sheets"]) == 1
    assert result["missing_sheets"][0]["sheet_number"] == 2

    assert output_path.exists()

    saved = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert saved["found_count"] == 1
    assert saved["missing_count"] == 1


def test_register_entries_with_same_number_and_title_stay_separate_by_volume():
    matcher = DrawingSheetMatcher()
    drawing_register = {
        "registers": [
            {
                "filename": "АС.pdf",
                "entries": [
                    {"sheet_number": 1, "designation": "P-АС-Ч1", "title": "Общие данные"}
                ],
            },
            {
                "filename": "ЭП.pdf",
                "entries": [
                    {"sheet_number": 1, "designation": "P-ЭП-Ч1", "title": "Общие данные"}
                ],
            },
        ]
    }

    entries = matcher._collect_register_entries(drawing_register)

    assert len(entries) == 2
    assert {entry["register_filename"] for entry in entries} == {"АС.pdf", "ЭП.pdf"}
