from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExcludedAutonomousFactReview(BaseModel):
    """Human decision for one excluded autonomous fact."""

    model_config = ConfigDict(extra="forbid")

    field: str
    decision: Literal[
        "accepted",
        "rejected",
        "corrected",
    ]
    corrected_value: str | None = None
    notes: str | None = None
    reviewed_by: str | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    reviewed_at: datetime | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

    @model_validator(mode="after")
    def validate_correction(self):
        self.field = self.field.strip()

        if not self.field:
            raise ValueError("reviewed excluded fact field must not be blank")

        if self.corrected_value is not None:
            self.corrected_value = self.corrected_value.strip()

            if not self.corrected_value:
                raise ValueError("corrected value must not be blank")

        if self.decision == "corrected":
            if self.corrected_value is None:
                raise ValueError(
                    "corrected decision requires corrected value"
                )
        elif self.corrected_value is not None:
            raise ValueError(
                "corrected value is only allowed for corrected decision"
            )

        if self.notes is not None:
            self.notes = self.notes.strip()

            if not self.notes:
                raise ValueError("review notes must not be blank")

        if self.reviewed_by is not None:
            self.reviewed_by = self.reviewed_by.strip()

            if not self.reviewed_by:
                raise ValueError("reviewed by must not be blank")

        if (self.reviewed_by is None) != (self.reviewed_at is None):
            raise ValueError(
                "reviewed by and reviewed at must be provided together"
            )

        if (
            self.reviewed_at is not None
            and self.reviewed_at.tzinfo is None
        ):
            raise ValueError("reviewed at must include timezone")

        return self


class AIReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_filename: str
    analysis_id: str
    decision: Literal[
        "accepted",
        "rejected",
        "needs_changes",
    ]
    notes: str | None = None
    excluded_fact_reviews: list[
        ExcludedAutonomousFactReview
    ] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_excluded_fact_reviews(self):
        fields = [review.field for review in self.excluded_fact_reviews]

        if len(fields) != len(set(fields)):
            raise ValueError(
                "reviewed excluded fact fields must be unique"
            )

        return self


class ExcludedAutonomousFactReviewUpdate(BaseModel):
    """Partial review request bound to one current AI analysis."""

    model_config = ConfigDict(extra="forbid")

    source_filename: str
    analysis_id: str
    decision: Literal[
        "accepted",
        "rejected",
        "corrected",
    ]
    corrected_value: str | None = None
    notes: str | None = None
    reviewed_by: str = Field(min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_review_details(self):
        validated = ExcludedAutonomousFactReview(
            field="validated-field",
            decision=self.decision,
            corrected_value=self.corrected_value,
            notes=self.notes,
        )
        self.reviewed_by = self.reviewed_by.strip()

        if not self.reviewed_by:
            raise ValueError("reviewed by must not be blank")

        self.corrected_value = validated.corrected_value
        self.notes = validated.notes
        return self


class ExcludedAutonomousFactReviewBinding(BaseModel):
    """Binding required to change a saved per-fact review."""

    model_config = ConfigDict(extra="forbid")

    source_filename: str
    analysis_id: str
