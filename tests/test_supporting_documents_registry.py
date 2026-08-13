import json
from pathlib import Path

import app.services.supporting_documents_registry as registry_module
from app.services.supporting_documents_registry import SupportingDocumentsRegistry


def test_supporting_documents_registry_builds_requirements(monkeypatch, tmp_path):

    registry = SupportingDocumentsRegistry()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    analysis_path = project_path / "analysis"

    project_path.mkdir(parents=True)

    hidden_works = {
        "status": "Готово",
        "acts_count": 2,
        "acts": [
            {
                "code": "grounding_device",
                "title": "Заземляющее устройство",
                "act_title": "АОСР на устройство заземляющего устройства",
                "evidence": [
                    {
                        "sheet_number": 10,
                        "title": "Устройство очага заземления",
                        "page_type": "Заземление",
                        "pages_count": 1,
                        "source": "Тест",
                    }
                ],
            },
            {
                # Повтор того же акта:
                # требования не должны задвоиться.
                "code": "grounding_device",
                "title": "Заземляющее устройство",
                "act_title": "АОСР на устройство заземляющего устройства",
                "evidence": [],
            },
        ],
    }

    monkeypatch.setattr(
        registry,
        "_project_path",
        lambda name: project_path,
    )

    monkeypatch.setattr(
        registry,
        "_analysis_path",
        lambda name: analysis_path,
    )

    monkeypatch.setattr(
        registry_module.hidden_works_registry,
        "analyze_project",
        lambda name: hidden_works,
    )

    result = registry.analyze_project(project_name)

    assert result["project"] == project_name

    # grounding_device имеет 3 требования:
    # разделы 04, 05 и 06.
    assert result["requirements_count"] == 3
    assert result["high_priority_count"] == 3
    assert result["requires_field_confirmation"] is True

    assert len(result["requirements"]) == 3
    assert len(result["sections"]) == 3

    codes = {
        item["code"]
        for item in result["requirements"]
    }

    assert codes == {
        "grounding_executive_scheme",
        "grounding_resistance_protocol",
        "grounding_quality_documents",
    }

    section_codes = {
        section["code"]
        for section in result["sections"]
    }

    assert section_codes == {
        "executive_schemes",
        "tests",
        "quality_documents",
    }

    for section in result["sections"]:
        assert section["required_count"] == 1
        assert section["high_priority_count"] == 1

    first = result["requirements"][0]

    assert first["source_act"]["code"] == "grounding_device"
    assert first["confirmation_required"] is True

    output_path = Path(result["analysis_file"])

    assert output_path.exists()
    assert output_path.name == "supporting_documents_registry.json"

    saved = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert saved["project"] == project_name
    assert saved["requirements_count"] == 3
    assert saved["high_priority_count"] == 3
    assert len(saved["requirements"]) == 3
