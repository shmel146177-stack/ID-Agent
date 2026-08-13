from pathlib import Path
import json
from pathlib import Path
from app.services.document_registry import document_registry
from app.services.drawing_sheet_matcher import drawing_sheet_matcher


class DocumentCompleteness:
    """
    Проверка комплектности проекта.

    Профили:

    equipment
        Проверка комплекта документации на оборудование.

    project
        Проверка рабочего проекта по ведомости
        рабочих чертежей.

        Основной результат берётся из сопоставления:
        ведомость -> реальные страницы PDF.
    """

    EQUIPMENT_REQUIRED_DOCUMENTS = [
        "Паспорт оборудования",
        "Сертификат",
        "Схема",
        "Протокол",
        "Руководство",
    ]

    # Оставляем для совместимости
    # со старым кодом.
    REQUIRED_DOCUMENTS = EQUIPMENT_REQUIRED_DOCUMENTS

    def _get_registry(
        self,
        project_name: str,
    ) -> dict:

        return document_registry.build(project_name)

    def _collect_classifications(
        self,
        registry: dict,
    ) -> list[str]:

        classifications = []

        for document in registry.get(
            "documents",
            [],
        ):

            classification = document.get("classification")

            if classification:

                classifications.append(classification)

        return classifications

    def _has_project_page_markers(
        self,
        project_name: str,
    ) -> bool:

        analysis_path = (
            Path("projects")
            / project_name
            / "analysis"
            / "page_analysis.json"
        )

        if not analysis_path.exists():
            return False

        try:
            data = json.loads(
                analysis_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return False

        project_page_markers = {
            "\u0412\u0435\u0434\u043e\u043c\u043e\u0441\u0442\u044c \u0440\u0430\u0431\u043e\u0447\u0438\u0445 \u0447\u0435\u0440\u0442\u0435\u0436\u0435\u0439",
            "\u0421\u0438\u0442\u0443\u0430\u0446\u0438\u043e\u043d\u043d\u044b\u0439 \u043f\u043b\u0430\u043d",
            "\u041f\u043b\u0430\u043d \u044d\u043b\u0435\u043a\u0442\u0440\u043e\u0441\u043d\u0430\u0431\u0436\u0435\u043d\u0438\u044f",
            "\u0417\u0430\u0437\u0435\u043c\u043b\u0435\u043d\u0438\u0435",
            "\u042d\u043b\u0435\u043a\u0442\u0440\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u0441\u0445\u0435\u043c\u0430",
            "\u0423\u0437\u0435\u043b \u043c\u043e\u043d\u0442\u0430\u0436\u0430",
            "\u0421\u043f\u0435\u0446\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f",
        }

        for document in data.get(
            "documents",
            [],
        ):

            page_types = document.get(
                "page_types",
                {},
            )

            if not isinstance(
                page_types,
                dict,
            ):
                continue

            if (
                set(page_types.keys())
                & project_page_markers
            ):
                return True

        return False

    def _detect_profile(
        self,
        project_name: str,
    ) -> str:
        """
        Определяет тип проекта.

        Если в реестре есть чертежи,
        считаем проект рабочей документацией.

        Если обнаружены документы оборудования,
        используется профиль equipment.
        """

        if self._has_project_page_markers(project_name):
            return "project"

        registry = self._get_registry(project_name)

        classifications = self._collect_classifications(registry)

        equipment_markers = {
            "Паспорт оборудования",
            "Сертификат",
            "Руководство",
            "Документация оборудования",
        }

        if any(
            classification in equipment_markers for classification in classifications
        ):

            return "equipment"

        if "Чертеж" in classifications:

            return "project"

        # Для неизвестных проектов
        # оставляем старое безопасное поведение.
        return "equipment"

    def _check_equipment(
        self,
        project_name: str,
    ) -> dict:

        registry = self._get_registry(project_name)

        classifications = self._collect_classifications(registry)

        documents = []

        found_count = 0

        for document_type in self.EQUIPMENT_REQUIRED_DOCUMENTS:

            present = document_type in classifications

            if present:

                found_count += 1

            documents.append(
                {
                    "document_type": (document_type),
                    "present": present,
                    "status": ("Есть" if present else "Отсутствует"),
                }
            )

        required_count = len(self.EQUIPMENT_REQUIRED_DOCUMENTS)

        missing_count = required_count - found_count

        completeness_percent = (
            round(
                (found_count / required_count * 100),
                1,
            )
            if required_count
            else 0.0
        )

        status = "Полный комплект" if missing_count == 0 else "Неполный комплект"

        return {
            "project": project_name,
            "status": status,
            "profile": "equipment",
            "profile_name": ("Документация оборудования"),
            "required_count": (required_count),
            "found_count": (found_count),
            "missing_count": (missing_count),
            "completeness_percent": (completeness_percent),
            "documents": documents,
        }

    def _check_project(
        self,
        project_name: str,
    ) -> dict:
        """
        Проверка проектной документации.

        Matcher автоматически:
        1. читает drawing_register.json;
        2. читает page_analysis.json;
        3. сравнивает ведомость с PDF;
        4. обновляет drawing_sheet_match.json.
        """

        sheet_match = drawing_sheet_matcher.analyze_project(project_name)

        required_count = sheet_match.get(
            "expected_count",
            0,
        )

        found_count = sheet_match.get(
            "found_count",
            0,
        )

        missing_count = sheet_match.get(
            "missing_count",
            0,
        )

        completeness_percent = sheet_match.get(
            "completeness_percent",
            0.0,
        )

        matches = sheet_match.get(
            "matches",
            [],
        )

        documents = []

        for match in matches:

            documents.append(
                {
                    "sheet_number": (match.get("sheet_number")),
                    "title": (match.get("title")),
                    "present": (
                        match.get(
                            "found",
                            False,
                        )
                    ),
                    "status": (
                        "Есть"
                        if match.get(
                            "found",
                            False,
                        )
                        else "Отсутствует"
                    ),
                    "matched_page": (match.get("matched_page")),
                    "matched_filename": (match.get("matched_filename")),
                    "matched_page_type": (match.get("matched_page_type")),
                    "score": (
                        match.get(
                            "score",
                            0,
                        )
                    ),
                    "confidence": (
                        match.get(
                            "confidence",
                            "Нет",
                        )
                    ),
                }
            )

        missing_sheets = sheet_match.get(
            "missing_sheets",
            [],
        )

        status = (
            "Полный комплект"
            if (required_count > 0 and missing_count == 0)
            else "Неполный комплект"
        )

        return {
            "project": project_name,
            "status": status,
            "profile": "project",
            "profile_name": ("Проектная документация"),
            "check_method": ("Ведомость рабочих чертежей " "↔ реальные страницы PDF"),
            "required_count": (required_count),
            "found_count": (found_count),
            "missing_count": (missing_count),
            "completeness_percent": (completeness_percent),
            "documents": documents,
            "missing_sheets": (missing_sheets),
            "sheet_match_status": (sheet_match.get("status")),
            "sheet_match_file": (sheet_match.get("output_path")),
        }

    def check(
        self,
        project_name: str,
        profile: str = "auto",
    ) -> dict:

        selected_profile = profile

        if selected_profile == "auto":

            selected_profile = self._detect_profile(project_name)

        if selected_profile == "project":

            return self._check_project(project_name)

        if selected_profile == "equipment":

            return self._check_equipment(project_name)

        raise ValueError("Неизвестный профиль " f"комплектности: {profile}")


document_completeness = DocumentCompleteness()
