from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.models.ai_analysis import AutonomousFactExclusion
from app.models.ai_review import (
    AIReviewDecision,
    ExcludedAutonomousFactReview,
)
from app.services.ai_client import AIClient
from app.services.ai_document_analysis import AIDocumentAnalysisService
from app.services.knowledge_context import (
    MAX_KNOWLEDGE_CONTEXT_CHARS,
    extract_knowledge_source_ids,
    extract_knowledge_source_pages,
)
from app.services.knowledge_repository import KnowledgeRepository
from app.services.knowledge_service import KnowledgeService
from app.services.project_service import project_service


router = APIRouter(prefix="/ai", tags=["AI"])




class AIAnalysisRequest(BaseModel):
    filename: str
    text: str
    knowledge_context: str | None = Field(
        default=None,
        max_length=MAX_KNOWLEDGE_CONTEXT_CHARS,
    )

    knowledge_project_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    knowledge_query: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
    )
    include_unreviewed_ocr: bool = False

    @model_validator(mode="after")
    def validate_knowledge_context_binding(self):
        context = (self.knowledge_context or "").strip()
        project_name = (
            self.knowledge_project_name or ""
        ).strip()
        query = (self.knowledge_query or "").strip()

        if context and not extract_knowledge_source_ids(context):
            raise ValueError(
                "knowledge_context must contain source binding"
            )

        if (
            self.knowledge_project_name is not None
            and not project_name
        ):
            raise ValueError(
                "knowledge_project_name must not be blank"
            )

        if self.knowledge_query is not None and not query:
            raise ValueError(
                "knowledge_query must not be blank"
            )

        if bool(project_name) != bool(query):
            raise ValueError(
                "knowledge_project_name and knowledge_query "
                "must be provided together"
            )

        if self.include_unreviewed_ocr and not project_name:
            raise ValueError(
                "include_unreviewed_ocr requires "
                "project knowledge search"
            )

        if context and project_name:
            raise ValueError(
                "knowledge_context cannot be combined with "
                "project knowledge search"
            )

        if project_name:
            self.knowledge_project_name = project_name
            self.knowledge_query = query

        return self


@router.get("/status")
def ai_status():
    return AIClient().status()


@router.get("/latest")
def latest_ai_analysis():
    from fastapi import HTTPException

    result = project_service.get_ai_analysis()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="AI analysis not found",
        )

    if not result.get("analysis_id"):
        raise HTTPException(
            status_code=409,
            detail="AI analysis missing analysis id",
        )

    if not result.get("source_filename"):
        raise HTTPException(
            status_code=409,
            detail="AI analysis missing source filename",
        )

    return result


@router.get("/comparison")
def get_ai_comparison():
    from fastapi import HTTPException

    comparison = project_service.get_ai_comparison()

    if comparison is None:
        raise HTTPException(
            status_code=404,
            detail="AI comparison not found",
        )

    latest_ai = project_service.get_ai_analysis()

    if latest_ai is None:
        raise HTTPException(
            status_code=409,
            detail="AI comparison has no current AI analysis",
        )

    if not comparison.get("analysis_id"):
        raise HTTPException(
            status_code=409,
            detail="AI comparison missing analysis id",
        )

    if not latest_ai.get("analysis_id"):
        raise HTTPException(
            status_code=409,
            detail="AI analysis missing analysis id",
        )

    if (
        latest_ai is not None
        and comparison.get("analysis_id")
        != latest_ai.get("analysis_id")
    ):
        raise HTTPException(
            status_code=409,
            detail="AI comparison analysis id mismatch",
        )

    if not comparison.get("source_filename"):
        raise HTTPException(
            status_code=409,
            detail="AI comparison missing source filename",
        )

    if not latest_ai.get("source_filename"):
        raise HTTPException(
            status_code=409,
            detail="AI analysis missing source filename",
        )

    if (
        latest_ai is not None
        and comparison.get("source_filename")
        != latest_ai.get("source_filename")
    ):
        raise HTTPException(
            status_code=409,
            detail="AI comparison source filename mismatch",
        )

    if comparison.get(
        "knowledge_source_ids",
        [],
    ) != latest_ai.get(
        "knowledge_source_ids",
        [],
    ):
        raise HTTPException(
            status_code=409,
            detail="AI comparison knowledge sources mismatch",
        )

    return comparison

@router.get("/review")
def get_ai_review():
    from fastapi import HTTPException

    review = project_service.get_ai_review()

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="AI review not found",
        )

    latest_ai = project_service.get_ai_analysis()

    if latest_ai is None:
        raise HTTPException(
            status_code=409,
            detail="AI review has no current AI analysis",
        )

    if not review.get("analysis_id"):
        raise HTTPException(
            status_code=409,
            detail="AI review missing analysis id",
        )

    if not latest_ai.get("analysis_id"):
        raise HTTPException(
            status_code=409,
            detail="AI analysis missing analysis id",
        )

    if (
        review.get("analysis_id")
        != latest_ai.get("analysis_id")
    ):
        raise HTTPException(
            status_code=409,
            detail="AI review analysis id mismatch",
        )

    if not review.get("source_filename"):
        raise HTTPException(
            status_code=409,
            detail="AI review missing source filename",
        )

    if not latest_ai.get("source_filename"):
        raise HTTPException(
            status_code=409,
            detail="AI analysis missing source filename",
        )

    if (
        review.get("source_filename")
        != latest_ai.get("source_filename")
    ):
        raise HTTPException(
            status_code=409,
            detail="AI review source filename mismatch",
        )

    if review.get(
        "knowledge_source_ids",
        [],
    ) != latest_ai.get(
        "knowledge_source_ids",
        [],
    ):
        raise HTTPException(
            status_code=409,
            detail="AI review knowledge sources mismatch",
        )

    return review


@router.get("/review/exclusions")
def get_excluded_fact_review_statuses():
    latest_ai = project_service.get_ai_analysis()

    if latest_ai is None:
        raise HTTPException(
            status_code=404,
            detail="AI analysis not found",
        )

    analysis_id = latest_ai.get("analysis_id")
    source_filename = latest_ai.get("source_filename")

    if not analysis_id:
        raise HTTPException(
            status_code=409,
            detail="AI analysis missing analysis id",
        )

    if not source_filename:
        raise HTTPException(
            status_code=409,
            detail="AI analysis missing source filename",
        )

    review = project_service.get_ai_review()
    fact_reviews = {}

    if review is not None:
        if review.get("analysis_id") != analysis_id:
            raise HTTPException(
                status_code=409,
                detail="AI review analysis id mismatch",
            )

        if review.get("source_filename") != source_filename:
            raise HTTPException(
                status_code=409,
                detail="AI review source filename mismatch",
            )

        if review.get(
            "knowledge_source_ids",
            [],
        ) != latest_ai.get(
            "knowledge_source_ids",
            [],
        ):
            raise HTTPException(
                status_code=409,
                detail="AI review knowledge sources mismatch",
            )

        try:
            parsed_reviews = [
                ExcludedAutonomousFactReview.model_validate(item)
                for item in review.get("excluded_fact_reviews", [])
            ]
        except (TypeError, ValueError) as error:
            raise HTTPException(
                status_code=409,
                detail="AI review has invalid excluded fact decisions",
            ) from error

        fact_reviews = {
            item.field: item
            for item in parsed_reviews
        }

    try:
        excluded_facts = [
            AutonomousFactExclusion.model_validate(item)
            for item in latest_ai.get(
                "excluded_autonomous_facts",
                [],
            )
        ]
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=409,
            detail="AI analysis has invalid structured exclusions",
        ) from error

    statuses = []
    review_counts = {
        "pending": 0,
        "accepted": 0,
        "rejected": 0,
        "corrected": 0,
    }

    for fact in excluded_facts:
        fact_review = fact_reviews.get(fact.field)
        review_status = (
            fact_review.decision
            if fact_review is not None
            else "pending"
        )
        status = fact.model_dump()
        status["review_status"] = review_status
        status["corrected_value"] = (
            fact_review.corrected_value
            if fact_review is not None
            else None
        )
        status["review_notes"] = (
            fact_review.notes
            if fact_review is not None
            else None
        )
        statuses.append(status)
        review_counts[review_status] += 1

    total = len(statuses)
    pending = review_counts["pending"]

    return {
        "source_filename": source_filename,
        "analysis_id": analysis_id,
        "excluded_fact_review_statuses": statuses,
        "excluded_fact_review_summary": {
            "total": total,
            "reviewed": total - pending,
            **review_counts,
            "can_accept": pending == 0,
        },
        "engineering_confirmation": False,
    }


@router.post("/review")
def review_ai_analysis(review: AIReviewDecision):
    from fastapi import HTTPException

    latest_ai = project_service.get_ai_analysis()

    if latest_ai is None:
        raise HTTPException(
            status_code=404,
            detail="AI analysis not found",
        )

    if not latest_ai.get("analysis_id"):
        raise HTTPException(
            status_code=409,
            detail="AI analysis missing analysis id",
        )

    if not latest_ai.get("source_filename"):
        raise HTTPException(
            status_code=409,
            detail="AI analysis missing source filename",
        )

    if (
        latest_ai.get("source_filename")
        != review.source_filename
    ):
        raise HTTPException(
            status_code=409,
            detail="AI analysis source filename mismatch",
        )

    if (
        latest_ai.get("analysis_id")
        != review.analysis_id
    ):
        raise HTTPException(
            status_code=409,
            detail="AI analysis id mismatch",
        )

    excluded_facts = latest_ai.get(
        "excluded_autonomous_facts",
        [],
    )
    excluded_fact_fields = {
        fact.get("field")
        for fact in excluded_facts
        if isinstance(fact, dict) and fact.get("field")
    }

    for fact_review in review.excluded_fact_reviews:
        if fact_review.field not in excluded_fact_fields:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Reviewed field is not a current structured "
                    "autonomous exclusion"
                ),
            )

    reviewed_fact_fields = {
        fact_review.field
        for fact_review in review.excluded_fact_reviews
    }

    if (
        review.decision == "accepted"
        and reviewed_fact_fields != excluded_fact_fields
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "All structured autonomous exclusions must be "
                "reviewed before accepting AI analysis"
            ),
        )

    review_data = review.model_dump()

    if "excluded_fact_reviews" not in review.model_fields_set:
        review_data.pop("excluded_fact_reviews", None)

    knowledge_source_ids = latest_ai.get(
        "knowledge_source_ids"
    )

    if knowledge_source_ids is not None:
        review_data["knowledge_source_ids"] = list(
            knowledge_source_ids
        )

    project_service.save_ai_review(
        review_data,
    )

    return review_data


@router.post("/analyze")
def analyze_document(request: AIAnalysisRequest):
    ai_client = AIClient()

    if ai_client.settings.active:
        service = AIDocumentAnalysisService.with_openai(
            ai_client=ai_client,
        )
    else:
        service = AIDocumentAnalysisService(
            ai_client=ai_client,
        )

    knowledge_context = request.knowledge_context
    excluded_unreviewed_ocr_pages = None

    if (
        knowledge_context is None
        and request.knowledge_project_name is not None
    ):
        try:
            repository = KnowledgeRepository.for_project(
                request.knowledge_project_name
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail=str(error),
            ) from error
        knowledge_service = KnowledgeService.from_repository(
            repository
        )

        if request.include_unreviewed_ocr:
            excluded_unreviewed_ocr_pages = []
        else:
            unreviewed_ocr_results = (
                knowledge_service.search_unreviewed_ocr_results(
                    request.knowledge_query or ""
                )
            )
            excluded_unreviewed_ocr_pages = [
                {
                    "source_id": result.chunk.source_id,
                    "page": result.chunk.page,
                }
                for result in unreviewed_ocr_results
            ]

        knowledge_context = knowledge_service.build_context(
            request.knowledge_query or "",
            max_results=5,
            max_chars=MAX_KNOWLEDGE_CONTEXT_CHARS,
            include_unreviewed_ocr=(
                request.include_unreviewed_ocr
            ),
        ) or None

    if knowledge_context:
        result = service.analyze_text(
            request.filename,
            request.text,
            knowledge_context=knowledge_context,
        )
    else:
        result = service.analyze_text(
            request.filename,
            request.text,
        )

    result_data = result.model_dump()
    included_knowledge_pages = None

    if knowledge_context:
        included_knowledge_pages = (
            extract_knowledge_source_pages(
                knowledge_context
            )
        )
    elif request.knowledge_project_name is not None:
        included_knowledge_pages = []

    if included_knowledge_pages is not None:
        result_data["included_knowledge_pages"] = (
            included_knowledge_pages
        )

    if excluded_unreviewed_ocr_pages is not None:
        result_data["excluded_unreviewed_ocr_pages"] = (
            excluded_unreviewed_ocr_pages
        )

    save_options = {}

    if knowledge_context:
        save_options["knowledge_source_ids"] = (
            extract_knowledge_source_ids(
                knowledge_context
            )
        )

    saved_ai_analysis = project_service.save_ai_analysis(
        result_data,
        source_filename=request.filename,
        **save_options,
    )

    return saved_ai_analysis["document"]
