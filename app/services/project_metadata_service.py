from pathlib import Path

import fitz

from app.services.project_manager import project_manager
from app.services.project_metadata_analyzer import project_metadata_analyzer
from app.services.ocr_service import ocr_service


class ProjectMetadataService:
    """Автоматическое заполнение карточки проекта по документам из input."""

    def __init__(self):
        self.projects_root = Path("projects")

    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Извлекает текст из PDF."""

        text_parts = []

        with fitz.open(pdf_path) as document:
            for page in document:
                page_text = page.get_text()

                if page_text:
                    text_parts.append(page_text)

        return "\n".join(text_parts)

    def _extract_project_people_with_ocr(
        self,
        pdf_files: list[Path],
    ) -> dict:
        """Extract designer and chief engineer using one OCR pass."""

        result = {
            "designer": None,
            "chief_engineer": None,
        }

        label = (
            "\u043f\u0440\u043e\u0435\u043a\u0442\u043d\u0430\u044f "
            "\u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f"
        )

        for pdf_path in pdf_files:
            with fitz.open(pdf_path) as document:
                for page_number, page in enumerate(
                    document,
                    start=1,
                ):
                    page_text = page.get_text() or ""

                    if label not in page_text.lower():
                        continue

                    try:
                        ocr_result = ocr_service.recognize_page(
                            str(pdf_path),
                            page_number=page_number,
                            language="rus+eng",
                            dpi=300,
                        )
                    except Exception:
                        continue

                    ocr_text = ocr_result.get("text", "")

                    if not ocr_text:
                        continue

                    ocr_metadata = (
                        project_metadata_analyzer.analyze_text(
                            ocr_text
                        )
                    )

                    result["designer"] = (
                        ocr_metadata.get("designer")
                    )
                    result["chief_engineer"] = (
                        ocr_metadata.get("chief_engineer")
                    )

                    if (
                        result["designer"]
                        or result["chief_engineer"]
                    ):
                        return result

        return result

    def update_from_project(
        self,
        project_name: str,
        overwrite: bool = False,
    ) -> dict:
        """
        Ищет реквизиты во всех PDF проекта и обновляет project.json.

        По умолчанию уже заполненные поля не перезаписываются.
        """

        project_path = self.projects_root / project_name
        input_path = project_path / "input"

        if not project_path.exists():
            raise FileNotFoundError(f"Проект не найден: {project_name}")

        if not input_path.exists():
            raise FileNotFoundError(f"Папка input не найдена: {input_path}")

        pdf_files = sorted(input_path.glob("*.pdf"))

        if not pdf_files:
            return {
                "project": project_name,
                "status": "PDF документы не найдены",
                "metadata": {},
                "updated_fields": {},
            }

        all_text = []

        for pdf_path in pdf_files:
            text = self._extract_pdf_text(pdf_path)

            if text:
                all_text.append(text)

        combined_text = "\n".join(all_text)

        if not combined_text.strip():
            return {
                "project": project_name,
                "status": "Текст в PDF не найден",
                "metadata": {},
                "updated_fields": {},
            }

        metadata = project_metadata_analyzer.analyze_text(combined_text)

        # PROJECT PEOPLE OCR FALLBACK
        if (
            not metadata.get("designer")
            or not metadata.get("chief_engineer")
        ):
            people = self._extract_project_people_with_ocr(
                pdf_files
            )

            if (
                not metadata.get("designer")
                and people.get("designer")
            ):
                metadata["designer"] = people["designer"]

            if (
                not metadata.get("chief_engineer")
                and people.get("chief_engineer")
            ):
                metadata["chief_engineer"] = (
                    people["chief_engineer"]
                )

        current_project = project_manager.get_project(project_name)

        updated_fields = {}

        for field, value in metadata.items():
            if not value:
                continue

            current_value = current_project.get(field)

            if overwrite or not current_value:
                updated_fields[field] = value

        if updated_fields:
            project = project_manager.update_project(
                project_name,
                updated_fields,
            )
        else:
            project = current_project

        return {
            "project": project_name,
            "status": "Готово",
            "pdf_count": len(pdf_files),
            "metadata": metadata,
            "updated_fields": updated_fields,
            "project_card": project,
        }


project_metadata_service = ProjectMetadataService()
