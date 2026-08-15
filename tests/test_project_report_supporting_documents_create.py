from pathlib import Path

import app.generators.project_report_generator as report_module
from app.generators.project_report_generator import ProjectReportGenerator


def test_project_report_create_uses_supporting_documents(monkeypatch, tmp_path):
    generator = ProjectReportGenerator()

    project_name = "TEST_PROJECT"
    output_path = tmp_path / "report.docx"

    supporting_documents = {
        "requirements_count": 3,
        "high_priority_count": 2,
        "requires_field_confirmation": True,
        "sections": [
            {
                "number": "04",
                "code": "executive_schemes",
                "title": "Исполнительные схемы",
                "required_count": 1,
                "documents": [],
            },
        ],
    }

    monkeypatch.setattr(
        generator,
        "_load_project_card",
        lambda name: {},
    )

    monkeypatch.setattr(
        generator,
        "_analysis_path",
        lambda name, filename: tmp_path / filename,
    )

    def fake_load_json(path, default=None):
        if Path(path).name == "supporting_documents_registry.json":
            return supporting_documents
        return {}

    monkeypatch.setattr(
        generator,
        "_load_json",
        fake_load_json,
    )

    monkeypatch.setattr(
        report_module.document_completeness,
        "check",
        lambda name: {},
    )

    monkeypatch.setattr(
        generator,
        "_output_path",
        lambda name: output_path,
    )

    captured = {}

    def capture_supporting(document, data):
        captured["data"] = data

    monkeypatch.setattr(
        generator,
        "_add_supporting_documents",
        capture_supporting,
    )

    generator.create(project_name)

    assert captured["data"] == supporting_documents
    assert output_path.exists()
