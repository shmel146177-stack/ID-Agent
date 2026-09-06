from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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


class AIAnalysisExecutionResult(AIAnalysisResult):
    """Result with trusted runtime diagnostics."""

    analysis_mode: Literal["openai", "autonomous"]
    ai_provider: str
    ai_model: str
    fallback_reason: AIFallbackReason | None = None
