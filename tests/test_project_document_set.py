import json
from pathlib import Path

import app.generators.project_document_set as set_module
from app.generators.project_document_set import ProjectDocumentSet


def test_project_document_set_creates_real_json(monkeypatch, tmp_path):

    generator = ProjectDocumentSet()

    project_name = "TEST_PROJECT"
    project_path = tmp_path / project_name
    analysis_path = project_path / "analysis"
    executive_root = project_path / "executive"

    project_path.mkdir(parents=True)

    folders = {
        "root": executive_root,
    }

    hidden_works_result = {
        "status": "Готово",
        "acts_count": 2,
        "high_priority_count": 1,
        "requires_field_confirmation": True,
    }

    sections = [
        {
            "code": "hidden_works",
            "title": "Акты скрытых работ",
            "status": "Документы сформированы",
            "actual_files_count": 2,
            "detected": {
                "files_count": 2,
                "files": [
                    "act_1.docx",
                    "act_2.docx",
                ],
            },
        },
        {
            "code": "journals",
            "title": "Журналы",
            "status": "Документы сформированы",
            "actual_files_count": 1,
            "detected": {
                "files_count": 1,
                "files": [
                    "journal.docx",
                ],
            },
        },
        {
            "code": "other",
            "title": "Прочие документы",
            "status": "Нет документов",
            "actual_files_count": 0,
            "detected": {
                "files_count": 0,
                "files": [],
            },
        },
    ]

    completeness = {
        "status": "Неполный комплект",
        "required_count": 4,
        "found_count": 3,
        "missing_count": 1,
        "completeness_percent": 75.0,
        "missing_sheets": [
            {
                "sheet_number": 4,
                "title": "Недостающий лист",
            }
        ],
    }

    monkeypatch.setattr(
        generator,
        "_project_path",
        lambda name: project_path,
    )

    monkeypatch.setattr(
        generator,
        "_analysis_path",
        lambda name: analysis_path,
    )

    monkeypatch.setattr(
        generator,
        "_executive_root",
        lambda name: executive_root,
    )

    monkeypatch.setattr(
        generator,
        "_create_folders",
        lambda name: folders,
    )

    monkeypatch.setattr(
        set_module.hidden_works_registry,
        "analyze_project",
        lambda name: hidden_works_result,
    )

    monkeypatch.setattr(
        generator,
        "_build_sections",
        lambda name, folders_data, hidden_data: sections,
    )

    monkeypatch.setattr(
        generator,
        "_missing_requirements",
        lambda name: completeness,
    )

    result = generator.create(project_name)

    assert result["project"] == project_name
    assert result["sections_count"] == 3
    assert result["sections_with_files"] == 2
    assert result["actual_files_count"] == 3

    assert result["hidden_works"]["acts_count"] == 2
    assert result["hidden_works"]["high_priority_count"] == 1
    assert result["hidden_works"]["requires_field_confirmation"] is True

    assert result["project_completeness"]["required_count"] == 4
    assert result["project_completeness"]["found_count"] == 3
    assert result["project_completeness"]["missing_count"] == 1
    assert result["project_completeness"]["completeness_percent"] == 75.0

    output_path = Path(result["analysis_file"])

    assert output_path.exists()
    assert output_path.name == "project_document_set.json"

    saved = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert saved["project"] == project_name
    assert saved["sections_count"] == 3
    assert saved["sections_with_files"] == 2
    assert saved["actual_files_count"] == 3
    assert saved["hidden_works"]["acts_count"] == 2
    assert saved["project_completeness"]["missing_count"] == 1
