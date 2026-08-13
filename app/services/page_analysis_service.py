import json
from pathlib import Path

import fitz

from app.services.ocr_service import ocr_service
from app.services.page_analyzer import page_analyzer


class PageAnalysisService:
    """
    Постраничный анализ PDF-документов проекта.

    Если на странице есть текстовый слой — используем его.
    Если текста нет — автоматически запускаем OCR только этой страницы.
    """

    def __init__(self):

        self.projects_root = Path("projects")

    def analyze_pdf(
        self,
        file_path: Path,
    ) -> dict:

        document = fitz.open(file_path)

        pages = []

        text_pages_count = 0
        ocr_pages_count = 0

        try:

            for page_number, page in enumerate(
                document,
                start=1,
            ):

                # -------------------------------------------------
                # 1. ПРОБУЕМ ОБЫЧНЫЙ ТЕКСТОВЫЙ СЛОЙ
                # -------------------------------------------------

                text = (page.get_text() or "").strip()

                source = "text"

                ocr_used = False
                rotation = 0

                # -------------------------------------------------
                # 2. ЕСЛИ ТЕКСТА НЕТ — OCR ТОЛЬКО ЭТОЙ СТРАНИЦЫ
                # -------------------------------------------------

                if not text:

                    ocr_result = ocr_service.recognize_page(
                        str(file_path),
                        page_number,
                    )

                    text = (
                        ocr_result.get(
                            "text",
                            "",
                        )
                        or ""
                    ).strip()

                    source = "ocr"

                    ocr_used = True

                    rotation = ocr_result.get(
                        "rotation",
                        0,
                    )

                    ocr_pages_count += 1

                else:

                    text_pages_count += 1

                # -------------------------------------------------
                # 3. КЛАССИФИКАЦИЯ СТРАНИЦЫ
                # -------------------------------------------------

                page_result = page_analyzer.analyze_page(
                    text,
                    page_number,
                )

                page_data = {
                    "page": page_number,
                    "page_type": page_result.get("page_type"),
                    "score": page_result.get(
                        "score",
                        0,
                    ),
                    "source": source,
                    "ocr_used": ocr_used,
                    "rotation": rotation,
                    "text_length": len(text),
                    "preview": page_result.get(
                        "preview",
                        "",
                    ),
                    "text": text,
                }

                pages.append(page_data)

        finally:

            document.close()

        # ---------------------------------------------------------
        # 4. СТАТИСТИКА ПО ТИПАМ СТРАНИЦ
        # ---------------------------------------------------------

        page_types = {}

        for page in pages:

            page_type = page.get("page_type") or "Не определено"

            page_types[page_type] = (
                page_types.get(
                    page_type,
                    0,
                )
                + 1
            )

        return {
            "filename": file_path.name,
            "path": str(file_path),
            "pages_count": len(pages),
            "text_pages_count": (text_pages_count),
            "ocr_pages_count": (ocr_pages_count),
            "page_types": page_types,
            "pages": pages,
        }

    def analyze_project(
        self,
        project_name: str,
    ) -> dict:

        project_path = self.projects_root / project_name

        input_path = project_path / "input"

        analysis_path = project_path / "analysis"

        if not project_path.exists():

            raise FileNotFoundError(f"Проект не найден: {project_name}")

        if not input_path.exists():

            raise FileNotFoundError(f"Папка input не найдена: {input_path}")

        analysis_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        pdf_files = sorted(input_path.glob("*.pdf"))

        documents = []

        total_pages = 0
        total_ocr_pages = 0

        for pdf_file in pdf_files:

            document_result = self.analyze_pdf(pdf_file)

            documents.append(document_result)

            total_pages += document_result.get(
                "pages_count",
                0,
            )

            total_ocr_pages += document_result.get(
                "ocr_pages_count",
                0,
            )

        result = {
            "project": project_name,
            "documents_count": len(documents),
            "pages_count": total_pages,
            "ocr_pages_count": (total_ocr_pages),
            "documents": documents,
        }

        output_path = analysis_path / "page_analysis.json"

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=4,
            )

        result["output_path"] = str(output_path)

        return result


page_analysis_service = PageAnalysisService()
