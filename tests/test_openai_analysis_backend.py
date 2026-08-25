import pytest

from app.models.ai_analysis import AIAnalysisResult
from app.services.ai_client import AIClient, AIUnavailableError
from app.services.ai_settings import AISettings
from app.services.openai_analysis_backend import OpenAIResponsesBackend


class ResponseStub:
    def __init__(self, output_parsed):
        self.output_parsed = output_parsed


class ResponsesStub:
    def __init__(self, output_parsed):
        self.output_parsed = output_parsed
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return ResponseStub(self.output_parsed)


class OpenAIClientStub:
    def __init__(self, output_parsed):
        self.responses = ResponsesStub(output_parsed)


class ClientFactoryStub:
    def __init__(self, client):
        self.client = client
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.client


def create_backend(
    result,
    max_input_chars=40_000,
):
    openai_stub = OpenAIClientStub(result)
    factory = ClientFactoryStub(openai_stub)

    ai_client = AIClient(
        settings=AISettings(
            api_key="test-key",
            model="test-model",
        ),
        client_factory=factory,
    )

    backend = OpenAIResponsesBackend(
        ai_client=ai_client,
        max_input_chars=max_input_chars,
    )

    return backend, openai_stub, factory


def test_openai_backend_rejects_invalid_input_limit():
    with pytest.raises(
        ValueError,
        match="положительным",
    ):
        OpenAIResponsesBackend(
            max_input_chars=0,
        )


def test_openai_backend_rejects_empty_text_without_api_call():
    result = AIAnalysisResult(
        summary="unused",
    )
    backend, openai_stub, factory = create_backend(result)

    with pytest.raises(
        ValueError,
        match="текст документа",
    ):
        backend(
            "document.pdf",
            "   ",
        )

    assert factory.calls == []
    assert openai_stub.responses.calls == []


def test_openai_backend_calls_responses_parse_with_structured_model():
    expected = AIAnalysisResult(
        summary="Документ проанализирован.",
        document_type_suggestion="Протокол",
    )
    backend, openai_stub, factory = create_backend(expected)

    result = backend(
        "protocol.pdf",
        "Протокол измерения сопротивления.",
    )

    assert result is expected
    assert factory.calls == [
        {
            "api_key": "test-key",
        }
    ]

    assert len(openai_stub.responses.calls) == 1
    call = openai_stub.responses.calls[0]

    assert call["model"] == "test-model"
    assert call["text_format"] is AIAnalysisResult

    assert call["input"][0]["role"] == "system"
    assert call["input"][1]["role"] == "user"

    user_content = call["input"][1]["content"]

    assert "protocol.pdf" in user_content
    assert "Протокол измерения сопротивления." in user_content


def test_openai_backend_rejects_missing_structured_result():
    backend, _, _ = create_backend(None)

    with pytest.raises(
        AIUnavailableError,
        match="структурированный результат",
    ):
        backend(
            "document.pdf",
            "Текст документа.",
        )


def test_openai_backend_rejects_wrong_result_type():
    backend, _, _ = create_backend(
        {
            "summary": "wrong type",
        }
    )

    with pytest.raises(
        TypeError,
        match="AIAnalysisResult",
    ):
        backend(
            "document.pdf",
            "Текст документа.",
        )


def test_openai_backend_limits_input_and_adds_warning():
    expected = AIAnalysisResult(
        summary="Документ проанализирован.",
    )
    backend, openai_stub, _ = create_backend(
        expected,
        max_input_chars=10,
    )

    result = backend(
        "document.pdf",
        "1234567890ABCDEFGHIJ",
    )

    call = openai_stub.responses.calls[0]
    user_content = call["input"][1]["content"]

    assert "1234567890" in user_content
    assert "ABCDEFGHIJ" not in user_content

    assert result.warnings == [
        "Текст для AI-анализа был ограничен первыми 10 символами.",
    ]

    assert result.requires_human_review is True
    assert result.engineering_confirmation is False
