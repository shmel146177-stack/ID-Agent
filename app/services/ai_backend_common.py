"""Общие части AI-бэкендов: промпт, обрезка входа, разбор ошибок провайдера."""

import json
from collections.abc import Callable
from typing import NoReturn, TypeVar

from openai import APIError, AuthenticationError, RateLimitError
from pydantic import ValidationError

from app.models.ai_analysis import AIAnalysisResult
from app.services.ai_client import AIUnavailableError

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

PROVIDER_LABELS = {
    "openai": "OpenAI",
    "deepseek": "DeepSeek",
    "local-qwen": "Локальная модель",
}

ResultT = TypeVar("ResultT")


def provider_label(provider_name: str) -> str:
    """Человекочитаемое имя провайдера для сообщений об ошибках."""

    return PROVIDER_LABELS.get(provider_name, provider_name or "Провайдер")


def validate_max_input_chars(max_input_chars: int) -> None:
    if max_input_chars <= 0:
        raise ValueError("Максимальный размер AI-входа должен быть положительным")


def build_user_content(
    document_name: str,
    text: str,
    knowledge_context: str | None,
    max_input_chars: int,
) -> tuple[str, bool]:
    """Собрать текст запроса и признак обрезки."""

    document_text = text.strip()
    was_truncated = len(document_text) > max_input_chars
    input_text = document_text[:max_input_chars]
    knowledge_text = (knowledge_context or "").strip()

    if knowledge_text:
        input_text = (
            f"{input_text}\n\n"
            "Knowledge context (source-bound reference):\n"
            f"{knowledge_text}"
        )

    document_label = document_name.strip() or "без имени"

    content = f"Имя файла: {document_label}\n\nТекст документа:\n{input_text}"

    return content, was_truncated


def apply_truncation_warning(
    result: AIAnalysisResult,
    was_truncated: bool,
    max_input_chars: int,
) -> AIAnalysisResult:
    """Отметить в результате, что вход был ограничен."""

    if not was_truncated:
        return result

    return result.model_copy(
        update={
            "warnings": [
                *result.warnings,
                (
                    "Текст для AI-анализа был ограничен "
                    f"первыми {max_input_chars} символами."
                ),
            ]
        }
    )


def ensure_structured_result(result: object, label: str) -> AIAnalysisResult:
    """Проверить структурированный ответ провайдера."""

    if result is None:
        raise AIUnavailableError(
            f"{label} не вернул структурированный результат",
            reason="invalid_provider_response",
        )

    if not isinstance(result, AIAnalysisResult):
        raise TypeError(f"{label} должен вернуть AIAnalysisResult")

    return result


def build_json_instruction() -> str:
    """Инструкция со схемой ответа для режима json_object.

    Провайдеры вроде DeepSeek не принимают строгую схему в response_format,
    поэтому схему передаём в тексте запроса.
    """

    schema = AIAnalysisResult.model_json_schema()

    return (
        "Верни только JSON без пояснений и без markdown, "
        "соответствующий схеме:\n"
        f"{json.dumps(schema, ensure_ascii=False)}"
    )


def run_provider_call(call: Callable[[], ResultT], label: str) -> ResultT:
    """Выполнить обращение к провайдеру и перевести его ошибки."""

    try:
        return call()
    except (RateLimitError, APIError) as error:
        raise_provider_error(error, label)


def raise_provider_error(error: Exception, label: str) -> NoReturn:
    """Перевести ошибку провайдера в AIUnavailableError с причиной."""

    if isinstance(error, AuthenticationError):
        raise AIUnavailableError(
            f"{label} API отклонил ключ: проверьте ID_AGENT_AI_API_KEY",
            reason="invalid_credential",
        ) from error

    if isinstance(error, RateLimitError):
        if getattr(error, "code", None) == "credit_balance_exhausted":
            raise AIUnavailableError(
                f"{label} API недоступен: исчерпан баланс API",
                reason="credit_balance_exhausted",
            ) from error

        raise AIUnavailableError(
            f"{label} API временно недоступен: превышен лимит запросов",
            reason="rate_limit_exceeded",
        ) from error

    if isinstance(error, APIError):
        raise AIUnavailableError(
            f"{label} API временно недоступен",
            reason="provider_unavailable",
        ) from error

    raise error


def parse_structured_text(payload: str | None) -> AIAnalysisResult | None:
    """Разобрать текстовый ответ провайдера, который не отдал структуру."""

    text = (payload or "").strip()
    if not text:
        return None

    candidates = [text]

    fenced = _strip_code_fence(text)
    if fenced != text:
        candidates.insert(0, fenced)

    for candidate in candidates:
        try:
            return AIAnalysisResult.model_validate_json(candidate)
        except ValidationError:
            continue

    return None


def _strip_code_fence(text: str) -> str:
    """Убрать markdown-обёртку вида ```json ... ``` вокруг JSON."""

    if not text.startswith("```"):
        return text

    body = text[3:]

    newline = body.find("\n")
    if newline != -1:
        body = body[newline + 1 :]

    end = body.rfind("```")
    if end != -1:
        body = body[:end]

    return body.strip()
