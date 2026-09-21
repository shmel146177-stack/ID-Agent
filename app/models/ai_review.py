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
