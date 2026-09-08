import re

from app.analyzer.document_classifier import DocumentClassifier
from app.models.ai_analysis import AIAnalysisResult, AIFactSuggestion
from app.services.document_analyzer import DocumentAnalyzer


class AutonomousAnalysisBackend:
    """Локальный анализ документа без внешнего AI-провайдера."""

    FACT_CONFIDENCE = 0.8
    EVIDENCE_MAX_CHARS = 240

    def __init__(
        self,
        classifier: DocumentClassifier | None = None,
        analyzer: DocumentAnalyzer | None = None,
    ):
        self.classifier = classifier or DocumentClassifier()
        self.analyzer = analyzer or DocumentAnalyzer()


    @classmethod
    def _limit_evidence(
        cls,
        evidence: str,
        match_start: int,
        match_end: int,
    ) -> str:
        if len(evidence) <= cls.EVIDENCE_MAX_CHARS:
            return evidence

        match_length = match_end - match_start
        available_context = max(
            0,
            cls.EVIDENCE_MAX_CHARS - match_length,
        )
        fragment_start = max(
            0,
            match_start - available_context // 2,
        )
        fragment_end = min(
            len(evidence),
            fragment_start + cls.EVIDENCE_MAX_CHARS,
        )
        fragment_start = max(
            0,
            fragment_end - cls.EVIDENCE_MAX_CHARS,
        )

        return evidence[
            fragment_start:fragment_end
        ].strip()

    @classmethod
    def _find_evidence(
        cls,
        text: str,
        value: str,
    ) -> str:
        flexible_value = r"\s*".join(
            re.escape(character)
            for character in value
        )

        for source_line in text.splitlines():
            evidence = source_line.strip()

            if not evidence:
                continue

            match = re.search(
                flexible_value,
                evidence,
                flags=re.IGNORECASE,
            )

            if match:
                return cls._limit_evidence(
                    evidence,
                    match.start(),
                    match.end(),
                )

        return value

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
                    evidence=self._find_evidence(
                        text,
                        value,
                    ),
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
