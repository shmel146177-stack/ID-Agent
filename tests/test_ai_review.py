import pytest
from pydantic import ValidationError

from app.models.ai_review import AIReviewDecision


def test_ai_review_decision_requires_explicit_human_decision():
    review = AIReviewDecision(
        source_filename="drawing.pdf",
        decision="accepted",
        notes="Checked against source document.",
    )

    assert review.source_filename == "drawing.pdf"
    assert review.decision == "accepted"
    assert review.notes == "Checked against source document."


def test_ai_review_decision_rejects_unknown_decision():
    with pytest.raises(ValidationError):
        AIReviewDecision(
            source_filename="drawing.pdf",
            decision="automatic",
        )
