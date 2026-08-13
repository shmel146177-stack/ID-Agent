import json
from pathlib import Path

from app.services.project_service import ProjectService


def test_project_service_saves_and_loads_analysis(monkeypatch, tmp_path):

    service = ProjectService()

    monkeypatch.chdir(tmp_path)

    service.file_path = "projects/data/current_analysis.json"

    data = {
        "project": "TEST_PROJECT",
        "status": "Готово",
        "documents_count": 2,
        "documents": [
            {
                "filename": "drawing.pdf",
                "classification": "Чертеж",
            },
            {
                "filename": "passport.pdf",
                "classification": "Паспорт оборудования",
            },
        ],
    }

    save_result = service.save_analysis(data)

    assert save_result["document"] == data
    assert "status" in save_result

    output_path = (
        tmp_path
        / "projects"
        / "data"
        / "current_analysis.json"
    )

    assert output_path.exists()
    assert output_path.is_file()

    saved = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert saved == data

    loaded = service.get_analysis()

    assert loaded == data
    assert loaded["project"] == "TEST_PROJECT"
    assert loaded["documents_count"] == 2
