import pytest
from pydantic import ValidationError

from app.models.ai_analysis import AIAnalysisResult, AIFactSuggestion


def test_ai_fact_suggestion_accepts_valid_confidence():
    fact = AIFactSuggestion(
        field="contract_number",
        value="123/26",
        evidence="Договор №123/26",
        confidence=0.91,
    )

    assert fact.field == "contract_number"
    assert fact.confidence == 0.91


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_ai_fact_suggestion_rejects_invalid_confidence(confidence):
    with pytest.raises(ValidationError):
        AIFactSuggestion(
            field="contract_number",
            value="123/26",
            confidence=confidence,
        )


def test_ai_analysis_requires_human_review_by_default():
    result = AIAnalysisResult(
        summary="Найден номер договора.",
    )

    assert result.requires_human_review is True
    assert result.engineering_confirmation is False


def test_ai_analysis_rejects_engineering_confirmation_true():
    with pytest.raises(ValidationError):
        AIAnalysisResult(
            summary="Попытка подтверждения.",
            engineering_confirmation=True,
        )


def test_ai_analysis_rejects_human_review_false():
    with pytest.raises(ValidationError):
        AIAnalysisResult(
            summary="Попытка отключить проверку.",
            requires_human_review=False,
        )


def test_ai_analysis_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        AIAnalysisResult(
            summary="Результат.",
            unexpected_field="unexpected",
        )


def test_ai_execution_result_supports_runtime_diagnostics():
    from app.models.ai_analysis import AIAnalysisExecutionResult

    result = AIAnalysisExecutionResult(
        summary="Autonomous result.",
        analysis_mode="autonomous",
        ai_provider="openai",
        ai_model="test-model",
        fallback_reason="api_not_configured",
    )

    assert result.analysis_mode == "autonomous"
    assert result.ai_provider == "openai"
    assert result.ai_model == "test-model"
    assert result.fallback_reason == "api_not_configured"
    assert result.requires_human_review is True
    assert result.engineering_confirmation is False


def test_ai_execution_result_rejects_unknown_fallback_reason():
    from app.models.ai_analysis import AIAnalysisExecutionResult

    with pytest.raises(ValidationError):
        AIAnalysisExecutionResult(
            summary="Autonomous result.",
            analysis_mode="autonomous",
            ai_provider="openai",
            ai_model="test-model",
            fallback_reason="unknown_reason",
        )


def test_ai_execution_result_rejects_openai_mode_with_fallback_reason():
    from app.models.ai_analysis import AIAnalysisExecutionResult

    with pytest.raises(ValidationError):
        AIAnalysisExecutionResult(
            summary="OpenAI result.",
            analysis_mode="openai",
            ai_provider="openai",
            ai_model="test-model",
            fallback_reason="provider_unavailable",
        )


def test_ai_execution_result_rejects_autonomous_mode_without_reason():
    from app.models.ai_analysis import AIAnalysisExecutionResult

    with pytest.raises(ValidationError):
        AIAnalysisExecutionResult(
            summary="Autonomous result.",
            analysis_mode="autonomous",
            ai_provider="openai",
            ai_model="test-model",
            fallback_reason=None,
        )


def test_ai_execution_result_rejects_unknown_provider():
    from app.models.ai_analysis import AIAnalysisExecutionResult

    with pytest.raises(ValidationError):
        AIAnalysisExecutionResult(
            summary="Autonomous result.",
            analysis_mode="autonomous",
            ai_provider="unknown-provider",
            ai_model="test-model",
            fallback_reason="provider_unavailable",
        )


def test_ai_execution_result_rejects_blank_model():
    from app.models.ai_analysis import AIAnalysisExecutionResult

    with pytest.raises(ValidationError):
        AIAnalysisExecutionResult(
            summary="Autonomous result.",
            analysis_mode="autonomous",
            ai_provider="openai",
            ai_model="   ",
            fallback_reason="provider_unavailable",
        )


def test_ai_execution_result_tracks_excluded_autonomous_fact_fields():
    from app.models.ai_analysis import AIAnalysisExecutionResult

    result = AIAnalysisExecutionResult(
        summary="Autonomous analysis completed.",
        analysis_mode="autonomous",
        ai_provider="openai",
        ai_model="test-model",
        fallback_reason="ai_disabled",
        excluded_autonomous_fact_fields=[
            "serial_number",
            "manufacturer",
        ],
    )

    assert result.excluded_autonomous_fact_fields == [
        "serial_number",
        "manufacturer",
    ]