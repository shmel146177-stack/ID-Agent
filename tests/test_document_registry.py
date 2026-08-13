import json
from pathlib import Path

from app.services.document_registry import DocumentRegistry


def test_document_registry_builds_and_saves_json(monkeypatch, tmp_path):

    registry = DocumentRegistry()

    project_name = "TEST_PROJECT"

    project_path = (
        tmp_path
        / "projects"
        / project_name
    )

    analysis_path = project_path / "analysis"
    analysis_path.mkdir(parents=True)

    project_analysis = {
        "project": project_name,
        "documents": [
            {
                "filename": "drawing.pdf",
                "classification": "Чертеж",
                "status": "Готово",
                "extension": ".pdf",
                "analysis": {
                    "drawing_number": "TEST-001",
                    "date": "12.08.2026",
                    "manufacturer": None,
                    "equipment": None,
                },
            },
            {
                "filename": "passport.pdf",
                "classification": "Паспорт оборудования",
                "status": "Готово",
                "extension": ".pdf",
                "analysis": {
                    "drawing_number": None,
                    "date": "11.08.2026",
                    "manufacturer": "ООО Завод",
                    "equipment": "Трансформатор ТМГ",
                },
            },
        ],
    }

    project_analysis_path = (
        analysis_path
        / "project_analysis.json"
    )

    project_analysis_path.write_text(
        json.dumps(
            project_analysis,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    result = registry.build(project_name)

    assert result["project"] == project_name
    assert result["documents_count"] == 2

    assert result["documents"][0]["number"] == 1
    assert result["documents"][0]["filename"] == "drawing.pdf"
    assert result["documents"][0]["classification"] == "Чертеж"
    assert result["documents"][0]["drawing_number"] == "TEST-001"

    assert result["documents"][1]["number"] == 2
    assert result["documents"][1]["filename"] == "passport.pdf"
    assert result["documents"][1]["manufacturer"] == "ООО Завод"
    assert result["documents"][1]["equipment"] == "Трансформатор ТМГ"

    output_path = (
        analysis_path
        / "document_registry.json"
    )

    assert output_path.exists()

    saved = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert saved == result
