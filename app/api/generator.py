from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.services.project_service import project_service
from app.generators.executive_doc_generator_v3 import executive_generator_v3

router = APIRouter()


@router.post("/generate")
def generate_document():

    analysis = project_service.get_analysis()

    if analysis is None:
        return {
            "status": "Нет данных для генерации"
        }

    file_path = executive_generator_v3.create(analysis)

    return FileResponse(
        path=file_path,
        filename="Исполнительная_документация.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )