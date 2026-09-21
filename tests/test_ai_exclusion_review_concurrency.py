from threading import Event, Thread

from app.models.ai_review import ExcludedAutonomousFactReviewUpdate
from app.services.ai_exclusion_review import (
    AIExclusionReviewError,
    AIExclusionReviewService,
)
from app.services.project_service import ProjectService


def test_independent_review_services_reject_concurrent_stale_update(
    tmp_path,
):
    analysis_path = str(tmp_path / "current_ai_analysis.json")
    review_path = str(tmp_path / "current_ai_review.json")

    first_project = ProjectService()
    first_project.ai_file_path = analysis_path
    first_project.ai_review_file_path = review_path
    second_project = ProjectService()
    second_project.ai_file_path = analysis_path
    second_project.ai_review_file_path = review_path

    analysis = first_project.save_ai_analysis(
        {
            "excluded_autonomous_facts": [
                {
                    "field": "voltage",
                    "value": "220 В",
                    "reason": "insufficient_context",
                    "evidence": "220 В",
                },
            ],
        },
        source_filename="passport.pdf",
    )["document"]
    request = ExcludedAutonomousFactReviewUpdate(
        source_filename="passport.pdf",
        analysis_id=analysis["analysis_id"],
        expected_revision=0,
        decision="accepted",
        reviewed_by="Engineer",
    )
    first_service = AIExclusionReviewService(first_project)
    second_service = AIExclusionReviewService(second_project)
    first_read = Event()
    release_first = Event()
    second_finished = Event()
    results = []
    errors = []
    original_get_review = first_project.get_ai_review

    def pause_after_first_read():
        review = original_get_review()
        first_read.set()
        release_first.wait(timeout=2)
        return review

    first_project.get_ai_review = pause_after_first_read

    def update(service):
        try:
            results.append(
                service.update_fact_review("voltage", request)
            )
        except AIExclusionReviewError as error:
            errors.append(error)

    def update_second():
        try:
            update(second_service)
        finally:
            second_finished.set()

    first = Thread(target=update, args=(first_service,))
    second = Thread(target=update_second)
    first.start()
    assert first_read.wait(timeout=2)

    second.start()
    assert not second_finished.wait(timeout=0.1)
    release_first.set()
    first.join(timeout=2)
    second.join(timeout=2)

    assert not first.is_alive()
    assert not second.is_alive()
    assert len(results) == 1
    assert results[0]["review_revision"] == 1
    assert len(errors) == 1
    assert errors[0].status_code == 409
    assert errors[0].detail == (
        "AI review revision mismatch: expected 0, current 1"
    )


def test_reanalysis_waits_for_review_update_before_archiving(tmp_path):
    analysis_path = str(tmp_path / "current_ai_analysis.json")
    review_path = str(tmp_path / "current_ai_review.json")
    history_path = str(tmp_path / "review_history")

    review_project = ProjectService()
    review_project.ai_file_path = analysis_path
    review_project.ai_review_file_path = review_path
    review_project.ai_review_history_dir = history_path
    analysis_project = ProjectService()
    analysis_project.ai_file_path = analysis_path
    analysis_project.ai_review_file_path = review_path
    analysis_project.ai_review_history_dir = history_path

    analysis = review_project.save_ai_analysis(
        {
            "excluded_autonomous_facts": [
                {
                    "field": "voltage",
                    "value": "220 В",
                    "reason": "insufficient_context",
                    "evidence": "220 В",
                },
            ],
        },
        source_filename="passport.pdf",
    )["document"]
    request = ExcludedAutonomousFactReviewUpdate(
        source_filename="passport.pdf",
        analysis_id=analysis["analysis_id"],
        expected_revision=0,
        decision="accepted",
        reviewed_by="Engineer",
    )
    review_service = AIExclusionReviewService(review_project)
    review_read = Event()
    release_review = Event()
    analysis_finished = Event()
    original_get_review = review_project.get_ai_review

    def pause_after_review_read():
        review = original_get_review()
        review_read.set()
        release_review.wait(timeout=2)
        return review

    review_project.get_ai_review = pause_after_review_read

    def update_review():
        review_service.update_fact_review("voltage", request)

    def run_reanalysis():
        try:
            analysis_project.save_ai_analysis(
                {"excluded_autonomous_facts": []},
                source_filename="passport.pdf",
            )
        finally:
            analysis_finished.set()

    review_thread = Thread(target=update_review)
    analysis_thread = Thread(target=run_reanalysis)
    review_thread.start()
    assert review_read.wait(timeout=2)

    analysis_thread.start()
    assert not analysis_finished.wait(timeout=0.1)
    release_review.set()
    review_thread.join(timeout=2)
    analysis_thread.join(timeout=2)

    assert not review_thread.is_alive()
    assert not analysis_thread.is_alive()
    archived = analysis_project.get_ai_review_history(
        analysis["analysis_id"]
    )
    assert archived is not None
    assert archived["review_revision"] == 1
    assert archived["excluded_fact_reviews"][0]["field"] == "voltage"
