from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import shutil
import os

from app.services.document_service import document_service
from app.parsers.pdf_parser import pdf_parser
from app.services.document_analyzer import document_analyzer
from app.services.project_service import project_service
from app.services.ai_client import AIClient
from app.services.ai_document_analysis import AIDocumentAnalysisService
from app.services.ai_analysis_comparison import (
    AIAnalysisComparisonService,
)
from app.services.knowledge_context import (
    MAX_KNOWLEDGE_CONTEXT_CHARS,
    extract_knowledge_source_ids,
)


router = APIRouter()

UPLOAD_DIR = "uploads"


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    use_ai: bool = False,
    knowledge_context: Annotated[str | None, Form()] = None,
):
    knowledge_context = (knowledge_context or "").strip() or None

    if knowledge_context is not None:
        if len(knowledge_context) > MAX_KNOWLEDGE_CONTEXT_CHARS:
            raise HTTPException(
                status_code=422,
                detail="Knowledge context exceeds size limit",
            )

        if not extract_knowledge_source_ids(knowledge_context):
            raise HTTPException(
                status_code=422,
                detail="Knowledge context missing source binding",
            )

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = os.path.basename(
        (file.filename or "").replace(
            "\\",
            "/"
        )
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = document_service.analyze(file_path)

    if result["extension"].lower() == ".pdf":

        text = pdf_parser.extract_text(file_path)

        analysis = document_analyzer.analyze_text(text)

        project_service.save_analysis(analysis)

        result.update(analysis)

        if use_ai:
            ai_client = AIClient()

            if ai_client.settings.active:
                ai_service = AIDocumentAnalysisService.with_openai(
                    ai_client=ai_client,
                )
            else:
                ai_service = AIDocumentAnalysisService(
                    ai_client=ai_client,
                )

            if knowledge_context:
                ai_analysis = ai_service.analyze_text(
                    filename,
                    text,
                    knowledge_context=knowledge_context,
                )
            else:
                ai_analysis = ai_service.analyze_text(
                    filename,
                    text,
                )

            ai_analysis_data = ai_analysis.model_dump()
            save_options = {}

            if knowledge_context:
                save_options["knowledge_source_ids"] = (
                    extract_knowledge_source_ids(
                        knowledge_context
                    )
                )

            saved_ai_analysis = project_service.save_ai_analysis(
                ai_analysis_data,
                source_filename=filename,
                **save_options,
            )

            saved_ai_document = saved_ai_analysis["document"]

            result["ai_analysis"] = saved_ai_document

            ai_comparison = (
                AIAnalysisComparisonService().compare(
                    analysis,
                    ai_analysis,
                )
            )

            comparison_options = {}

            if knowledge_context:
                comparison_options["knowledge_source_ids"] = (
                    saved_ai_document.get(
                        "knowledge_source_ids",
                        [],
                    )
                )

            project_service.save_ai_comparison(
                ai_comparison,
                analysis_id=saved_ai_document["analysis_id"],
                source_filename=filename,
                **comparison_options,
            )

            result["ai_comparison"] = ai_comparison

    return result
