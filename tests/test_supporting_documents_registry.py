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

    by_code = {item["code"]: item for item in result["requirements"]}

    scheme = by_code["grounding_executive_scheme"]
    assert scheme["document_types"] == ["Исполнительная схема"]
    assert scheme["match_keywords"] == ["заземл"]

    quality = by_code["grounding_quality_documents"]
    assert quality["document_types"] == ["Паспорт оборудования", "Сертификат", "Декларация"]
    assert "полос" in quality["match_any_keywords"]

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


def test_supporting_documents_registry_matches_saved_analysis(
    monkeypatch,
    tmp_path,
):
    registry = SupportingDocumentsRegistry()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    analysis_path = project_path / "analysis"

    analysis_path.mkdir(parents=True)

    hidden_works = {
        "acts": [
            {
                "code": "grounding_device",
                "title": "Grounding",
                "act_title": "Grounding act",
                "evidence": [],
            }
        ]
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

    project_analysis = {
        "documents": [
            {
                "filename": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442.pdf",
                "path": "input/certificate.pdf",
                "classification": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442",
            }
        ]
    }

    page_analysis = {
        "documents": [
            {
                "filename": "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442.pdf",
                "pages": [
                    {
                        "text": (
                            "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442 "
                            "\u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0438\u044f "
                            "\u043d\u0430 \u043f\u043e\u043b\u043e\u0441\u0443 "
                            "\u0441\u0442\u0430\u043b\u044c\u043d\u0443\u044e 40x5"
                        )
                    }
                ],
            }
        ]
    }

    (analysis_path / "project_analysis.json").write_text(
        registry_module.json.dumps(
            project_analysis,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    (analysis_path / "page_analysis.json").write_text(
        registry_module.json.dumps(
            page_analysis,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = registry.analyze_project(project_name)

    matching = result["matching"]

    assert matching["required_count"] == 3
    assert matching["found_count"] == 1
    assert matching["missing_count"] == 2

    assert len(matching["matched"]) == 1

    matched = matching["matched"][0]

    assert matched["requirement_code"] == "grounding_quality_documents"
    assert matched["filename"] == "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442.pdf"
    assert matched["classification"] == "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442"
