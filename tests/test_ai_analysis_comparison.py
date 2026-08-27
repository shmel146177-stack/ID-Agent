from app.models.ai_analysis import (
    AIAnalysisResult,
    AIFactSuggestion,
)
from app.services.ai_analysis_comparison import (
    AIAnalysisComparisonService,
)


def test_ai_comparison_detects_match_and_conflict():
    deterministic = {
        "document_type": "Чертеж",
        "drawing_number": "A-01",
    }

    ai_analysis = AIAnalysisResult(
        summary="AI suggestions",
        facts=[
            AIFactSuggestion(
                field="drawing_number",
                value="A-01",
                confidence=0.95,
            ),
            AIFactSuggestion(
                field="document_type",
                value="Паспорт",
                confidence=0.80,
            ),
        ],
    )

    service = AIAnalysisComparisonService()

    result = service.compare(
        deterministic,
        ai_analysis,
    )

    assert result["matches"] == [
        {
            "field": "drawing_number",
            "value": "A-01",
            "confidence": 0.95,
        }
    ]

    assert result["conflicts"] == [
        {
            "field": "document_type",
            "deterministic_value": "Чертеж",
            "ai_value": "Паспорт",
            "confidence": 0.80,
        }
    ]

    assert result["requires_human_review"] is True


def test_ai_comparison_ignores_unknown_deterministic_field():
    deterministic = {
        "document_type": "Чертеж",
    }

    ai_analysis = AIAnalysisResult(
        summary="AI suggestions",
        facts=[
            AIFactSuggestion(
                field="drawing_number",
                value="A-01",
                confidence=0.90,
            ),
        ],
    )

    result = AIAnalysisComparisonService().compare(
        deterministic,
        ai_analysis,
    )

    assert result["matches"] == []
    assert result["conflicts"] == []
    assert result["suggestions"] == [
        {
            "field": "drawing_number",
            "value": "A-01",
            "confidence": 0.90,
        }
    ]
    assert result["requires_human_review"] is True


def test_ai_comparison_handles_empty_facts():
    deterministic = {
        "document_type": "Чертеж",
    }

    ai_analysis = AIAnalysisResult(
        summary="No facts",
    )

    result = AIAnalysisComparisonService().compare(
        deterministic,
        ai_analysis,
    )

    assert result == {
        "matches": [],
        "conflicts": [],
        "suggestions": [],
        "requires_human_review": True,
    }

def test_ai_comparison_treats_missing_value_as_suggestion():
    deterministic = {
        "drawing_number": None,
    }

    ai_analysis = AIAnalysisResult(
        summary="AI suggestions",
        facts=[
            AIFactSuggestion(
                field="drawing_number",
                value="A-01",
                confidence=0.90,
            ),
        ],
    )

    result = AIAnalysisComparisonService().compare(
        deterministic,
        ai_analysis,
    )

    assert result["matches"] == []
    assert result["conflicts"] == []
    assert result["suggestions"] == [
        {
            "field": "drawing_number",
            "value": "A-01",
            "confidence": 0.90,
        }
    ]
    assert result["requires_human_review"] is True

def test_ai_comparison_treats_empty_value_as_suggestion():
    deterministic = {
        "drawing_number": "",
    }

    ai_analysis = AIAnalysisResult(
        summary="AI suggestions",
        facts=[
            AIFactSuggestion(
                field="drawing_number",
                value="A-01",
                confidence=0.90,
            ),
        ],
    )

    result = AIAnalysisComparisonService().compare(
        deterministic,
        ai_analysis,
    )

    assert result["matches"] == []
    assert result["conflicts"] == []
    assert result["suggestions"] == [
        {
            "field": "drawing_number",
            "value": "A-01",
            "confidence": 0.90,
        }
    ]
    assert result["requires_human_review"] is True

def test_ai_comparison_treats_whitespace_value_as_suggestion():
    deterministic = {
        "drawing_number": "   ",
    }

    ai_analysis = AIAnalysisResult(
        summary="AI suggestions",
        facts=[
            AIFactSuggestion(
                field="drawing_number",
                value="A-01",
                confidence=0.90,
            ),
        ],
    )

    result = AIAnalysisComparisonService().compare(
        deterministic,
        ai_analysis,
    )

    assert result["matches"] == []
    assert result["conflicts"] == []
    assert result["suggestions"] == [
        {
            "field": "drawing_number",
            "value": "A-01",
            "confidence": 0.90,
        }
    ]
    assert result["requires_human_review"] is True

def test_ai_comparison_ignores_surrounding_string_whitespace():
    deterministic = {
        "drawing_number": "  A-01  ",
    }

    ai_analysis = AIAnalysisResult(
        summary="AI suggestions",
        facts=[
            AIFactSuggestion(
                field="drawing_number",
                value="A-01",
                confidence=0.95,
            ),
        ],
    )

    result = AIAnalysisComparisonService().compare(
        deterministic,
        ai_analysis,
    )

    assert result["matches"] == [
        {
            "field": "drawing_number",
            "value": "A-01",
            "confidence": 0.95,
        }
    ]
    assert result["conflicts"] == []
    assert result["suggestions"] == []
    assert result["requires_human_review"] is True
