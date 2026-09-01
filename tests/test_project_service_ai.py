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

    assert result is not None
    assert result["summary"] == ai_analysis["summary"]
    assert (
        result["document_type_suggestion"]
        == ai_analysis["document_type_suggestion"]
    )
    assert result["requires_human_review"] is True
    assert result["engineering_confirmation"] is False
    assert result["analysis_id"]

def test_new_deterministic_analysis_invalidates_old_ai(tmp_path):
    service = ProjectService()

    service.file_path = str(
        tmp_path / "current_analysis.json"
    )
    service.ai_file_path = str(
        tmp_path / "current_ai_analysis.json"
    )

    service.save_ai_analysis(
        {
            "summary": "Old AI analysis",
            "requires_human_review": True,
            "engineering_confirmation": False,
        }
    )

    assert Path(service.ai_file_path).exists()

    service.save_analysis(
        {
            "document_type": "new-drawing",
        }
    )

    assert not Path(service.ai_file_path).exists()


def test_ai_analysis_can_store_source_filename(tmp_path):
    service = ProjectService()

    service.ai_file_path = str(
        tmp_path / "current_ai_analysis.json"
    )

    service.save_ai_analysis(
        {
            "summary": "AI analysis",
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        source_filename="drawing.pdf",
    )

    saved = service.get_ai_analysis()

    assert saved["source_filename"] == "drawing.pdf"
    assert saved["summary"] == "AI analysis"

def test_project_service_saves_ai_comparison_with_source_binding(tmp_path):
    service = ProjectService()

    service.ai_comparison_file_path = str(
        tmp_path / "current_ai_comparison.json"
    )

    comparison = {
        "matches": [],
        "conflicts": [],
        "suggestions": [
            {
                "field": "drawing_number",
                "value": "A-01",
                "confidence": 0.95,
            }
        ],
        "requires_human_review": True,
        "engineering_confirmation": False,
    }

    service.save_ai_comparison(
        comparison,
        analysis_id="analysis-123",
        source_filename="drawing.pdf",
        knowledge_source_ids=["sp-grounding"],
    )

    saved = service.get_ai_comparison()

    assert saved is not None
    assert saved["analysis_id"] == "analysis-123"
    assert saved["source_filename"] == "drawing.pdf"
    assert saved["knowledge_source_ids"] == ["sp-grounding"]
    assert saved["suggestions"] == comparison["suggestions"]
    assert saved["requires_human_review"] is True
    assert saved["engineering_confirmation"] is False

def test_new_deterministic_analysis_invalidates_old_ai_comparison(tmp_path):
    service = ProjectService()

    service.file_path = str(
        tmp_path / "current_analysis.json"
    )
    service.ai_comparison_file_path = str(
        tmp_path / "current_ai_comparison.json"
    )

    service.save_ai_comparison(
        {
            "matches": [],
            "conflicts": [],
            "suggestions": [],
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        analysis_id="old-analysis-id",
        source_filename="old.pdf",
    )

    assert Path(service.ai_comparison_file_path).exists()

    service.save_analysis(
        {
            "document_type": "new-drawing",
        }
    )

    assert not Path(service.ai_comparison_file_path).exists()

def test_new_ai_analysis_invalidates_old_ai_comparison(tmp_path):
    service = ProjectService()

    service.ai_file_path = str(
        tmp_path / "current_ai_analysis.json"
    )
    service.ai_comparison_file_path = str(
        tmp_path / "current_ai_comparison.json"
    )

    service.save_ai_comparison(
        {
            "matches": [],
            "conflicts": [],
            "suggestions": [],
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        analysis_id="old-analysis-id",
        source_filename="old.pdf",
    )

    assert Path(service.ai_comparison_file_path).exists()

    service.save_ai_analysis(
        {
            "summary": "New AI analysis",
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        source_filename="new.pdf",
    )

    assert not Path(service.ai_comparison_file_path).exists()


def test_project_service_saves_ai_knowledge_source_ids(tmp_path):
    service = ProjectService()
    service.ai_file_path = str(
        tmp_path / "current_ai_analysis.json"
    )

    service.save_ai_analysis(
        {
            "summary": "AI analysis with knowledge.",
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        source_filename="drawing.pdf",
        knowledge_source_ids=[
            "sp-grounding",
            "sp-concrete",
        ],
    )

    saved = service.get_ai_analysis()

    assert saved["knowledge_source_ids"] == [
        "sp-grounding",
        "sp-concrete",
    ]
