import json

import app.services.drawing_register_service as service_module
from app.services.drawing_register_service import DrawingRegisterService


def test_drawing_register_service_builds_register(monkeypatch, tmp_path):

    service = DrawingRegisterService()

    page_type = "\u0412\u0435\u0434\u043e\u043c\u043e\u0441\u0442\u044c \u0440\u0430\u0431\u043e\u0447\u0438\u0445 \u0447\u0435\u0440\u0442\u0435\u0436\u0435\u0439"

    fake_page_analysis = {
        "documents": [
            {
                "filename": "project.pdf",
                "pages": [
                    {
                        "page": 2,
                        "page_type": page_type,
                        "text": "Тестовая ведомость",
                    }
                ],
            }
        ]
    }

    monkeypatch.setattr(
        service,
        "_load_page_analysis",
        lambda project_name: fake_page_analysis,
    )

    output_path = tmp_path / "drawing_register.json"

    monkeypatch.setattr(
        service,
        "_output_path",
        lambda project_name: output_path,
    )

    monkeypatch.setattr(
        service_module.drawing_register_analyzer,
        "analyze_text",
        lambda text: {
            "register_detected": True,
            "register_block_detected": True,
            "entries_count": 2,
            "numbered_entries_count": 2,
            "numbering_restored": False,
            "expected_sheet_count": 3,
            "number_evidence": [1, 2, 3],
            "entries": [
                {"sheet_number": "1"},
                {"sheet_number": "2"},
            ],
        },
    )

    result = service.analyze_project("TEST_PROJECT")

    assert result["project"] == "TEST_PROJECT"
    assert result["registers_count"] == 1
    assert result["entries_count"] == 2
    assert result["expected_sheet_count"] == 3

    register = result["registers"][0]

    assert register["filename"] == "project.pdf"
    assert register["page"] == 2
    assert register["register_detected"] is True
    assert register["entries_count"] == 2

    assert output_path.exists()

    saved = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert saved["registers_count"] == 1
    assert saved["entries_count"] == 2
