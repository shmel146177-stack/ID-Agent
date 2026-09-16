from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)

AIFallbackReason = Literal[
    "empty_text",
    "api_not_configured",
    "ai_disabled",
    "backend_not_connected",
    "provider_unavailable",
    "credit_balance_exhausted",
    "rate_limit_exceeded",
    "invalid_provider_response",
]


AutonomousFactExclusionReason = Literal[
    "missing_evidence",
    "insufficient_context",
]


def _normalize_excluded_autonomous_fact_fields(
    fields: list[str],
) -> list[str]:
    normalized_fields = [
        field.strip()
        for field in fields
    ]

    if any(not field for field in normalized_fields):
        raise ValueError(
            "excluded autonomous fact fields "
            "must not be blank"
        )

    if len(normalized_fields) != len(set(normalized_fields)):
        raise ValueError(
            "excluded autonomous fact fields "
            "must be unique"
        )

    return normalized_fields



def _normalize_excluded_autonomous_fact_reasons(
    fields: list[str],
    reasons: dict[str, AutonomousFactExclusionReason],
) -> dict[str, AutonomousFactExclusionReason]:
    normalized_reasons = {
        field.strip(): reason
        for field, reason in reasons.items()
    }

    if any(not field for field in normalized_reasons):
        raise ValueError(
            "excluded autonomous fact reason fields "
            "must not be blank"
        )

    if len(normalized_reasons) != len(reasons):
        raise ValueError(
            "excluded autonomous fact reason fields "
            "must be unique"
        )

    if (
        normalized_reasons
        and set(normalized_reasons) != set(fields)
    ):
        raise ValueError(
            "excluded autonomous fact reasons "
            "must match excluded fields"
        )

    return normalized_reasons


def _count_excluded_autonomous_fact_reasons(
    reasons: dict[str, AutonomousFactExclusionReason],
) -> dict[AutonomousFactExclusionReason, int]:
    counts: dict[
        AutonomousFactExclusionReason,
        int,
    ] = {}

    for reason in reasons.values():
        counts[reason] = counts.get(reason, 0) + 1

    return counts


class AIFactSuggestion(BaseModel):
    """Факт, предложенный AI для последующей проверки."""

    model_config = ConfigDict(extra="forbid")

    field: str
    value: str
    evidence: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class AIAnalysisResult(BaseModel):
    """Структурированный результат AI-анализа документа."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    document_type_suggestion: str | None = None
    facts: list[AIFactSuggestion] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    requires_human_review: Literal[True] = True
    engineering_confirmation: Literal[False] = False


class AutonomousAnalysisResult(AIAnalysisResult):
    """Autonomous result with trusted exclusion diagnostics."""

    excluded_autonomous_fact_fields: list[str] = Field(
        default_factory=list
    )
    excluded_autonomous_fact_reasons: dict[
        str,
        AutonomousFactExclusionReason,
    ] = Field(default_factory=dict)

    @computed_field
    @property
    def excluded_autonomous_fact_reason_counts(
        self,
    ) -> dict[AutonomousFactExclusionReason, int]:
        return _count_excluded_autonomous_fact_reasons(
            self.excluded_autonomous_fact_reasons
        )

    @model_validator(mode="after")
    def validate_excluded_autonomous_fact_fields(self):
        self.excluded_autonomous_fact_fields = (
            _normalize_excluded_autonomous_fact_fields(
                self.excluded_autonomous_fact_fields
            )
        )
        self.excluded_autonomous_fact_reasons = (
            _normalize_excluded_autonomous_fact_reasons(
                self.excluded_autonomous_fact_fields,
                self.excluded_autonomous_fact_reasons,
            )
        )
        return self


class AIAnalysisExecutionResult(AIAnalysisResult):
    """Result with trusted runtime diagnostics."""

    analysis_mode: Literal["openai", "autonomous"]
    ai_provider: Literal["openai"]
    ai_model: str
    fallback_reason: AIFallbackReason | None = None
    excluded_autonomous_fact_fields: list[str] = Field(default_factory=list)
    excluded_autonomous_fact_reasons: dict[
        str,
        AutonomousFactExclusionReason,
    ] = Field(default_factory=dict)

    @computed_field
    @property
    def excluded_autonomous_fact_reason_counts(
        self,
    ) -> dict[AutonomousFactExclusionReason, int]:
        return _count_excluded_autonomous_fact_reasons(
            self.excluded_autonomous_fact_reasons
        )

    @model_validator(mode="after")
    def validate_execution_diagnostics(self):
        if not self.ai_model.strip():
            raise ValueError(
                "ai_model must not be blank"
            )

        if (
            self.analysis_mode == "openai"
            and self.fallback_reason is not None
        ):
            raise ValueError(
                "fallback_reason must be empty "
                "in openai mode"
            )

        if (
            self.analysis_mode == "autonomous"
            and self.fallback_reason is None
        ):
            raise ValueError(
                "fallback_reason is required "
                "in autonomous mode"
            )

        excluded_fields = (
            _normalize_excluded_autonomous_fact_fields(
                self.excluded_autonomous_fact_fields
            )
        )
        excluded_reasons = (
            _normalize_excluded_autonomous_fact_reasons(
                excluded_fields,
                self.excluded_autonomous_fact_reasons,
            )
        )

        if (
            self.analysis_mode == "openai"
            and (excluded_fields or excluded_reasons)
        ):
            raise ValueError(
                "excluded autonomous fact fields "
                "must be empty in openai mode"
            )

        self.excluded_autonomous_fact_fields = excluded_fields
        self.excluded_autonomous_fact_reasons = excluded_reasons

        return self
