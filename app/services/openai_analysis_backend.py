from openai import APIError, RateLimitError

from app.models.ai_analysis import AIAnalysisResult
from app.services.ai_client import AIClient, AIUnavailableError


class OpenAIResponsesBackend:
    """Structured Outputs backend через OpenAI Responses API."""

    DEFAULT_MAX_INPUT_CHARS = 40_000

    SYSTEM_PROMPT = (
        "Ты вспомогательный модуль ID-Agent для анализа инженерных документов. "
        "Используй только факты из предоставленного текста. "
        "Не выдумывай отсутствующие данные. "
        "Любой найденный факт является только предложением для проверки человеком. "
        "Не подтверждай соответствие проекту, качество работ, приемку работ "
        "или иные инженерные факты. "
        "Для найденных фактов по возможности указывай краткое текстовое evidence."
    )

    def __init__(
        self,
        ai_client: AIClient | None = None,
        max_input_chars: int = DEFAULT_MAX_INPUT_CHARS,
    ):
        if max_input_chars <= 0:
            raise ValueError(
                "Максимальный размер AI-входа должен быть положительным"
            )

        self.ai_client = ai_client or AIClient()
        self.max_input_chars = max_input_chars

    def __call__(
        self,
        filename: str,
        text: str,
        knowledge_context: str | None = None,
    ) -> AIAnalysisResult:
        document_name = (filename or "").strip() or "без имени"
        document_text = (text or "").strip()

        if not document_text:
            raise ValueError(
                "Для OpenAI-анализа требуется текст документа"
            )

        was_truncated = len(document_text) > self.max_input_chars
        input_text = document_text[: self.max_input_chars]
        knowledge_text = (knowledge_context or "").strip()

        if knowledge_text:
            input_text = (
                f"{input_text}\n\n"
                "Knowledge context (source-bound reference):\n"
                f"{knowledge_text}"
            )

        client = self.ai_client.get_client()

        try:
            response = client.responses.parse(
                model=self.ai_client.settings.model,
                input=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Имя файла: {document_name}\n\n"
                            f"Текст документа:\n{input_text}"
                        ),
                    },
                ],
                text_format=AIAnalysisResult,
            )
        except RateLimitError as exc:
            if getattr(exc, "code", None) == "credit_balance_exhausted":
                raise AIUnavailableError(
                    "OpenAI API недоступен: исчерпан баланс API"
                ) from exc

            raise AIUnavailableError(
                "OpenAI API временно недоступен: превышен лимит запросов"
            ) from exc

        except APIError as exc:
            raise AIUnavailableError(
                "OpenAI API временно недоступен"
            ) from exc
        result = response.output_parsed

        if result is None:
            raise AIUnavailableError(
                "OpenAI не вернул структурированный результат"
            )

        if not isinstance(result, AIAnalysisResult):
            raise TypeError(
                "OpenAI должен вернуть AIAnalysisResult"
            )

        if was_truncated:
            result = result.model_copy(
                update={
                    "warnings": [
                        *result.warnings,
                        (
                            "Текст для AI-анализа был ограничен "
                            f"первыми {self.max_input_chars} символами."
                        ),
                    ]
                }
            )

        return result
