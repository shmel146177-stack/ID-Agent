from collections.abc import Callable

from app.models.ai_analysis import AIAnalysisResult
from app.services.ai_client import AIClient


class AIDocumentAnalysisService:
    """AI-анализ текста документа с безопасным fallback-режимом."""

    def __init__(
        self,
        ai_client: AIClient | None = None,
        analysis_backend: (
            Callable[[str, str], AIAnalysisResult] | None
        ) = None,
    ):
        self.ai_client = ai_client or AIClient()
        self.analysis_backend = analysis_backend

    def analyze_text(
        self,
        filename: str,
        text: str,
    ) -> AIAnalysisResult:
        document_name = (filename or "").strip() or "без имени"
        document_text = (text or "").strip()

        if not document_text:
            return AIAnalysisResult(
                summary=(
                    f"AI-анализ документа {document_name} "
                    "не выполнен: текст отсутствует."
                ),
                warnings=[
                    "Для AI-анализа требуется текст документа.",
                ],
            )

        if not self.ai_client.configured:
            return AIAnalysisResult(
                summary=(
                    f"AI-анализ документа {document_name} "
                    "не выполнен: OpenAI API не настроен."
                ),
                warnings=[
                    "Отсутствует OPENAI_API_KEY.",
                    "Детерминированный анализ ID-Agent остается доступен.",
                ],
            )

        if self.analysis_backend is None:
            return AIAnalysisResult(
                summary=(
                    f"AI-анализ документа {document_name} "
                    "не выполнен: backend модели еще не подключен."
                ),
                warnings=[
                    "OpenAI настроен, но вызов модели пока отключен.",
                ],
            )

        result = self.analysis_backend(
            document_name,
            document_text,
        )

        if not isinstance(result, AIAnalysisResult):
            raise TypeError(
                "AI backend должен возвращать AIAnalysisResult"
            )

        return result
