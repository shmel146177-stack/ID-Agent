from datetime import datetime, timezone
from functools import wraps
from threading import Lock

from app.models.ai_analysis import AutonomousFactExclusion
from app.models.ai_review import (
    AIReviewDecision,
    ExcludedAutonomousFactReview,
    ExcludedAutonomousFactReviewBinding,
    ExcludedAutonomousFactReviewHistory,
    ExcludedAutonomousFactReviewUpdate,
)
from app.services.interprocess_lock import exclusive_file_lock


class AIExclusionReviewError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _serialized_mutation(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._mutation_lock:
            with exclusive_file_lock(
                self.project_service.ai_review_lock_path
            ):
                return method(self, *args, **kwargs)

    return wrapper


class AIExclusionReviewService:
    """Manage source-bound human review of autonomous exclusions."""

    def __init__(self, project_service):
        self.project_service = project_service
        self._mutation_lock = Lock()

    @staticmethod
    def _error(status_code: int, detail: str):
        raise AIExclusionReviewError(status_code, detail)

    def _current_analysis(self) -> dict:
        analysis = self.project_service.get_ai_analysis()

        if analysis is None:
            self._error(404, "AI analysis not found")

        return analysis

    def _current_identity(self, analysis: dict) -> tuple[str, str]:
        analysis_id = analysis.get("analysis_id")
        source_filename = analysis.get("source_filename")

        if not analysis_id:
            self._error(409, "AI analysis missing analysis id")

        if not source_filename:
            self._error(409, "AI analysis missing source filename")

        return analysis_id, source_filename

    def _validate_request_binding(
        self,
        analysis: dict,
        analysis_id: str,
        source_filename: str,
    ) -> None:
        if analysis.get("analysis_id") != analysis_id:
            self._error(409, "AI analysis id mismatch")

        if analysis.get("source_filename") != source_filename:
            self._error(409, "AI analysis source filename mismatch")

    def _validate_saved_binding(
        self,
        review: dict,
        analysis: dict,
    ) -> None:
        if review.get("analysis_id") != analysis.get("analysis_id"):
            self._error(409, "AI review analysis id mismatch")

        if review.get("source_filename") != analysis.get(
            "source_filename"
        ):
            self._error(409, "AI review source filename mismatch")

    def _parse_excluded_facts(
        self,
        analysis: dict,
    ) -> list[AutonomousFactExclusion]:
        try:
            return [
                AutonomousFactExclusion.model_validate(item)
                for item in analysis.get(
                    "excluded_autonomous_facts",
                    [],
                )
            ]
        except (TypeError, ValueError) as error:
            raise AIExclusionReviewError(
                409,
                "AI analysis has invalid structured exclusions",
            ) from error

    def _require_current_field(
        self,
        field: str,
        excluded_fact_fields: list[str],
    ) -> None:
        if field not in excluded_fact_fields:
            self._error(
                409,
                "Reviewed field is not a current structured "
                "autonomous exclusion",
            )

    def _parse_review_data(self, review: dict) -> dict:
        try:
            return AIReviewDecision.model_validate(
                {
                    key: value
                    for key, value in review.items()
                    if key != "knowledge_source_ids"
                }
            ).model_dump(mode="json")
        except (TypeError, ValueError) as error:
            raise AIExclusionReviewError(
                409,
                "AI review has invalid data",
            ) from error

    def _require_revision(
        self,
        review_data: dict,
        expected_revision: int,
    ) -> int:
        current_revision = review_data["review_revision"]

        if expected_revision != current_revision:
            self._error(
                409,
                "AI review revision mismatch: expected "
                f"{expected_revision}, current {current_revision}",
            )

        return current_revision

    @staticmethod
    def _copy_knowledge_sources(data: dict, analysis: dict) -> None:
        knowledge_source_ids = analysis.get("knowledge_source_ids")

        if knowledge_source_ids is not None:
            data["knowledge_source_ids"] = list(knowledge_source_ids)

    def get_review(self) -> dict:
        review = self.project_service.get_ai_review()

        if review is None:
            self._error(404, "AI review not found")

        analysis = self.project_service.get_ai_analysis()

        if analysis is None:
            self._error(409, "AI review has no current AI analysis")

        if not review.get("analysis_id"):
            self._error(409, "AI review missing analysis id")

        if not analysis.get("analysis_id"):
            self._error(409, "AI analysis missing analysis id")

        if review.get("analysis_id") != analysis.get("analysis_id"):
            self._error(409, "AI review analysis id mismatch")

        if not review.get("source_filename"):
            self._error(409, "AI review missing source filename")

        if not analysis.get("source_filename"):
            self._error(409, "AI analysis missing source filename")

        if review.get("source_filename") != analysis.get(
            "source_filename"
        ):
            self._error(409, "AI review source filename mismatch")

        if review.get("knowledge_source_ids", []) != analysis.get(
            "knowledge_source_ids",
            [],
        ):
            self._error(409, "AI review knowledge sources mismatch")

        review_data = dict(review)
        review_data["review_revision"] = self._parse_review_data(
            review
        )["review_revision"]
        return review_data

    def get_review_history(self, analysis_id: str) -> dict:
        review = self.project_service.get_ai_review_history(analysis_id)

        if review is None:
            self._error(404, "AI review history not found")

        return review

    def list_review_history(
        self,
        limit: int = 50,
        offset: int = 0,
        source_filename: str | None = None,
    ) -> dict:
        archives = self.project_service.list_ai_review_history()

        if source_filename is not None:
            archives = [
                archive
                for archive in archives
                if archive.get("source_filename") == source_filename
            ]

        total_count = len(archives)
        page = archives[offset : offset + limit]

        return {
            "count": len(page),
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "archives": page,
        }

    def get_statuses(self) -> dict:
        analysis = self._current_analysis()
        analysis_id, source_filename = self._current_identity(analysis)
        review = self.project_service.get_ai_review()
        fact_reviews = {}

        if review is not None:
            self._validate_saved_binding(review, analysis)

            if review.get("knowledge_source_ids", []) != analysis.get(
                "knowledge_source_ids",
                [],
            ):
                self._error(409, "AI review knowledge sources mismatch")

            try:
                parsed_reviews = [
                    ExcludedAutonomousFactReview.model_validate(item)
                    for item in review.get("excluded_fact_reviews", [])
                ]
            except (TypeError, ValueError) as error:
                raise AIExclusionReviewError(
                    409,
                    "AI review has invalid excluded fact decisions",
                ) from error

            fact_reviews = {item.field: item for item in parsed_reviews}

        review_revision = (
            self._parse_review_data(review)["review_revision"]
            if review is not None
            else 0
        )

        statuses = []
        review_counts = {
            "pending": 0,
            "accepted": 0,
            "rejected": 0,
            "corrected": 0,
        }

        for fact in self._parse_excluded_facts(analysis):
            fact_review = fact_reviews.get(fact.field)
            review_status = (
                fact_review.decision
                if fact_review is not None
                else "pending"
            )
            status = fact.model_dump()
            status.update(
                {
                    "review_status": review_status,
                    "corrected_value": (
                        fact_review.corrected_value
                        if fact_review is not None
                        else None
                    ),
                    "review_notes": (
                        fact_review.notes
                        if fact_review is not None
                        else None
                    ),
                    "reviewed_by": (
                        fact_review.reviewed_by
                        if fact_review is not None
                        else None
                    ),
                    "reviewed_at": (
                        fact_review.reviewed_at
                        if fact_review is not None
                        else None
                    ),
                }
            )
            statuses.append(status)
            review_counts[review_status] += 1

        total = len(statuses)
        pending = review_counts["pending"]

        return {
            "source_filename": source_filename,
            "analysis_id": analysis_id,
            "review_revision": review_revision,
            "excluded_fact_review_statuses": statuses,
            "excluded_fact_review_summary": {
                "total": total,
                "reviewed": total - pending,
                **review_counts,
                "can_accept": pending == 0,
            },
            "engineering_confirmation": False,
        }

    @_serialized_mutation
    def update_fact_review(
        self,
        field: str,
        request: ExcludedAutonomousFactReviewUpdate,
    ) -> dict:
        analysis = self._current_analysis()
        self._validate_request_binding(
            analysis,
            request.analysis_id,
            request.source_filename,
        )
        excluded_fact_fields = [
            fact.field for fact in self._parse_excluded_facts(analysis)
        ]
        self._require_current_field(field, excluded_fact_fields)
        reviewed_at = datetime.now(timezone.utc)
        new_fact_review = ExcludedAutonomousFactReview(
            field=field,
            decision=request.decision,
            corrected_value=request.corrected_value,
            notes=request.notes,
            reviewed_by=request.reviewed_by,
            reviewed_at=reviewed_at,
        )
        saved_review = self.project_service.get_ai_review()

        if saved_review is None:
            review_data = AIReviewDecision(
                source_filename=request.source_filename,
                analysis_id=request.analysis_id,
                decision="needs_changes",
            ).model_dump(mode="json")
        else:
            self._validate_saved_binding(saved_review, analysis)
            review_data = self._parse_review_data(saved_review)

        current_revision = self._require_revision(
            review_data,
            request.expected_revision,
        )

        reviews_by_field = {
            item["field"]: item
            for item in review_data["excluded_fact_reviews"]
        }
        previous_review_data = reviews_by_field.get(field)
        history_event = ExcludedAutonomousFactReviewHistory(
            analysis_id=request.analysis_id,
            field=field,
            action=(
                "updated"
                if previous_review_data is not None
                else "created"
            ),
            previous_review=(
                ExcludedAutonomousFactReview.model_validate(
                    previous_review_data
                )
                if previous_review_data is not None
                else None
            ),
            current_review=new_fact_review,
            reviewed_by=request.reviewed_by,
            reviewed_at=reviewed_at,
        )
        reviews_by_field[field] = new_fact_review.model_dump(mode="json")
        review_data["excluded_fact_reviews"] = [
            reviews_by_field[current_field]
            for current_field in excluded_fact_fields
            if current_field in reviews_by_field
        ]
        review_data.setdefault(
            "excluded_fact_review_history",
            [],
        ).append(history_event.model_dump(mode="json"))
        review_data["review_revision"] = current_revision + 1
        self._copy_knowledge_sources(review_data, analysis)
        self.project_service.save_ai_review(review_data)
        return review_data

    @_serialized_mutation
    def clear_fact_review(
        self,
        field: str,
        request: ExcludedAutonomousFactReviewBinding,
    ) -> dict:
        analysis = self._current_analysis()
        self._validate_request_binding(
            analysis,
            request.analysis_id,
            request.source_filename,
        )
        excluded_fact_fields = [
            fact.field for fact in self._parse_excluded_facts(analysis)
        ]
        self._require_current_field(field, excluded_fact_fields)
        saved_review = self.project_service.get_ai_review()

        if saved_review is None:
            self._error(404, "Excluded fact review not found")

        self._validate_saved_binding(saved_review, analysis)
        review_data = self._parse_review_data(saved_review)
        current_revision = self._require_revision(
            review_data,
            request.expected_revision,
        )
        saved_fields = {
            item["field"]
            for item in review_data["excluded_fact_reviews"]
        }

        if field not in saved_fields:
            self._error(404, "Excluded fact review not found")

        previous_review_data = next(
            item
            for item in review_data["excluded_fact_reviews"]
            if item["field"] == field
        )

        reviewed_at = datetime.now(timezone.utc)
        history_event = ExcludedAutonomousFactReviewHistory(
            analysis_id=request.analysis_id,
            field=field,
            action="cleared",
            previous_review=(
                ExcludedAutonomousFactReview.model_validate(
                    previous_review_data
                )
            ),
            current_review=None,
            reviewed_by=request.reviewed_by,
            reviewed_at=reviewed_at,
        )

        review_data["excluded_fact_reviews"] = [
            item
            for item in review_data["excluded_fact_reviews"]
            if item["field"] != field
        ]
        review_data.setdefault(
            "excluded_fact_review_history",
            [],
        ).append(history_event.model_dump(mode="json"))
        review_data["review_revision"] = current_revision + 1

        if review_data["decision"] == "accepted":
            review_data["decision"] = "needs_changes"

        self._copy_knowledge_sources(review_data, analysis)
        self.project_service.save_ai_review(review_data)
        return review_data

    @_serialized_mutation
    def save_review(self, review: AIReviewDecision) -> dict:
        analysis = self._current_analysis()
        self._current_identity(analysis)
        self._validate_request_binding(
            analysis,
            review.analysis_id,
            review.source_filename,
        )
        excluded_fact_fields = {
            fact.field for fact in self._parse_excluded_facts(analysis)
        }

        for fact_review in review.excluded_fact_reviews:
            self._require_current_field(
                fact_review.field,
                list(excluded_fact_fields),
            )

        reviewed_fact_fields = {
            fact_review.field
            for fact_review in review.excluded_fact_reviews
        }

        if (
            review.decision == "accepted"
            and reviewed_fact_fields != excluded_fact_fields
        ):
            self._error(
                409,
                "All structured autonomous exclusions must be "
                "reviewed before accepting AI analysis",
            )

        review_data = review.model_dump(mode="json")

        existing_review = self.project_service.get_ai_review()

        if existing_review is not None:
            self._validate_saved_binding(existing_review, analysis)
            existing_data = self._parse_review_data(existing_review)
            current_revision = self._require_revision(
                existing_data,
                review.review_revision,
            )
            history = existing_data.get(
                "excluded_fact_review_history",
                [],
            )

            if history:
                review_data["excluded_fact_review_history"] = history
        else:
            current_revision = self._require_revision(review_data, 0)
            review_data.pop("excluded_fact_review_history", None)

        if "excluded_fact_reviews" not in review.model_fields_set:
            review_data.pop("excluded_fact_reviews", None)

        review_data["review_revision"] = current_revision + 1
        self._copy_knowledge_sources(review_data, analysis)
        self.project_service.save_ai_review(review_data)
        return review_data
