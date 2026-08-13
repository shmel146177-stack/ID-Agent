from pathlib import Path

from fastapi.responses import FileResponse

import app.api.generator as generator_api


def test_api_generator_handles_missing_data_and_returns_file(monkeypatch, tmp_path):

    monkeypatch.setattr(
        generator_api.project_service,
        "get_analysis",
        lambda: None,
    )

    result = generator_api.generate_document()

    assert isinstance(result, dict)
    assert "status" in result

    analysis = {
        "equipment": "Шкаф управления TEST-001",
        "manufacturer": "ООО Тест",
        "drawing_number": "TEST-001",
    }

    output_file = tmp_path / "generated.docx"
    output_file.write_bytes(b"TEST DOCX")

    monkeypatch.setattr(
        generator_api.project_service,
        "get_analysis",
        lambda: analysis,
    )

    received = {}

    def fake_create(data):
        received.update(data)
        return str(output_file)

    monkeypatch.setattr(
        generator_api.executive_generator_v3,
        "create",
        fake_create,
    )

    response = generator_api.generate_document()

    assert isinstance(response, FileResponse)
    assert Path(response.path) == output_file

    assert response.media_type == (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    )

    assert received == analysis
