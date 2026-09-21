from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.ai_review import (
    AIReviewDecision,
    ExcludedAutonomousFactReview,
    ExcludedAutonomousFactReviewHistory,
    ExcludedAutonomousFactReviewUpdate,
)


def test_ai_review_decision_requires_explicit_human_decision():
    review = AIReviewDecision(
        source_filename="drawing.pdf",
        analysis_id="analysis-1",
        decision="accepted",
        notes="Checked against source document.",
    )

    assert review.source_filename == "drawing.pdf"
    assert review.analysis_id == "analysis-1"
    assert review.decision == "accepted"
    assert review.notes == "Checked against source document."
    assert review.review_revision == 0


def test_ai_review_models_reject_negative_revisions():
    with pytest.raises(ValidationError):
        AIReviewDecision(
            source_filename="drawing.pdf",
            analysis_id="analysis-1",
            decision="accepted",
            review_revision=-1,
        )

    with pytest.raises(ValidationError):
        ExcludedAutonomousFactReviewUpdate(
            source_filename="drawing.pdf",
            analysis_id="analysis-1",
            expected_revision=-1,
            decision="accepted",
            reviewed_by="Engineer",
        )


def test_ai_review_decision_rejects_unknown_decision():
    with pytest.raises(ValidationError):
        AIReviewDecision(
            source_filename="drawing.pdf",
            analysis_id="analysis-1",
            decision="automatic",
        )

def test_ai_review_decision_requires_analysis_id():
    with pytest.raises(ValidationError):
        AIReviewDecision(
            source_filename="drawing.pdf",
            decision="accepted",
        )


def test_excluded_fact_review_accepts_correction():
    review = ExcludedAutonomousFactReview(
        field=" voltage ",
        decision="corrected",
        corrected_value=" 230 В ",
        notes=" Checked against the nameplate. ",
    )

    assert review.field == "voltage"
    assert review.corrected_value == "230 В"
    assert review.notes == "Checked against the nameplate."


@pytest.mark.parametrize(
    "payload",
    [
        {
            "field": "voltage",
            "decision": "corrected",
        },
        {
            "field": "voltage",
            "decision": "accepted",
            "corrected_value": "230 В",
        },
        {
            "field": " ",
            "decision": "rejected",
        },
    ],
)
def test_excluded_fact_review_rejects_invalid_decision(payload):
    with pytest.raises(ValidationError):
        ExcludedAutonomousFactReview(**payload)


def test_ai_review_rejects_duplicate_excluded_fact_fields():
    with pytest.raises(ValidationError):
        AIReviewDecision(
            source_filename="drawing.pdf",
            analysis_id="analysis-1",
            decision="needs_changes",
            excluded_fact_reviews=[
                {
                    "field": "voltage",
                    "decision": "accepted",
                },
                {
                    "field": "voltage",
                    "decision": "rejected",
                },
            ],
        )


def test_excluded_fact_review_update_normalizes_correction():
    update = ExcludedAutonomousFactReviewUpdate(
        source_filename="passport.pdf",
        analysis_id="analysis-1",
        decision="corrected",
        corrected_value=" 230 В ",
        notes=" Checked by human. ",
        reviewed_by=" Engineer ",
    )

    assert update.corrected_value == "230 В"
    assert update.notes == "Checked by human."
    assert update.reviewed_by == "Engineer"


def test_excluded_fact_review_validates_audit_pair():
    with pytest.raises(ValidationError):
        ExcludedAutonomousFactReview(
            field="voltage",
            decision="accepted",
            reviewed_by="Engineer",
        )


def test_excluded_fact_review_history_accepts_created_event():
    current_review = ExcludedAutonomousFactReview(
        field="voltage",
        decision="accepted",
    )
    event = ExcludedAutonomousFactReviewHistory(
        analysis_id="analysis-1",
        field=" voltage ",
        action="created",
        current_review=current_review,
        reviewed_by=" Engineer ",
        reviewed_at=datetime.now(timezone.utc),
    )

    assert event.field == "voltage"
    assert event.reviewed_by == "Engineer"


@pytest.mark.parametrize(
    "action,previous,current",
    [
        ("created", {"field": "voltage", "decision": "rejected"}, None),
        ("updated", None, {"field": "voltage", "decision": "accepted"}),
        ("cleared", None, None),
    ],
)
def test_excluded_fact_review_history_rejects_invalid_transition(
    action,
    previous,
    current,
):
    with pytest.raises(ValidationError):
        ExcludedAutonomousFactReviewHistory(
            analysis_id="analysis-1",
            field="voltage",
            action=action,
            previous_review=previous,
            current_review=current,
            reviewed_by="Engineer",
            reviewed_at=datetime.now(timezone.utc),
        )
