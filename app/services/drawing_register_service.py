import json
from pathlib import Path

from app.services.drawing_register_analyzer import (
    drawing_register_analyzer,
)
from app.services.ocr_service import ocr_service


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

    def _ocr_register_text(
        self,
        document: dict,
        page: dict,
    ) -> str:
        """Читает видимую таблицу, не доверяя скрытому текстовому слою PDF."""

        file_path = document.get("path")
        page_number = page.get("page")

        if not file_path or not isinstance(page_number, int):
            return ""

        try:

            result = ocr_service.recognize_page_region(
                file_path,
                page_number,
                region=(0.0, 0.0, 0.505, 0.5),
                language="rus",
                psm=3,
            )

        except Exception:
            return ""

        return result.get("text", "") or ""

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

                analysis_source = "embedded_text"

                visual_text = self._ocr_register_text(
                    document,
                    page,
                )

                if visual_text:

                    visual_analysis = drawing_register_analyzer.analyze_text(
                        visual_text,
                        allow_title_only=True,
                    )

                    visual_is_usable = (
                        visual_analysis.get("register_block_detected", False)
                        and visual_analysis.get("entries_count", 0)
                        >= analysis.get("entries_count", 0)
                    )

                    if visual_is_usable:

                        embedded_expected_count = analysis.get(
                            "expected_sheet_count",
                            0,
                        )

                        visual_entries = visual_analysis.get(
                            "entries",
                            [],
                        )

                        if (
                            not visual_analysis.get("numbering_restored", False)
                            and embedded_expected_count == len(visual_entries)
                        ):

                            for index, entry in enumerate(
                                visual_entries,
                                start=1,
                            ):
                                entry["sheet_number"] = index
                                entry["number_source"] = (
                                    "restored_visual_sequence"
                                )

                            visual_analysis["numbering_restored"] = True
                            visual_analysis["numbered_entries_count"] = len(
                                visual_entries
                            )
                            visual_analysis["expected_sheet_count"] = (
                                embedded_expected_count
                            )

                        analysis = visual_analysis
                        analysis_source = "visual_ocr"

                register_data = {
                    "filename": (filename),
                    "page": page.get("page"),
                    "page_type": (page_type),
                    "analysis_source": (analysis_source),
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
