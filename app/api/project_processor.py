import os
import shutil
from urllib.parse import quote

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile
)
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.project_processor import project_processor
from app.services.project_package import project_package
from app.services.project_manager import project_manager
from app.services.hidden_works_registry import hidden_works_registry
from app.services.supporting_documents_registry import supporting_documents_registry

from app.generators.document_registry_excel import document_registry_excel
from app.generators.project_executive_generator import (
    project_executive_generator
)
from app.generators.hidden_works_act_generator import (
    hidden_works_act_generator
)
from app.generators.hidden_works_journal_generator import (
    hidden_works_journal_generator
)


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


class ProjectCreate(BaseModel):
    project_name: str


class ProjectCardUpdate(BaseModel):
    object_name: str = ""
    address: str = ""
    customer: str = ""
    contractor: str = ""
    designer: str = ""
    contract_number: str = ""
    start_date: str = ""
    finish_date: str = ""
    chief_engineer: str = ""


class HiddenWorksActData(BaseModel):
    act_code: str = "grounding_device"

    act_number: str = ""
    act_date: str = ""

    customer_representative: str = ""
    contractor_representative: str = ""
    construction_control_representative: str = ""
    designer_representative: str = ""

    work_contractor: str = ""
    work_representative: str = ""

    work_name: str = ""
    work_location: str = ""

    project_documentation: str = ""

    materials: str = ""
    material_documents: str = ""

    actual_materials: str = ""
    executive_scheme: str = ""

    quality_documents: str = ""

    work_start_date: str = ""
    work_finish_date: str = ""

    compliance: str = ""
    materials_compliance: str = ""
    test_results: str = ""
    geometric_parameters: str = ""
    next_works: str = ""

    additional_information: str = ""
    attachments: str = ""
    remarks: str = ""


# =========================================================
# СПИСОК ПРОЕКТОВ
# =========================================================

@router.get("")
def list_projects():

    try:
        projects = project_manager.list_projects()

        return {
            "projects_count": len(projects),
            "projects": projects
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# =========================================================
# СОЗДАНИЕ ПРОЕКТА
# =========================================================

@router.post("")
def create_project(
    data: ProjectCreate
):

    try:
        project = project_manager.create_project(
            data.project_name
        )

        return {
            "status": "Проект готов",
            "project": project
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# =========================================================
# ЗАГРУЗКА + АВТОМАТИЧЕСКИЙ АНАЛИЗ
# =========================================================

@router.post("/{project_name}/upload")
def upload_project_file(
    project_name: str,
    file: UploadFile = File(...)
):

    file_path = None

    try:
        # Проверяем существование проекта
        project_manager.get_project(
            project_name
        )

        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Имя файла не указано"
            )

        filename = os.path.basename(
            file.filename.replace(
                "\\",
                "/"
            )
        )

        if not filename:
            raise HTTPException(
                status_code=400,
                detail="Некорректное имя файла"
            )

        extension = os.path.splitext(
            filename
        )[1].lower()

        allowed_extensions = {
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".jpg",
            ".jpeg",
            ".png",
            ".tif",
            ".tiff"
        }

        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Неподдерживаемый формат файла: "
                    f"{extension or 'без расширения'}"
                )
            )

        input_path = os.path.join(
            "projects",
            project_name,
            "input"
        )

        os.makedirs(
            input_path,
            exist_ok=True
        )

        file_path = os.path.join(
            input_path,
            filename
        )

        # ---------------------------------------------
        # 1. СОХРАНЯЕМ ФАЙЛ
        # ---------------------------------------------

        with open(
            file_path,
            "wb"
        ) as destination:

            shutil.copyfileobj(
                file.file,
                destination
            )

        file_size = os.path.getsize(
            file_path
        )

        # ---------------------------------------------
        # 2. АВТОМАТИЧЕСКИ ОБРАБАТЫВАЕМ ПРОЕКТ
        # ---------------------------------------------

        try:

            processing_result = (
                project_processor.process(
                    project_name
                )
            )

            processing_status = "Готово"
            processing_error = None

        except Exception as processing_exception:

            # Файл уже успешно сохранён.
            # Ошибка анализа не должна удалять файл.
            processing_result = None
            processing_status = "Ошибка анализа"
            processing_error = str(
                processing_exception
            )

        # ---------------------------------------------
        # 3. ВОЗВРАЩАЕМ РЕЗУЛЬТАТ
        # ---------------------------------------------

        return {
            "status": "Файл загружен",
            "project": project_name,
            "filename": filename,
            "extension": extension,
            "size_bytes": file_size,
            "saved_to": file_path,
            "automatic_processing": {
                "status": processing_status,
                "error": processing_error,
                "result": processing_result
            }
        }

    except HTTPException:
        raise

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:

        file.file.close()


# =========================================================
# РУЧНАЯ ОБРАБОТКА ПРОЕКТА
# =========================================================

@router.post("/{project_name}/process")
def process_project(
    project_name: str
):

    try:
        return project_processor.process(
            project_name
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# =========================================================
# КАРТОЧКА ПРОЕКТА
# =========================================================

@router.get("/{project_name}/card")
def get_project_card(
    project_name: str
):

    try:
        return project_manager.get_project(
            project_name
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.put("/{project_name}/card")
def update_project_card(
    project_name: str,
    card: ProjectCardUpdate
):

    try:
        return project_manager.update_project(
            project_name,
            card.model_dump()
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# =========================================================
# СОЗДАНИЕ АОСР
# =========================================================

@router.post("/{project_name}/hidden-works-act")
def create_hidden_works_act(
    project_name: str,
    act: HiddenWorksActData
):

    try:

        act_data = act.model_dump()

        act_code = act_data.pop(
            "act_code",
            "grounding_device",
        )

        if not act_data.get("actual_materials"):
            act_data["actual_materials"] = (
                act_data.get("materials")
                or ""
            )

        save_result = (
            hidden_works_act_generator.save_act_data(
                project_name,
                act_code,
                act_data,
            )
        )

        file_path = hidden_works_act_generator.create(
            project_name,
            act_code=act_code,
            act_data=act_data,
        )

        registry = hidden_works_registry.analyze_project(
            project_name
        )

        excel_path = document_registry_excel.create(
            project_name
        )

        package_path = project_package.create_zip(
            project_name
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    if not os.path.exists(
        file_path
    ):
        raise HTTPException(
            status_code=404,
            detail="АОСР не создан"
        )

    filename = os.path.basename(
        file_path
    )

    headers = {
        "X-Act-Number": quote(
            str(act.act_number)
        ),
        "X-Acts-Count": str(
            registry.get(
                "acts_count",
                0
            )
        ),
        "X-Act-Filename": quote(
            filename
        ),
        "X-Excel-Updated": (
            "true"
            if os.path.exists(excel_path)
            else "false"
        ),
        "X-Package-Updated": (
            "true"
            if os.path.exists(package_path)
            else "false"
        )
    }

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        headers=headers
    )


# =========================================================
# РЕЕСТР АОСР
# =========================================================

@router.get("/{project_name}/hidden-works-registry")
def get_hidden_works_registry(
    project_name: str
):

    try:
        return hidden_works_registry.analyze_project(
            project_name
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# =========================================================
# ЖУРНАЛ АОСР
# =========================================================

@router.get("/{project_name}/supporting-documents-registry")
def get_supporting_documents_registry(
    project_name: str
):

    try:
        return supporting_documents_registry.analyze_project(
            project_name
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.get("/{project_name}/hidden-works-journal")
def download_hidden_works_journal(
    project_name: str
):

    try:
        file_path = (
            hidden_works_journal_generator.create(
                project_name
            )
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    if not os.path.exists(
        file_path
    ):
        raise HTTPException(
            status_code=404,
            detail="Журнал АОСР не создан"
        )

    return FileResponse(
        path=file_path,
        filename="05_Журнал_АОСР.docx",
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )
    )


# =========================================================
# EXCEL-РЕЕСТР
# =========================================================

@router.get("/{project_name}/registry")
def download_registry(
    project_name: str
):

    file_path = os.path.join(
        "projects",
        project_name,
        "output",
        f"Реестр_документов_{project_name}.xlsx"
    )

    if not os.path.exists(
        file_path
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "Excel-реестр не найден. "
                "Сначала выполните обработку проекта."
            )
        )

    return FileResponse(
        path=file_path,
        filename=(
            f"Реестр_документов_"
            f"{project_name}.xlsx"
        ),
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )


# =========================================================
# ИСПОЛНИТЕЛЬНАЯ ДОКУМЕНТАЦИЯ
# =========================================================

@router.get("/{project_name}/executive-doc")
def download_executive_document(
    project_name: str
):

    try:
        file_path = (
            project_executive_generator.create(
                project_name
            )
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    if not os.path.exists(
        file_path
    ):
        raise HTTPException(
            status_code=404,
            detail="Исполнительная документация не создана"
        )

    return FileResponse(
        path=file_path,
        filename=(
            f"Исполнительная_документация_"
            f"{project_name}.docx"
        ),
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )
    )


# =========================================================
# ZIP-КОМПЛЕКТ
# =========================================================

@router.get("/{project_name}/package")
def download_project_package(
    project_name: str
):

    try:
        file_path = project_package.create_zip(
            project_name
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    if not os.path.exists(
        file_path
    ):
        raise HTTPException(
            status_code=404,
            detail="ZIP-комплект проекта не создан"
        )

    return FileResponse(
        path=file_path,
        filename=f"Комплект_{project_name}.zip",
        media_type="application/zip"
    )
