import pytest
from pydantic import ValidationError

from app.models.ai_review import (
    AIReviewDecision,
    ExcludedAutonomousFactReview,
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
