import json
import re
from datetime import datetime
from pathlib import Path

import fitz


class ProjectSectionExporter:
    """
    Экспорт страниц проекта по разделам
    исполнительной документации.

    Версия v6.60:
    - читает page_analysis.json;
    - не изменяет исходные PDF;
    - формирует отдельный PDF исходных документов;
    - формирует отдельный PDF рабочей документации;
    - сохраняет результат анализа в JSON.
    """

    SOURCE_PAGE_TYPES = {
        "Титульный лист",
        "Технические условия",
        "Согласование",
        "Охрана окружающей среды",
    }

    WORKING_PAGE_TYPES = {
        "Ведомость рабочих чертежей",
        "Ситуационный план",
        "План электроснабжения",
        "Заземление",
        "Электрическая схема",
        "Узел монтажа",
        "Спецификация",
    }

    def _project_path(
        self,
        project_name: str,
    ) -> Path:

        return Path("projects") / project_name

    def _input_path(
        self,
        project_name: str,
    ) -> Path:

        return self._project_path(project_name) / "input"

    def _analysis_path(
        self,
        project_name: str,
    ) -> Path:

        return self._project_path(project_name) / "analysis"

    def _executive_root(
        self,
        project_name: str,
    ) -> Path:

        return (
            self._project_path(project_name)
            / "executive_docs"
            / "Исполнительная_документация"
        )

    def _source_folder(
        self,
        project_name: str,
    ) -> Path:

        return self._executive_root(project_name) / "01_Исходные_документы"

    def _working_folder(
        self,
        project_name: str,
    ) -> Path:

        return self._executive_root(project_name) / "02_Рабочая_документация"

    def _load_json(
        self,
        path: Path,
    ) -> dict:

        if not path.exists():

            raise FileNotFoundError(f"Файл анализа не найден: {path}")

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    def _safe_filename(
        self,
        value: str,
    ) -> str:

        value = re.sub(
            r'[<>:"/\\|?*]',
            "_",
            value,
        )

        return value.strip(" .")

    def _document_filename(
        self,
        document_data: dict,
    ) -> str | None:

        for key in (
            "filename",
            "file",
            "name",
            "document",
        ):

            value = document_data.get(key)

            if value:

                return Path(str(value)).name

        return None

    def _find_source_pdf(
        self,
        project_name: str,
        document_data: dict,
    ) -> Path:

        input_folder = self._input_path(project_name)

        filename = self._document_filename(document_data)

        if filename:

            candidate = input_folder / filename

            if candidate.exists():

                return candidate

        pdf_files = sorted(input_folder.glob("*.pdf"))

        if len(pdf_files) == 1:

            return pdf_files[0]

        if filename:

            for file in pdf_files:

                if file.name.lower() == filename.lower():

                    return file

        raise FileNotFoundError(
            ("Не удалось определить исходный PDF " f"для документа: {filename}")
        )

    def _page_number(
        self,
        page_data: dict,
    ) -> int | None:

        for key in (
            "page_number",
            "page",
            "number",
        ):

            value = page_data.get(key)

            if value is None:
                continue

            try:

                return int(value)

            except (
                TypeError,
                ValueError,
            ):

                continue

        return None

    def _collect_pages(
        self,
        page_analysis: dict,
    ) -> dict:

        source_pages = []
        working_pages = []
        unclassified_pages = []

        for document_index, document in enumerate(
            page_analysis.get(
                "documents",
                [],
            )
        ):

            for page in document.get(
                "pages",
                [],
            ):

                page_number = self._page_number(page)

                page_type = page.get("page_type")

                if page_number is None:
                    continue

                page_info = {
                    "document_index": (document_index),
                    "page_number": (page_number),
                    "page_type": (page_type),
                }

                if page_type in self.SOURCE_PAGE_TYPES:

                    source_pages.append(page_info)

                elif page_type in self.WORKING_PAGE_TYPES:

                    working_pages.append(page_info)

                else:

                    unclassified_pages.append(page_info)

        return {
            "source_pages": (source_pages),
            "working_pages": (working_pages),
            "unclassified_pages": (unclassified_pages),
        }

    def _export_group(
        self,
        project_name: str,
        page_analysis: dict,
        pages: list[dict],
        output_file: Path,
    ) -> dict:

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = fitz.open()

        exported_pages = []

        documents = page_analysis.get(
            "documents",
            [],
        )

        opened_documents = {}

        try:

            for page_info in pages:

                document_index = page_info["document_index"]

                if document_index >= len(documents):

                    continue

                document_data = documents[document_index]

                if document_index not in opened_documents:

                    source_pdf = self._find_source_pdf(
                        project_name,
                        document_data,
                    )

                    opened_documents[document_index] = {
                        "path": (source_pdf),
                        "document": (fitz.open(source_pdf)),
                    }

                source_item = opened_documents[document_index]

                source_document = source_item["document"]

                page_number = page_info["page_number"]

                # page_analysis использует
                # человекочитаемую нумерацию 1..N.
                source_page_index = page_number - 1

                if (
                    source_page_index < 0
                    or source_page_index >= source_document.page_count
                ):

                    continue

                destination.insert_pdf(
                    source_document,
                    from_page=(source_page_index),
                    to_page=(source_page_index),
                )

                exported_pages.append(
                    {
                        "source_file": (source_item["path"].name),
                        "source_page": (page_number),
                        "page_type": (page_info.get("page_type")),
                        "exported_page": (len(exported_pages) + 1),
                    }
                )

            if destination.page_count > 0:

                destination.save(
                    output_file,
                    garbage=4,
                    deflate=True,
                )

            elif output_file.exists():

                output_file.unlink()

        finally:

            destination.close()

            for item in opened_documents.values():

                item["document"].close()

        return {
            "file": (str(output_file) if output_file.exists() else None),
            "pages_count": (len(exported_pages)),
            "pages": (exported_pages),
        }

    def export_project(
        self,
        project_name: str,
    ) -> dict:

        project_path = self._project_path(project_name)

        if not project_path.exists():

            raise FileNotFoundError(("Проект не найден: " f"{project_name}"))

        page_analysis_file = self._analysis_path(project_name) / "page_analysis.json"

        page_analysis = self._load_json(page_analysis_file)

        groups = self._collect_pages(page_analysis)

        safe_project_name = self._safe_filename(project_name)

        source_output = self._source_folder(project_name) / (
            "Исходные_документы_" f"{safe_project_name}.pdf"
        )

        working_output = self._working_folder(project_name) / (
            "Рабочая_документация_" f"{safe_project_name}.pdf"
        )

        source_result = self._export_group(
            project_name,
            page_analysis,
            groups["source_pages"],
            source_output,
        )

        working_result = self._export_group(
            project_name,
            page_analysis,
            groups["working_pages"],
            working_output,
        )

        result = {
            "project": (project_name),
            "created_at": (datetime.now().isoformat(timespec="seconds")),
            "status": ("Готово"),
            "source_documents": (source_result),
            "working_drawings": (working_result),
            "unclassified_pages_count": (len(groups["unclassified_pages"])),
            "unclassified_pages": (groups["unclassified_pages"]),
            "total_exported_pages": (
                source_result["pages_count"] + working_result["pages_count"]
            ),
        }

        analysis_folder = self._analysis_path(project_name)

        analysis_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        result_file = analysis_folder / "project_section_export.json"

        with open(
            result_file,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=2,
            )

        result["analysis_file"] = str(result_file)

        return result


project_section_exporter = ProjectSectionExporter()
