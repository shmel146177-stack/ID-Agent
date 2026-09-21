import json
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

    assert saved_ai is not None
    assert saved_ai["summary"] == ai_analysis["summary"]
    assert saved_ai["source_filename"] == ai_analysis["source_filename"]
    assert saved_ai["requires_human_review"] is True
    assert saved_ai["engineering_confirmation"] is False
    assert saved_ai["analysis_id"]

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

def test_ai_analysis_gets_new_id_for_each_save(tmp_path):
    service = ProjectService()

    service.ai_file_path = str(
        tmp_path / "current_ai_analysis.json"
    )
    service.ai_review_file_path = str(
        tmp_path / "current_ai_review.json"
    )

    analysis = {
        "summary": "AI suggestion",
        "requires_human_review": True,
        "engineering_confirmation": False,
    }

    first = service.save_ai_analysis(
        analysis,
        source_filename="drawing.pdf",
    )["document"]

    second = service.save_ai_analysis(
        analysis,
        source_filename="drawing.pdf",
    )["document"]

    assert first["source_filename"] == "drawing.pdf"
    assert second["source_filename"] == "drawing.pdf"

    assert first["analysis_id"]
    assert second["analysis_id"]
    assert first["analysis_id"] != second["analysis_id"]


def test_new_ai_analysis_archives_matching_review(tmp_path):
    service = ProjectService()
    service.ai_file_path = str(tmp_path / "current_ai_analysis.json")
    service.ai_review_file_path = str(tmp_path / "current_ai_review.json")
    service.ai_review_history_dir = str(tmp_path / "review_history")

    first = service.save_ai_analysis(
        {
            "summary": "First analysis",
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        source_filename="passport.pdf",
    )["document"]
    review = {
        "source_filename": "passport.pdf",
        "analysis_id": first["analysis_id"],
        "decision": "accepted",
        "excluded_fact_review_history": [
            {
                "field": "voltage",
                "action": "created",
            },
        ],
    }
    service.save_ai_review(review)

    service.save_ai_analysis(
        {
            "summary": "Second analysis",
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        source_filename="passport.pdf",
    )

    assert service.get_ai_review() is None
    archived = service.get_ai_review_history(first["analysis_id"])

    assert archived is not None
    assert archived["analysis_id"] == first["analysis_id"]
    assert archived["excluded_fact_review_history"] == review[
        "excluded_fact_review_history"
    ]
    assert archived["archived_at"]


def test_deterministic_analysis_archives_matching_ai_review(tmp_path):
    service = ProjectService()
    service.file_path = str(tmp_path / "current_analysis.json")
    service.ai_file_path = str(tmp_path / "current_ai_analysis.json")
    service.ai_review_file_path = str(tmp_path / "current_ai_review.json")
    service.ai_review_history_dir = str(tmp_path / "review_history")

    analysis = service.save_ai_analysis(
        {
            "summary": "AI analysis",
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        source_filename="passport.pdf",
    )["document"]
    review = {
        "source_filename": "passport.pdf",
        "analysis_id": analysis["analysis_id"],
        "decision": "needs_changes",
    }
    service.save_ai_review(review)

    service.save_analysis({"document_type": "drawing"})

    archived = service.get_ai_review_history(analysis["analysis_id"])

    assert archived is not None
    assert archived["analysis_id"] == analysis["analysis_id"]
    assert archived["decision"] == review["decision"]
    assert archived["archived_at"]


def test_ai_review_history_path_does_not_use_raw_analysis_id(tmp_path):
    service = ProjectService()
    service.ai_review_history_dir = str(tmp_path / "review_history")

    archive_path = Path(
        service._ai_review_history_path("../../outside")
    )

    assert archive_path.parent == tmp_path / "review_history"
    assert archive_path.suffix == ".json"
    assert "outside" not in archive_path.name


def test_project_service_lists_review_archives_newest_first(tmp_path):
    service = ProjectService()
    service.ai_review_history_dir = str(tmp_path / "review_history")
    Path(service.ai_review_history_dir).mkdir()

    archives = [
        {
            "analysis_id": "analysis-old",
            "source_filename": "old.pdf",
            "decision": "rejected",
            "archived_at": "2026-09-20T10:00:00+00:00",
            "excluded_fact_review_history": [{"action": "created"}],
        },
        {
            "analysis_id": "analysis-new",
            "source_filename": "new.pdf",
            "decision": "accepted",
            "archived_at": "2026-09-21T10:00:00+00:00",
            "excluded_fact_review_history": [
                {"action": "created"},
                {"action": "updated"},
            ],
        },
    ]

    for archive in archives:
        path = service._ai_review_history_path(archive["analysis_id"])
        Path(path).write_text(
            json.dumps(archive),
            encoding="utf-8",
        )

    (Path(service.ai_review_history_dir) / "broken.json").write_text(
        "not-json",
        encoding="utf-8",
    )

    result = service.list_ai_review_history()

    assert [item["analysis_id"] for item in result] == [
        "analysis-new",
        "analysis-old",
    ]
    assert result[0]["history_event_count"] == 2
