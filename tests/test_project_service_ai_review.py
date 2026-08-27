from pathlib import Path

from app.services.project_service import ProjectService


def test_project_service_saves_ai_review_separately(tmp_path):
    service = ProjectService()

    service.ai_file_path = str(
        tmp_path / "current_ai_analysis.json"
    )
    service.ai_review_file_path = str(
        tmp_path / "current_ai_review.json"
    )

    ai_analysis = {
        "summary": "AI suggestion",
        "source_filename": "drawing.pdf",
        "requires_human_review": True,
        "engineering_confirmation": False,
    }

    review = {
        "source_filename": "drawing.pdf",
        "decision": "accepted",
        "notes": "Checked by human.",
    }

    service.save_ai_analysis(ai_analysis)
    service.save_ai_review(review)

    saved_ai = service.get_ai_analysis()
    saved_review = service.get_ai_review()

    assert saved_ai == ai_analysis
    assert saved_review == review

    assert Path(service.ai_file_path).exists()
    assert Path(service.ai_review_file_path).exists()


def test_new_ai_analysis_invalidates_old_review(tmp_path):
    service = ProjectService()

    service.ai_file_path = str(
        tmp_path / "current_ai_analysis.json"
    )
    service.ai_review_file_path = str(
        tmp_path / "current_ai_review.json"
    )

    service.save_ai_review(
        {
            "source_filename": "old.pdf",
            "decision": "accepted",
            "notes": "Checked by human.",
        }
    )

    assert Path(service.ai_review_file_path).exists()

    service.save_ai_analysis(
        {
            "summary": "New AI analysis",
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        source_filename="new.pdf",
    )

    assert not Path(service.ai_review_file_path).exists()


def test_new_deterministic_analysis_invalidates_old_review(tmp_path):
    service = ProjectService()

    service.file_path = str(
        tmp_path / "current_analysis.json"
    )
    service.ai_file_path = str(
        tmp_path / "current_ai_analysis.json"
    )
    service.ai_review_file_path = str(
        tmp_path / "current_ai_review.json"
    )

    service.save_ai_review(
        {
            "source_filename": "old.pdf",
            "decision": "accepted",
            "notes": "Checked by human.",
        }
    )

    assert Path(service.ai_review_file_path).exists()

    service.save_analysis(
        {
            "document_type": "new-drawing",
        }
    )

    assert not Path(service.ai_review_file_path).exists()
