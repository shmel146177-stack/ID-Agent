from app.analyzer.document_classifier import DocumentClassifier
from app.models.ai_analysis import AIAnalysisResult, AIFactSuggestion
from app.services.document_analyzer import DocumentAnalyzer


class AutonomousAnalysisBackend:
    """Локальный анализ документа без внешнего AI-провайдера."""

    FACT_CONFIDENCE = 0.8

    def __init__(
        self,
        classifier: DocumentClassifier | None = None,
        analyzer: DocumentAnalyzer | None = None,
    ):
        self.classifier = classifier or DocumentClassifier()
        self.analyzer = analyzer or DocumentAnalyzer()

    def __call__(
        self,
        filename: str,
        text: str,
    ) -> AIAnalysisResult:
        document_type = self.classifier.classify(
            filename,
            text,
        )
        extracted_data = self.analyzer.analyze_text(text)

        facts = []

        for field, raw_value in extracted_data.items():
            if field == "document_type" or raw_value is None:
                continue

            value = str(raw_value).strip()

            if not value:
                continue

            facts.append(
                AIFactSuggestion(
                    field=field,
                    value=value,
                    evidence=value,
                    confidence=self.FACT_CONFIDENCE,
                )
            )

        if document_type == "Не определён":
            document_type = None

        return AIAnalysisResult(
            summary=(
                f"Автономный анализ документа {filename}: "
                f"найдено фактов - {len(facts)}."
            ),
            document_type_suggestion=document_type,
            facts=facts,
            warnings=[
                (
                    "Результат получен автономными "
                    "детерминированными правилами."
                ),
                "Все найденные факты требуют проверки человеком.",
            ],
        )
