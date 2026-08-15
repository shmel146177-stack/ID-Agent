import app.services.project_processor as processor_module
from app.services.project_processor import ProjectProcessor


def test_project_processor_pipeline(monkeypatch):
    project_name = "TEST_PROJECT"

    monkeypatch.setattr(
        processor_module.document_scanner,
        "analyze_project",
        lambda name: {"status": "scan_ok"},
    )

    monkeypatch.setattr(
        processor_module.page_analysis_service,
        "analyze_project",
        lambda name: {"status": "page_analysis_ok"},
    )

    monkeypatch.setattr(
        processor_module.project_section_exporter,
        "export_project",
        lambda name: {"status": "section_export_ok"},
    )

    monkeypatch.setattr(
        processor_module.drawing_register_service,
        "analyze_project",
        lambda name: {"status": "drawing_register_ok"},
    )

    monkeypatch.setattr(
        processor_module.project_metadata_service,
        "update_from_project",
        lambda name: {"status": "metadata_ok"},
    )

    monkeypatch.setattr(
        processor_module.document_registry,
        "build",
        lambda name: {"status": "registry_ok"},
    )

    monkeypatch.setattr(
        processor_module.document_completeness,
        "check",
        lambda name: {"status": "completeness_ok"},
    )

    monkeypatch.setattr(
        processor_module.executive_document_router,
        "route",
        lambda name: {"status": "routing_ok"},
    )

    monkeypatch.setattr(
        processor_module.supporting_documents_registry,
        "analyze_project",
        lambda name: {"status": "supporting_documents_ok"},
    )

    monkeypatch.setattr(
        processor_module.hidden_works_act_generator,
        "create_all",
        lambda name: {"status": "acts_ok"},
    )

    monkeypatch.setattr(
        processor_module.hidden_works_journal_generator,
        "create",
        lambda name: "journal.docx",
    )

    monkeypatch.setattr(
        processor_module.document_registry_excel,
        "create",
        lambda name: "registry.xlsx",
    )

    monkeypatch.setattr(
        processor_module.project_report_generator,
        "create",
        lambda name: "report.docx",
    )

    result = ProjectProcessor().process(project_name)

    assert result["project"] == project_name
    assert result["status"] == "Готово"

    assert result["scan"]["status"] == "scan_ok"
    assert result["page_analysis"]["status"] == "page_analysis_ok"
    assert result["section_export"]["status"] == "section_export_ok"
    assert result["drawing_register"]["status"] == "drawing_register_ok"
    assert result["metadata"]["status"] == "metadata_ok"
    assert result["registry"]["status"] == "registry_ok"
    assert result["completeness"]["status"] == "completeness_ok"
    assert result["document_routing"]["status"] == "routing_ok"
    assert result["supporting_documents"]["status"] == "supporting_documents_ok"
    assert result["hidden_works_acts"]["status"] == "acts_ok"

    assert result["hidden_works_journal"] == "journal.docx"
    assert result["excel"] == "registry.xlsx"
    assert result["report"] == "report.docx"
