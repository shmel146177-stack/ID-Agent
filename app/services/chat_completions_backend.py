"""Анализ документа через Chat Completions API.

Нужен провайдерам, которые не поддерживают Responses API: DeepSeek, локальный
сервер LM Studio и другие OpenAI-совместимые эндпоинты. Сначала запрос идёт
со строгой схемой; если провайдер её не принимает, запрос повторяется в режиме
json_object со схемой в тексте, и отказ запоминается — следующие документы
сразу идут запасным путём. Пустой ответ повторяется один раз: DeepSeek
предупреждает о таких случаях в своей документации. Текстовый ответ
разбирается, а при неудаче поднимается AIUnavailableError с причиной
invalid_provider_response.
"""

from openai import BadRequestError

from app.models.ai_analysis import AIAnalysisResult
from app.services.ai_backend_common import (
    DEFAULT_MAX_INPUT_CHARS,
    SYSTEM_PROMPT,
    apply_truncation_warning,
    build_json_instruction,
    build_user_content,
    ensure_structured_result,
    parse_structured_text,
    provider_label,
    run_provider_call,
    validate_max_input_chars,
)
from app.services.ai_client import AIClient


class ChatCompletionsBackend:
    """Structured Outputs backend через Chat Completions API."""

    DEFAULT_MAX_INPUT_CHARS = DEFAULT_MAX_INPUT_CHARS
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def __init__(
        self,
        ai_client: AIClient | None = None,
        max_input_chars: int = DEFAULT_MAX_INPUT_CHARS,
    ):
        validate_max_input_chars(max_input_chars)

        self.ai_client = ai_client or AIClient()
        self.max_input_chars = max_input_chars

        # Поддерживает ли провайдер строгую схему. None — ещё неизвестно.
        self._schema_supported: bool | None = None

    @property
    def label(self) -> str:
        return provider_label(self.ai_client.settings.provider)

    def __call__(
        self,
        filename: str,
        text: str,
        knowledge_context: str | None = None,
    ) -> AIAnalysisResult:
        document_text = (text or "").strip()

        if not document_text:
            raise ValueError("Для AI-анализа требуется текст документа")

        user_content, was_truncated = build_user_content(
            filename,
            document_text,
            knowledge_context,
            self.max_input_chars,
        )

        client = self.ai_client.get_client()

        result = self._attempt(client, user_content)

        if result is None:
            # Провайдер иногда отвечает пустым содержимым — повторяем один раз.
            result = self._attempt(client, user_content)

        structured = ensure_structured_result(result, self.label)

        return apply_truncation_warning(
            structured,
            was_truncated,
            self.max_input_chars,
        )

    def _attempt(self, client, user_content: str) -> AIAnalysisResult | None:
        """Одно обращение к провайдеру: структура из ответа либо из текста."""

        completion = run_provider_call(
            lambda: self._request(client, user_content),
            self.label,
        )

        message = _first_message(completion)
        result = getattr(message, "parsed", None)

        if result is None:
            result = parse_structured_text(getattr(message, "content", None))

        return result

    def _request(self, client, user_content: str):
        """Запрос со строгой схемой, а при её неприятии — в режиме json_object."""

        if self._schema_supported is False:
            return self._json_object_request(client, user_content)

        try:
            completion = client.chat.completions.parse(
                model=self.ai_client.settings.model,
                messages=self._messages(user_content),
                response_format=AIAnalysisResult,
            )
        except BadRequestError:
            self._schema_supported = False

            return self._json_object_request(client, user_content)

        self._schema_supported = True

        return completion

    def _json_object_request(self, client, user_content: str):
        """Запрос в режиме json_object со схемой в тексте сообщения."""

        return client.chat.completions.create(
            model=self.ai_client.settings.model,
            messages=self._messages(f"{user_content}\n\n{build_json_instruction()}"),
            response_format={"type": "json_object"},
        )

    def _messages(self, user_content: str) -> list[dict]:
        return [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_content,
            },
        ]


def _first_message(completion):
    """Первое сообщение ответа либо None, если список вариантов пуст."""

    choices = getattr(completion, "choices", None) or []

    if not choices:
        return None

    return getattr(choices[0], "message", None)
