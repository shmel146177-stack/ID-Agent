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

def test_ai_execution_result_rejects_openai_excluded_autonomous_fields():
    from app.models.ai_analysis import AIAnalysisExecutionResult

    with pytest.raises(ValidationError):
        AIAnalysisExecutionResult(
            summary="OpenAI analysis completed.",
            analysis_mode="openai",
            ai_provider="openai",
            ai_model="test-model",
            excluded_autonomous_fact_fields=[
                "serial_number",
            ],
        )


def test_ai_execution_result_rejects_blank_excluded_autonomous_field():
    from app.models.ai_analysis import AIAnalysisExecutionResult

    with pytest.raises(ValidationError):
        AIAnalysisExecutionResult(
            summary="Autonomous analysis completed.",
            analysis_mode="autonomous",
            ai_provider="openai",
            ai_model="test-model",
            fallback_reason="ai_disabled",
            excluded_autonomous_fact_fields=[
                "   ",
            ],
        )


def test_ai_execution_result_rejects_duplicate_excluded_autonomous_fields():
    from app.models.ai_analysis import AIAnalysisExecutionResult

    with pytest.raises(ValidationError):
        AIAnalysisExecutionResult(
            summary="Autonomous analysis completed.",
            analysis_mode="autonomous",
            ai_provider="openai",
            ai_model="test-model",
            fallback_reason="ai_disabled",
            excluded_autonomous_fact_fields=[
                "serial_number",
                "serial_number",
            ],
        )

def test_autonomous_analysis_result_rejects_blank_excluded_fact_field():
    from app.models.ai_analysis import AutonomousAnalysisResult

    with pytest.raises(ValidationError):
        AutonomousAnalysisResult(
            summary="Autonomous analysis completed.",
            excluded_autonomous_fact_fields=[
                "   ",
            ],
        )


def test_autonomous_analysis_result_rejects_duplicate_excluded_fact_fields():
    from app.models.ai_analysis import AutonomousAnalysisResult

    with pytest.raises(ValidationError):
        AutonomousAnalysisResult(
            summary="Autonomous analysis completed.",
            excluded_autonomous_fact_fields=[
                "serial_number",
                "serial_number",
            ],
        )

def test_autonomous_analysis_result_tracks_exclusion_reasons():
    from app.models.ai_analysis import AutonomousAnalysisResult

    result = AutonomousAnalysisResult(
        summary="Autonomous analysis completed.",
        excluded_autonomous_fact_fields=[
            "serial_number",
            "ip",
        ],
        excluded_autonomous_fact_reasons={
            "serial_number": "missing_evidence",
            "ip": "insufficient_context",
        },
    )

    assert result.excluded_autonomous_fact_reasons == {
        "serial_number": "missing_evidence",
        "ip": "insufficient_context",
    }


def test_autonomous_analysis_result_rejects_unknown_exclusion_reason():
    from app.models.ai_analysis import AutonomousAnalysisResult

    with pytest.raises(ValidationError):
        AutonomousAnalysisResult(
            summary="Autonomous analysis completed.",
            excluded_autonomous_fact_fields=[
                "serial_number",
            ],
            excluded_autonomous_fact_reasons={
                "serial_number": "unknown_reason",
            },
        )


def test_autonomous_analysis_result_rejects_mismatched_exclusion_reasons():
    from app.models.ai_analysis import AutonomousAnalysisResult

    with pytest.raises(ValidationError):
        AutonomousAnalysisResult(
            summary="Autonomous analysis completed.",
            excluded_autonomous_fact_fields=[
                "serial_number",
            ],
            excluded_autonomous_fact_reasons={
                "ip": "insufficient_context",
            },
        )


def test_ai_execution_result_rejects_openai_exclusion_reasons():
    from app.models.ai_analysis import AIAnalysisExecutionResult

    with pytest.raises(ValidationError):
        AIAnalysisExecutionResult(
            summary="OpenAI analysis completed.",
            analysis_mode="openai",
            ai_provider="openai",
            ai_model="test-model",
            excluded_autonomous_fact_reasons={
                "ip": "insufficient_context",
            },
        )

def test_autonomous_analysis_result_counts_exclusion_reasons():
    from app.models.ai_analysis import AutonomousAnalysisResult

    result = AutonomousAnalysisResult(
        summary="Autonomous analysis completed.",
        excluded_autonomous_fact_fields=[
            "serial_number",
            "ip",
            "frequency",
        ],
        excluded_autonomous_fact_reasons={
            "serial_number": "missing_evidence",
            "ip": "insufficient_context",
            "frequency": "insufficient_context",
        },
    )

    expected_counts = {
        "missing_evidence": 1,
        "insufficient_context": 2,
    }

    assert (
        result.excluded_autonomous_fact_reason_counts
        == expected_counts
    )
    assert result.model_dump()[
        "excluded_autonomous_fact_reason_counts"
    ] == expected_counts


def test_autonomous_analysis_result_tracks_excluded_fact_details():
    from app.models.ai_analysis import (
        AutonomousAnalysisResult,
        AutonomousFactExclusion,
    )

    result = AutonomousAnalysisResult(
        summary="Autonomous analysis completed.",
        excluded_autonomous_fact_fields=[
            "serial_number",
            "ip",
        ],
        excluded_autonomous_fact_reasons={
            "serial_number": "missing_evidence",
            "ip": "insufficient_context",
        },
        excluded_autonomous_facts=[
            AutonomousFactExclusion(
                field="serial_number",
                value="ABC-123",
                reason="missing_evidence",
            ),
            AutonomousFactExclusion(
                field="ip",
                value="IP66",
                reason="insufficient_context",
                evidence="Component enclosure IP66.",
            ),
        ],
    )

    assert result.model_dump()["excluded_autonomous_facts"] == [
        {
            "field": "serial_number",
            "value": "ABC-123",
            "reason": "missing_evidence",
            "evidence": None,
        },
        {
            "field": "ip",
            "value": "IP66",
            "reason": "insufficient_context",
            "evidence": "Component enclosure IP66.",
        },
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {
            "field": "   ",
            "value": "ABC-123",
            "reason": "missing_evidence",
        },
        {
            "field": "serial_number",
            "value": "   ",
            "reason": "missing_evidence",
        },
        {
            "field": "serial_number",
            "value": "ABC-123",
            "reason": "missing_evidence",
            "evidence": "Serial number ABC-123.",
        },
        {
            "field": "ip",
            "value": "IP66",
            "reason": "insufficient_context",
        },
        {
            "field": "ip",
            "value": "IP66",
            "reason": "insufficient_context",
            "evidence": "   ",
        },
    ],
)
def test_autonomous_fact_exclusion_rejects_invalid_details(payload):
    from app.models.ai_analysis import AutonomousFactExclusion

    with pytest.raises(ValidationError):
        AutonomousFactExclusion(**payload)


@pytest.mark.parametrize(
    (
        "excluded_fields",
        "excluded_reasons",
        "excluded_facts",
    ),
    [
        (
            ["serial_number"],
            {"serial_number": "missing_evidence"},
            [
                {
                    "field": "ip",
                    "value": "IP66",
                    "reason": "insufficient_context",
                    "evidence": "Component enclosure IP66.",
                },
            ],
        ),
        (
            ["serial_number"],
            {"serial_number": "missing_evidence"},
            [
                {
                    "field": "serial_number",
                    "value": "ABC-123",
                    "reason": "insufficient_context",
                    "evidence": "Serial number ABC-123.",
                },
            ],
        ),
        (
            ["serial_number"],
            {"serial_number": "missing_evidence"},
            [
                {
                    "field": "serial_number",
                    "value": "ABC-123",
                    "reason": "missing_evidence",
                },
                {
                    "field": "serial_number",
                    "value": "XYZ-789",
                    "reason": "missing_evidence",
                },
            ],
        ),
        (
            ["ip", "frequency"],
            {
                "ip": "insufficient_context",
                "frequency": "insufficient_context",
            },
            [
                {
                    "field": "frequency",
                    "value": "50 Hz",
                    "reason": "insufficient_context",
                    "evidence": "Contactor frequency 50 Hz.",
                },
                {
                    "field": "ip",
                    "value": "IP66",
                    "reason": "insufficient_context",
                    "evidence": "Component enclosure IP66.",
                },
            ],
        ),
    ],
)
def test_autonomous_analysis_result_rejects_inconsistent_excluded_fact_details(
    excluded_fields,
    excluded_reasons,
    excluded_facts,
):
    from app.models.ai_analysis import AutonomousAnalysisResult

    with pytest.raises(ValidationError):
        AutonomousAnalysisResult(
            summary="Autonomous analysis completed.",
            excluded_autonomous_fact_fields=excluded_fields,
            excluded_autonomous_fact_reasons=excluded_reasons,
            excluded_autonomous_facts=excluded_facts,
        )


def test_ai_execution_result_rejects_openai_excluded_autonomous_facts():
    from app.models.ai_analysis import AIAnalysisExecutionResult

    with pytest.raises(ValidationError):
        AIAnalysisExecutionResult(
            summary="OpenAI analysis completed.",
            analysis_mode="openai",
            ai_provider="openai",
            ai_model="test-model",
            excluded_autonomous_facts=[
                {
                    "field": "ip",
                    "value": "IP66",
                    "reason": "insufficient_context",
                    "evidence": "Component enclosure IP66.",
                },
            ],
        )
