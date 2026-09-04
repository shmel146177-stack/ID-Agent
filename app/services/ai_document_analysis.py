from collections.abc import Callable

from app.models.ai_analysis import (
    AIAnalysisExecutionResult,
    AIAnalysisResult,
)
from app.services.ai_client import AIClient, AIUnavailableError


class AIDocumentAnalysisService:
    """AI-анализ текста документа с безопасным fallback-режимом."""

    def __init__(
        self,
        ai_client: AIClient | None = None,
        analysis_backend: Callable[..., AIAnalysisResult] | None = None,
    ):
        self.ai_client = ai_client or AIClient()
        self.analysis_backend = analysis_backend

    @classmethod
    def with_openai(
        cls,
        ai_client: AIClient | None = None,
        max_input_chars: int = 40_000,
    ) -> "AIDocumentAnalysisService":
        from app.services.openai_analysis_backend import (
            OpenAIResponsesBackend,
        )

        client = ai_client or AIClient()

        return cls(
            ai_client=client,
            analysis_backend=OpenAIResponsesBackend(
                ai_client=client,
                max_input_chars=max_input_chars,
            ),
        )

    def _build_execution_result(
        self,
        result: AIAnalysisResult,
        *,
        analysis_mode: str,
        fallback_reason: str | None = None,
    ) -> AIAnalysisExecutionResult:
        return AIAnalysisExecutionResult(
            **result.model_dump(),
            analysis_mode=analysis_mode,
            ai_provider="openai",
            ai_model=self.ai_client.settings.model,
            fallback_reason=fallback_reason,
        )

    def analyze_text(
        self,
        filename: str,
        text: str,
        knowledge_context: str | None = None,
    ) -> AIAnalysisExecutionResult:
        document_name = (filename or "").strip() or "без имени"
        document_text = (text or "").strip()
        knowledge_text = (knowledge_context or "").strip()

        if not document_text:
            return self._build_execution_result(
                AIAnalysisResult(
                    summary=(
                        f"AI-анализ документа {document_name} "
                        "не выполнен: текст отсутствует."
                    ),
                    warnings=[
                        "Для AI-анализа требуется текст документа.",
                    ],
                ),
                analysis_mode="autonomous",
                fallback_reason="empty_text",
            )

        if not self.ai_client.configured:
            return self._build_execution_result(
                AIAnalysisResult(
                    summary=(
                        f"AI-анализ документа {document_name} "
                        "не выполнен: OpenAI API не настроен."
                    ),
                    warnings=[
                        "Отсутствует OPENAI_API_KEY.",
                        "Детерминированный анализ ID-Agent остается доступен.",
                    ],
                ),
                analysis_mode="autonomous",
                fallback_reason="api_not_configured",
            )

        if self.analysis_backend is None:
            return self._build_execution_result(
                AIAnalysisResult(
                    summary=(
                        f"AI-анализ документа {document_name} "
                        "не выполнен: backend модели еще не подключен."
                    ),
                    warnings=[
                        "OpenAI настроен, но вызов модели пока отключен.",
                    ],
                ),
                analysis_mode="autonomous",
                fallback_reason=(
                    "ai_disabled"
                    if not self.ai_client.settings.enabled
                    else "backend_not_connected"
                ),
            )

        try:
            if knowledge_text:
                result = self.analysis_backend(
                    document_name,
                    document_text,
                    knowledge_text,
                )
            else:
                result = self.analysis_backend(
                    document_name,
                    document_text,
                )
        except AIUnavailableError as exc:
            return self._build_execution_result(
                AIAnalysisResult(
                    summary=(
                        f"AI-анализ документа {document_name} "
                        f"временно недоступен: {exc}"
                    ),
                    warnings=[
                        "Детерминированный анализ ID-Agent остается доступен.",
                    ],
                ),
                analysis_mode="autonomous",
                fallback_reason="provider_unavailable",
            )

        if not isinstance(result, AIAnalysisResult):
            raise TypeError(
                "AI backend должен возвращать AIAnalysisResult"
            )

        return self._build_execution_result(
            result,
            analysis_mode="openai",
        )
