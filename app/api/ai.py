from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ai_client import AIClient
from app.services.ai_document_analysis import AIDocumentAnalysisService


router = APIRouter(prefix="/ai", tags=["AI"])


class AIAnalysisRequest(BaseModel):
    filename: str
    text: str


@router.get("/status")
def ai_status():
    return AIClient().status()


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

    return result.model_dump()
