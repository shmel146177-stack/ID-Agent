import json
from pathlib import Path

from app.services.drawing_register_analyzer import (
    drawing_register_analyzer,
)


class DrawingRegisterService:
    """
    Сервис анализа ведомости рабочих чертежей проекта.

    Использует уже готовый page_analysis.json,
    находит страницы типа
    "Ведомость рабочих чертежей",
    анализирует их и сохраняет результат
    в drawing_register.json.
    """

    def _project_path(
        self,
        project_name: str,
    ) -> Path:

        return Path("projects") / project_name

    def _page_analysis_path(
        self,
        project_name: str,
    ) -> Path:

        return self._project_path(project_name) / "analysis" / "page_analysis.json"

    def _output_path(
        self,
        project_name: str,
    ) -> Path:

        return self._project_path(project_name) / "analysis" / "drawing_register.json"

    def _load_page_analysis(
        self,
        project_name: str,
    ) -> dict:

        file_path = self._page_analysis_path(project_name)

        if not file_path.exists():

            raise FileNotFoundError("Не найден файл " f"{file_path}")

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    def analyze_project(
        self,
        project_name: str,
    ) -> dict:

        page_analysis = self._load_page_analysis(project_name)

        registers = []

        total_entries = 0

        for document in page_analysis.get("documents", []):

            filename = document.get("filename")

            for page in document.get("pages", []):

                page_type = page.get("page_type")

                if page_type != "Ведомость рабочих чертежей":
                    continue

                text = page.get("text", "") or ""

                analysis = drawing_register_analyzer.analyze_text(text)

                register_data = {
                    "filename": (filename),
                    "page": page.get("page"),
                    "page_type": (page_type),
                    "register_detected": (
                        analysis.get(
                            "register_detected",
                            False,
                        )
                    ),
                    "register_block_detected": (
                        analysis.get(
                            "register_block_detected",
                            False,
                        )
                    ),
                    "entries_count": (
                        analysis.get(
                            "entries_count",
                            0,
                        )
                    ),
                    "numbered_entries_count": (
                        analysis.get(
                            "numbered_entries_count",
                            0,
                        )
                    ),
                    "numbering_restored": (
                        analysis.get(
                            "numbering_restored",
                            False,
                        )
                    ),
                    "expected_sheet_count": (
                        analysis.get(
                            "expected_sheet_count",
                            0,
                        )
                    ),
                    "number_evidence": (
                        analysis.get(
                            "number_evidence",
                            [],
                        )
                    ),
                    "entries": (
                        analysis.get(
                            "entries",
                            [],
                        )
                    ),
                }

                registers.append(register_data)

                total_entries += register_data["entries_count"]

        expected_sheet_count = 0

        if registers:

            expected_sheet_count = max(
                register.get(
                    "expected_sheet_count",
                    0,
                )
                for register in registers
            )

        output_path = self._output_path(project_name)

        result = {
            "project": project_name,
            "status": ("Готово" if registers else "Ведомость не найдена"),
            "registers_count": len(registers),
            "entries_count": (total_entries),
            "expected_sheet_count": (expected_sheet_count),
            "registers": (registers),
            "output_path": str(output_path),
        }

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return result


drawing_register_service = DrawingRegisterService()
