import pytest
from openai import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)

from app.models.ai_analysis import AIAnalysisResult
from app.services.ai_client import AIClient, AIUnavailableError
from app.services.ai_document_analysis import AIDocumentAnalysisService
from app.services.ai_settings import (
    PROTOCOL_CHAT_COMPLETIONS,
    PROTOCOL_RESPONSES,
    AISettings,
)
from app.services.chat_completions_backend import ChatCompletionsBackend
from app.services.openai_analysis_backend import OpenAIResponsesBackend


class MessageStub:
    def __init__(self, parsed=None, content=None):
        self.parsed = parsed
        self.content = content


class ChoiceStub:
    def __init__(self, message):
        self.message = message


class CompletionStub:
    def __init__(self, message):
        self.choices = [] if message is None else [ChoiceStub(message)]


class CompletionsStub:
    """Подмена chat.completions: отдаёт заранее заданные ответы по очереди."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def _next(self, kwargs):
        self.calls.append(kwargs)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def parse(self, **kwargs):
        return self._next(kwargs)

    def create(self, **kwargs):
        return self._next(kwargs)


class ChatStub:
    def __init__(self, responses):
        self.completions = CompletionsStub(responses)


class OpenAIClientStub:
    def __init__(self, responses):
        self.chat = ChatStub(responses)


class ClientFactoryStub:
    def __init__(self, client):
        self.client = client
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.client


def create_settings(**overrides):
    values = {
        "api_key": "deepseek-key",
        "model": "deepseek-flash",
        "enabled": True,
        "provider": "deepseek",
        "protocol": PROTOCOL_CHAT_COMPLETIONS,
        "base_url": "https://api.deepseek.com",
    }
    values.update(overrides)

    return AISettings(**values)


def create_backend(responses, max_input_chars=40_000, **settings_overrides):
    openai_stub = OpenAIClientStub(responses)
    factory = ClientFactoryStub(openai_stub)

    ai_client = AIClient(
        settings=create_settings(**settings_overrides),
        client_factory=factory,
    )

    backend = ChatCompletionsBackend(
        ai_client=ai_client,
        max_input_chars=max_input_chars,
    )

    return backend, openai_stub, factory


def test_chat_backend_rejects_invalid_input_limit():
    with pytest.raises(
        ValueError,
        match="положительным",
    ):
        ChatCompletionsBackend(max_input_chars=0)


def test_chat_backend_rejects_empty_text_without_api_call():
    backend, _, factory = create_backend([])

    with pytest.raises(
        ValueError,
        match="текст документа",
    ):
        backend("document.pdf", "   ")

    assert factory.calls == []


def test_chat_backend_calls_completions_parse_with_schema():
    expected = AIAnalysisResult(
        summary="Документ проанализирован.",
        document_type_suggestion="Протокол",
    )
    backend, openai_stub, factory = create_backend(
        [CompletionStub(MessageStub(parsed=expected))]
    )

    result = backend(
        "protocol.pdf",
        "Протокол измерения сопротивления.",
    )

    assert result is expected
    assert factory.calls == [
        {
            "api_key": "deepseek-key",
            "base_url": "https://api.deepseek.com",
        }
    ]

    call = openai_stub.chat.completions.calls[0]

    assert call["model"] == "deepseek-flash"
    assert call["response_format"] is AIAnalysisResult
    assert call["messages"][0]["role"] == "system"
    assert call["messages"][1]["role"] == "user"
    assert "protocol.pdf" in call["messages"][1]["content"]
    assert "Протокол измерения сопротивления." in call["messages"][1]["content"]


def test_chat_backend_parses_json_from_text_answer():
    backend, _, _ = create_backend(
        [CompletionStub(MessageStub(content='{"summary": "Разобрано из текста."}'))]
    )

    result = backend("document.pdf", "Текст документа.")

    assert result.summary == "Разобрано из текста."


def test_chat_backend_parses_json_from_code_fence():
    payload = '```json\n{"summary": "Ответ в обёртке."}\n```'
    backend, _, _ = create_backend([CompletionStub(MessageStub(content=payload))])

    result = backend("document.pdf", "Текст документа.")

    assert result.summary == "Ответ в обёртке."


def test_chat_backend_retries_in_json_object_mode_after_bad_request():
    def bad_request():
        error = BadRequestError.__new__(BadRequestError)
        Exception.__init__(error, "response_format json_schema is unsupported")
        return error

    backend, openai_stub, _ = create_backend(
        [
            bad_request(),
            CompletionStub(MessageStub(content='{"summary": "Повтор удался."}')),
        ]
    )

    result = backend("document.pdf", "Текст документа.")

    assert result.summary == "Повтор удался."
    assert len(openai_stub.chat.completions.calls) == 2

    first_call, retry_call = openai_stub.chat.completions.calls

    assert first_call["response_format"] is AIAnalysisResult
    assert retry_call["response_format"] == {"type": "json_object"}
    assert "соответствующий схеме" in retry_call["messages"][1]["content"]


def test_chat_backend_rejects_unstructured_answer():
    backend, openai_stub, _ = create_backend(
        [
            CompletionStub(MessageStub(content="Извините, не могу.")),
            CompletionStub(MessageStub(content="Извините, не могу.")),
        ]
    )

    with pytest.raises(AIUnavailableError) as error:
        backend("document.pdf", "Текст документа.")

    assert error.value.reason == "invalid_provider_response"
    assert len(openai_stub.chat.completions.calls) == 2


def test_chat_backend_rejects_empty_choices():
    backend, openai_stub, _ = create_backend(
        [
            CompletionStub(None),
            CompletionStub(None),
        ]
    )

    with pytest.raises(
        AIUnavailableError,
        match="структурированный результат",
    ):
        backend("document.pdf", "Текст документа.")

    assert len(openai_stub.chat.completions.calls) == 2


def test_chat_backend_limits_input_and_adds_warning():
    expected = AIAnalysisResult(summary="Документ проанализирован.")
    backend, openai_stub, _ = create_backend(
        [CompletionStub(MessageStub(parsed=expected))],
        max_input_chars=10,
    )

    result = backend("document.pdf", "1234567890ABCDEFGHIJ")

    user_content = openai_stub.chat.completions.calls[0]["messages"][1]["content"]

    assert "1234567890" in user_content
    assert "ABCDEFGHIJ" not in user_content

    assert result.warnings == [
        "Текст для AI-анализа был ограничен первыми 10 символами.",
    ]


def test_chat_backend_translates_connection_error():
    def failing_parse(**kwargs):
        raise APIConnectionError(request=object())

    backend, openai_stub, _ = create_backend([])
    openai_stub.chat.completions.parse = failing_parse

    with pytest.raises(AIUnavailableError) as error:
        backend("document.pdf", "Текст документа.")

    assert error.value.reason == "provider_unavailable"
    assert "DeepSeek API временно недоступен" in str(error.value)


def test_chat_backend_reports_rate_limit():
    def failing_parse(**kwargs):
        exception = RateLimitError.__new__(RateLimitError)
        Exception.__init__(exception, "Rate limit exceeded")
        exception.code = "rate_limit_exceeded"
        raise exception

    backend, openai_stub, _ = create_backend([])
    openai_stub.chat.completions.parse = failing_parse

    with pytest.raises(AIUnavailableError) as error:
        backend("document.pdf", "Текст документа.")

    assert error.value.reason == "rate_limit_exceeded"


def test_with_settings_selects_chat_backend_for_chat_protocol():
    ai_client = AIClient(
        settings=create_settings(),
        client_factory=ClientFactoryStub(OpenAIClientStub([])),
    )

    service = AIDocumentAnalysisService.with_settings(
        ai_client=ai_client,
        max_input_chars=1234,
    )

    assert isinstance(service.analysis_backend, ChatCompletionsBackend)
    assert service.analysis_backend.ai_client is ai_client
    assert service.analysis_backend.max_input_chars == 1234


def test_with_settings_selects_responses_backend_for_openai():
    ai_client = AIClient(
        settings=create_settings(
            provider="openai",
            protocol=PROTOCOL_RESPONSES,
            base_url=None,
        ),
        client_factory=ClientFactoryStub(OpenAIClientStub([])),
    )

    service = AIDocumentAnalysisService.with_settings(ai_client=ai_client)

    assert isinstance(service.analysis_backend, OpenAIResponsesBackend)


def test_analysis_reports_configured_provider_and_model():
    expected = AIAnalysisResult(summary="Документ проанализирован.")
    ai_client = AIClient(
        settings=create_settings(),
        client_factory=ClientFactoryStub(
            OpenAIClientStub([CompletionStub(MessageStub(parsed=expected))])
        ),
    )

    service = AIDocumentAnalysisService.with_settings(ai_client=ai_client)
    result = service.analyze_text("document.pdf", "Текст документа.")

    assert result.ai_provider == "deepseek"
    assert result.ai_model == "deepseek-flash"
    assert result.analysis_mode == "openai"
    assert result.fallback_reason is None


def test_chat_backend_reports_rejected_key():
    def failing_parse(**kwargs):
        exception = AuthenticationError.__new__(AuthenticationError)
        Exception.__init__(exception, "Authentication Fails")
        raise exception

    backend, openai_stub, _ = create_backend([])
    openai_stub.chat.completions.parse = failing_parse

    with pytest.raises(AIUnavailableError) as error:
        backend("document.pdf", "Текст документа.")

    assert error.value.reason == "invalid_credential"
    assert "ID_AGENT_AI_API_KEY" in str(error.value)


def test_chat_backend_repeats_once_after_empty_answer():
    expected = AIAnalysisResult(summary="Ответ со второй попытки.")
    backend, openai_stub, _ = create_backend(
        [
            CompletionStub(MessageStub(content="")),
            CompletionStub(MessageStub(parsed=expected)),
        ]
    )

    result = backend("document.pdf", "Текст документа.")

    assert result is expected
    assert len(openai_stub.chat.completions.calls) == 2


def test_chat_backend_fails_after_two_empty_answers():
    backend, openai_stub, _ = create_backend(
        [
            CompletionStub(MessageStub(content="")),
            CompletionStub(MessageStub(content="   ")),
        ]
    )

    with pytest.raises(AIUnavailableError) as error:
        backend("document.pdf", "Текст документа.")

    assert error.value.reason == "invalid_provider_response"
    assert len(openai_stub.chat.completions.calls) == 2


def test_chat_backend_remembers_rejected_schema():
    def bad_request():
        error = BadRequestError.__new__(BadRequestError)
        Exception.__init__(error, "response_format json_schema is unsupported")
        return error

    answer = '{"summary": "Ответ в режиме json_object."}'

    backend, openai_stub, _ = create_backend(
        [
            bad_request(),
            CompletionStub(MessageStub(content=answer)),
            CompletionStub(MessageStub(content=answer)),
        ]
    )

    first = backend("document.pdf", "Текст документа.")
    second = backend("second.pdf", "Текст второго документа.")

    assert first.summary == "Ответ в режиме json_object."
    assert second.summary == "Ответ в режиме json_object."

    calls = openai_stub.chat.completions.calls

    assert len(calls) == 3
    assert calls[0]["response_format"] is AIAnalysisResult
    assert calls[1]["response_format"] == {"type": "json_object"}
    assert calls[2]["response_format"] == {"type": "json_object"}
