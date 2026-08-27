from app.models.ai_analysis import AIAnalysisResult


class AIAnalysisComparisonService:
    def compare(
        self,
        deterministic: dict,
        ai_analysis: AIAnalysisResult,
    ) -> dict:
        matches = []
        conflicts = []
        suggestions = []

        for fact in ai_analysis.facts:
            if fact.field not in deterministic:
                suggestions.append(
                    {
                        "field": fact.field,
                        "value": fact.value,
                        "confidence": fact.confidence,
                    }
                )
                continue

            deterministic_value = deterministic[fact.field]

            if deterministic_value is None:
                suggestions.append(
                    {
                        "field": fact.field,
                        "value": fact.value,
                        "confidence": fact.confidence,
                    }
                )
                continue

            if deterministic_value == fact.value:
                matches.append(
                    {
                        "field": fact.field,
                        "value": fact.value,
                        "confidence": fact.confidence,
                    }
                )
                continue

            conflicts.append(
                {
                    "field": fact.field,
                    "deterministic_value": deterministic_value,
                    "ai_value": fact.value,
                    "confidence": fact.confidence,
                }
            )

        return {
            "matches": matches,
            "conflicts": conflicts,
            "suggestions": suggestions,
            "requires_human_review": True,
        }
