from pathlib import Path

from app.services.project_service import ProjectService


def test_project_service_saves_ai_analysis_separately(tmp_path):
    service = ProjectService()

    service.file_path = str(
        tmp_path / "current_analysis.json"
    )
    service.ai_file_path = str(
        tmp_path / "current_ai_analysis.json"
    )

    deterministic_analysis = {
        "document_type": "drawing",
        "drawing_number": "TEST-001",
    }

    ai_analysis = {
        "summary": "AI suggestion",
        "document_type_suggestion": "passport",
        "requires_human_review": True,
        "engineering_confirmation": False,
    }

    service.save_analysis(deterministic_analysis)
    service.save_ai_analysis(ai_analysis)

    deterministic_saved = Path(
        service.file_path
    ).read_text(encoding="utf-8")

    ai_saved = Path(
        service.ai_file_path
    ).read_text(encoding="utf-8")

    assert '"document_type": "drawing"' in deterministic_saved
    assert '"AI suggestion"' not in deterministic_saved

    assert '"summary": "AI suggestion"' in ai_saved
    assert '"document_type": "drawing"' not in ai_saved

def test_project_service_reads_ai_analysis(tmp_path):
    service = ProjectService()

    service.ai_file_path = str(
        tmp_path / "current_ai_analysis.json"
    )

    ai_analysis = {
        "summary": "Saved AI analysis",
        "document_type_suggestion": "drawing",
        "requires_human_review": True,
        "engineering_confirmation": False,
    }

    service.save_ai_analysis(ai_analysis)

    result = service.get_ai_analysis()

    assert result == ai_analysis
