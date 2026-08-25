import pytest

from app.models.ai_analysis import AIAnalysisResult, AIFactSuggestion
from app.services.ai_client import AIClient, AIUnavailableError
from app.services.ai_document_analysis import AIDocumentAnalysisService
from app.services.ai_settings import AISettings


def create_ai_client(api_key=None):
    settings = AISettings(
        api_key=api_key,
        model="test-model",
    )
    return AIClient(settings=settings)


def test_ai_document_analysis_handles_empty_text():
    service = AIDocumentAnalysisService(
        ai_client=create_ai_client(),
    )

    result = service.analyze_text(
        "document.pdf",
        "   ",
    )

    assert result.requires_human_review is True
    assert result.engineering_confirmation is False
    assert "текст отсутствует" in result.summary
    assert result.warnings == [
        "Для AI-анализа требуется текст документа.",
    ]


def test_ai_document_analysis_falls_back_without_api_key():
    service = AIDocumentAnalysisService(
        ai_client=create_ai_client(),
    )

    result = service.analyze_text(
        "document.pdf",
        "Текст инженерного документа.",
    )

    assert "OpenAI API не настроен" in result.summary
    assert "Отсутствует OPENAI_API_KEY." in result.warnings
    assert result.requires_human_review is True
    assert result.engineering_confirmation is False


def test_ai_document_analysis_does_not_call_missing_backend():
    service = AIDocumentAnalysisService(
        ai_client=create_ai_client("test-key"),
    )

    result = service.analyze_text(
        "document.pdf",
        "Текст инженерного документа.",
    )

    assert "backend модели еще не подключен" in result.summary
    assert result.warnings == [
        "OpenAI настроен, но вызов модели пока отключен.",
    ]


def test_ai_document_analysis_uses_configured_backend():
    calls = []

    def backend(filename, text):
        calls.append((filename, text))
        return AIAnalysisResult(
            summary="Найден предполагаемый номер договора.",
            document_type_suggestion="Договор",
            facts=[
                AIFactSuggestion(
                    field="contract_number",
                    value="123/26",
                    evidence="Договор №123/26",
                    confidence=0.95,
                )
            ],
        )

    service = AIDocumentAnalysisService(
        ai_client=create_ai_client("test-key"),
        analysis_backend=backend,
    )

    result = service.analyze_text(
        "contract.pdf",
        "Договор №123/26",
    )

    assert calls == [
        (
            "contract.pdf",
            "Договор №123/26",
        )
    ]
    assert result.document_type_suggestion == "Договор"
    assert result.facts[0].field == "contract_number"
    assert result.facts[0].value == "123/26"
    assert result.requires_human_review is True
    assert result.engineering_confirmation is False


def test_ai_document_analysis_rejects_invalid_backend_result():
    def backend(filename, text):
        return {
            "summary": "Неправильный тип результата",
        }

    service = AIDocumentAnalysisService(
        ai_client=create_ai_client("test-key"),
        analysis_backend=backend,
    )

    with pytest.raises(
        TypeError,
        match="AIAnalysisResult",
    ):
        service.analyze_text(
            "document.pdf",
            "Текст документа.",
        )

def test_ai_document_analysis_with_openai_builds_backend():
    ai_client = create_ai_client("test-key")

    service = AIDocumentAnalysisService.with_openai(
        ai_client=ai_client,
        max_input_chars=1234,
    )

    assert service.ai_client is ai_client
    assert service.analysis_backend.ai_client is ai_client
    assert service.analysis_backend.max_input_chars == 1234



def test_ai_document_analysis_falls_back_when_backend_unavailable():
    def backend(filename, text):
        raise AIUnavailableError("OpenAI временно недоступен")

    service = AIDocumentAnalysisService(
        ai_client=create_ai_client("test-key"),
        analysis_backend=backend,
    )

    result = service.analyze_text(
        "document.pdf",
        "Текст инженерного документа.",
    )

    assert result.requires_human_review is True
    assert result.engineering_confirmation is False
    assert "AI-анализ" in result.summary
    assert "временно недоступен" in result.summary
    assert "Детерминированный анализ ID-Agent остается доступен." in (
        result.warnings
    )
