from fastapi import APIRouter
from pydantic import BaseModel

from app.models.ai_review import AIReviewDecision
from app.services.ai_client import AIClient
from app.services.ai_document_analysis import AIDocumentAnalysisService
from app.services.project_service import project_service


router = APIRouter(prefix="/ai", tags=["AI"])


class AIAnalysisRequest(BaseModel):
    filename: str
    text: str


@router.get("/status")
def ai_status():
    return AIClient().status()


@router.get("/latest")
def latest_ai_analysis():
    result = project_service.get_ai_analysis()

    if result is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="AI analysis not found",
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

    if (
        latest_ai is not None
        and comparison.get("source_filename")
        != latest_ai.get("source_filename")
    ):
        raise HTTPException(
            status_code=409,
            detail="AI comparison source filename mismatch",
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

    if (
        review.get("source_filename")
        != latest_ai.get("source_filename")
    ):
        raise HTTPException(
            status_code=409,
            detail="AI review source filename mismatch",
        )

    return review


@router.post("/review")
def review_ai_analysis(review: AIReviewDecision):
    from fastapi import HTTPException

    latest_ai = project_service.get_ai_analysis()

    if latest_ai is None:
        raise HTTPException(
            status_code=404,
            detail="AI analysis not found",
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

    review_data = review.model_dump()

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

    result = service.analyze_text(
        request.filename,
        request.text,
    )

    result_data = result.model_dump()

    saved_ai_analysis = project_service.save_ai_analysis(
        result_data,
        source_filename=request.filename,
    )

    return saved_ai_analysis["document"]
