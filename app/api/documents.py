from fastapi import APIRouter, UploadFile, File
import shutil
import os

from app.services.document_service import document_service
from app.parsers.pdf_parser import pdf_parser
from app.services.document_analyzer import document_analyzer
from app.services.project_service import project_service


router = APIRouter()

UPLOAD_DIR = "uploads"


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_path = os.path.join(
        UPLOAD_DIR,
        file.filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = document_service.analyze(file_path)

    if result["extension"].lower() == ".pdf":

        text = pdf_parser.extract_text(file_path)

        analysis = document_analyzer.analyze_text(text)

        project_service.save_analysis(analysis)

        result.update(analysis)

    return result