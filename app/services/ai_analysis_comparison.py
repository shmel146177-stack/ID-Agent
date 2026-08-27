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

            if (
                deterministic_value is None
                or (
                    isinstance(deterministic_value, str)
                    and not deterministic_value.strip()
                )
            ):
                suggestions.append(
                    {
                        "field": fact.field,
                        "value": fact.value,
                        "confidence": fact.confidence,
                    }
                )
                continue

            comparison_deterministic_value = (
                deterministic_value.strip()
                if isinstance(deterministic_value, str)
                else deterministic_value
            )

            comparison_ai_value = (
                fact.value.strip()
                if isinstance(fact.value, str)
                else fact.value
            )

            if comparison_deterministic_value == comparison_ai_value:
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
