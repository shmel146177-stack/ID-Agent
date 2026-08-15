import json
from datetime import datetime
from pathlib import Path

from app.services.document_completeness import document_completeness
from app.services.hidden_works_registry import hidden_works_registry
from app.services.supporting_documents_registry import supporting_documents_registry


class ProjectDocumentSet:
    """
    Формирование структуры комплекта
    исполнительной документации проекта.

    Версия v6.57:
    - создаёт 8 разделов;
    - анализирует проектную документацию;
    - определяет потенциальные АОСР;
    - проверяет фактически созданные файлы
      внутри разделов исполнительной документации;
    - обновляет статусы разделов.
    """

    SECTIONS = [
        {
            "number": "01",
            "code": "source_documents",
            "title": "Исходные документы",
            "folder": "01_Исходные_документы",
            "description": (
                "Проектная документация, технические условия, "
                "согласования и исходные материалы."
            ),
        },
        {
            "number": "02",
            "code": "working_drawings",
            "title": "Рабочая документация",
            "folder": "02_Рабочая_документация",
            "description": ("Рабочие чертежи, схемы, планы, узлы " "и спецификации."),
        },
        {
            "number": "03",
            "code": "hidden_works_acts",
            "title": "Акты скрытых работ",
            "folder": "03_Акты_скрытых_работ",
            "description": ("Акты освидетельствования скрытых работ."),
        },
        {
            "number": "04",
            "code": "executive_schemes",
            "title": "Исполнительные схемы",
            "folder": "04_Исполнительные_схемы",
            "description": ("Исполнительные схемы фактически " "выполненных работ."),
        },
        {
            "number": "05",
            "code": "tests",
            "title": "Протоколы и испытания",
            "folder": "05_Протоколы_и_испытания",
            "description": (
                "Протоколы измерений, испытаний, "
                "проверок и лабораторных исследований."
            ),
        },
        {
            "number": "06",
            "code": "quality_documents",
            "title": "Паспорта и сертификаты",
            "folder": "06_Паспорта_и_сертификаты",
            "description": (
                "Паспорта оборудования, сертификаты, "
                "декларации и документы качества."
            ),
        },
        {
            "number": "07",
            "code": "journals",
            "title": "Журналы работ",
            "folder": "07_Журналы_работ",
            "description": ("Общий и специальные журналы " "производства работ."),
        },
        {
            "number": "08",
            "code": "final_documents",
            "title": "Итоговые документы",
            "folder": "08_Итоговые_документы",
            "description": (
                "Итоговые реестры, отчёты " "и сводные документы ID-Agent."
            ),
        },
    ]

    ALLOWED_FILE_EXTENSIONS = {
        ".docx",
        ".doc",
        ".xlsx",
        ".xls",
        ".xlsm",
        ".pdf",
        ".json",
        ".dwg",
        ".dxf",
        ".jpg",
        ".jpeg",
        ".png",
    }

    def _project_path(
        self,
        project_name: str,
    ) -> Path:

        return Path("projects") / project_name

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

    def _load_json(
        self,
        path: Path,
    ) -> dict:

        if not path.exists():
            return {}

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    def _create_folders(
        self,
        project_name: str,
    ) -> list[dict]:

        root = self._executive_root(project_name)

        root.mkdir(
            parents=True,
            exist_ok=True,
        )

        result = []

        for section in self.SECTIONS:

            folder = root / section["folder"]

            folder.mkdir(
                parents=True,
                exist_ok=True,
            )

            result.append(
                {
                    **section,
                    "path": str(folder),
                }
            )

        return result

    def _list_section_files(
        self,
        folder_path: str | Path,
    ) -> list[dict]:

        folder = Path(folder_path)

        if not folder.exists():

            return []

        files = []

        for file in sorted(folder.rglob("*")):

            if not file.is_file():
                continue

            if file.suffix.lower() not in self.ALLOWED_FILE_EXTENSIONS:
                continue

            files.append(
                {
                    "name": (file.name),
                    "relative_path": str(file.relative_to(folder)),
                    "extension": (file.suffix.lower()),
                    "size_bytes": (file.stat().st_size),
                }
            )

        return files

    def _page_type_summary(
        self,
        project_name: str,
    ) -> dict:

        page_analysis_path = self._analysis_path(project_name) / "page_analysis.json"

        data = self._load_json(page_analysis_path)

        summary = {}

        for document in data.get(
            "documents",
            [],
        ):

            for page in document.get(
                "pages",
                [],
            ):

                page_type = page.get("page_type")

                if not page_type:
                    continue

                summary[page_type] = (
                    summary.get(
                        page_type,
                        0,
                    )
                    + 1
                )

        if not summary:

            stored_summary = data.get(
                "page_types",
                {},
            )

            if isinstance(
                stored_summary,
                dict,
            ):

                summary = stored_summary

        return summary

    def _detected_documents(
        self,
        project_name: str,
    ) -> dict:

        page_types = self._page_type_summary(project_name)

        source_types = {
            "Титульный лист",
            "Технические условия",
            "Согласование",
            "Охрана окружающей среды",
        }

        working_types = {
            "Ведомость рабочих чертежей",
            "Ситуационный план",
            "План электроснабжения",
            "Заземление",
            "Электрическая схема",
            "Узел монтажа",
            "Спецификация",
        }

        source_documents = {}
        working_documents = {}

        for page_type, count in page_types.items():

            if page_type in source_types:

                source_documents[page_type] = count

            elif page_type in working_types:

                working_documents[page_type] = count

        return {
            "source_documents": (source_documents),
            "working_drawings": (working_documents),
        }

    def _build_hidden_works_data(
        self,
        hidden_works_result: dict,
    ) -> dict:

        acts = []

        for act in hidden_works_result.get(
            "acts",
            [],
        ):

            evidence = []

            for item in act.get(
                "evidence",
                [],
            ):

                evidence.append(
                    {
                        "sheet_number": (item.get("sheet_number")),
                        "title": (item.get("title")),
                        "page_type": (item.get("page_type")),
                        "pages_count": (item.get("pages_count")),
                        "source": (item.get("source")),
                    }
                )

            acts.append(
                {
                    "code": (act.get("code")),
                    "title": (act.get("title")),
                    "act_title": (act.get("act_title")),
                    "status": (act.get("status")),
                    "priority": (act.get("priority")),
                    "confidence": (act.get("confidence")),
                    "confirmation_required": (act.get("confirmation_required")),
                    "confirmation": (act.get("confirmation")),
                    "evidence": (evidence),
                }
            )

        return {
            "acts_count": (
                hidden_works_result.get(
                    "acts_count",
                    0,
                )
            ),
            "high_priority_count": (
                hidden_works_result.get(
                    "high_priority_count",
                    0,
                )
            ),
            "requires_field_confirmation": (
                hidden_works_result.get(
                    "requires_field_confirmation",
                    False,
                )
            ),
            "acts": acts,
        }

    def _output_documents(
        self,
        project_name: str,
    ) -> list[dict]:

        output_folder = self._project_path(project_name) / "output"

        if not output_folder.exists():

            return []

        files = []

        for file in sorted(output_folder.iterdir()):

            if not file.is_file():
                continue

            if file.suffix.lower() not in {
                ".docx",
                ".xlsx",
                ".xlsm",
                ".pdf",
            }:
                continue

            files.append(
                {
                    "name": (file.name),
                    "path": str(file),
                    "extension": (file.suffix.lower()),
                    "size_bytes": (file.stat().st_size),
                }
            )

        return files

    def _build_sections(
        self,
        project_name: str,
        folders: list[dict],
        hidden_works_result: dict,
        supporting_documents_result: dict | None = None,
    ) -> list[dict]:

        detected = self._detected_documents(project_name)

        if supporting_documents_result is None:
            supporting_documents_result = supporting_documents_registry.analyze_project(
                project_name
            )

        supporting_by_code = {
            item.get("code"): item
            for item in supporting_documents_result.get("sections", [])
            if item.get("code")
        }

        sections = []

        for folder in folders:

            code = folder["code"]

            actual_files = self._list_section_files(folder["path"])

            section = {
                "number": (folder["number"]),
                "code": code,
                "title": (folder["title"]),
                "folder": (folder["folder"]),
                "path": (folder["path"]),
                "description": (folder["description"]),
                "status": ("Ожидает документов"),
                "detected": {},
                "actual_files_count": (len(actual_files)),
                "actual_files": (actual_files),
            }

            # -----------------------------------------------------
            # 01. ИСХОДНЫЕ ДОКУМЕНТЫ
            # 02. РАБОЧАЯ ДОКУМЕНТАЦИЯ
            # -----------------------------------------------------

            if code in detected:

                section["detected"] = detected[code]

                if section["detected"]:

                    section["status"] = "Документы обнаружены"

            # -----------------------------------------------------
            # 03. АОСР
            # -----------------------------------------------------

            if code == "hidden_works_acts":

                hidden_data = self._build_hidden_works_data(hidden_works_result)

                hidden_data["created_files_count"] = len(actual_files)

                hidden_data["created_files"] = actual_files

                section["detected"] = hidden_data

                acts_count = hidden_data.get(
                    "acts_count",
                    0,
                )

                if acts_count > 0 and actual_files:

                    section["status"] = (
                        "Черновики сформированы. " "Требует подтверждения"
                    )

                elif acts_count > 0:

                    section["status"] = "Требует подтверждения"

                elif actual_files:

                    section["status"] = "Документы обнаружены"

                else:

                    section["status"] = "АОСР автоматически " "не определены"

            # -----------------------------------------------------
            # 04-07. ФАКТИЧЕСКИЕ ФАЙЛЫ
            # -----------------------------------------------------

            if code in {
                "executive_schemes",
                "tests",
                "quality_documents",
                "journals",
            }:

                supporting_section = supporting_by_code.get(code, {})

                if code != "journals" and supporting_section:
                    section["detected"] = {
                        "required_count": (
                            supporting_section.get("required_count", 0)
                        ),
                        "high_priority_count": (
                            supporting_section.get("high_priority_count", 0)
                        ),
                        "documents": (
                            supporting_section.get("documents", [])
                        ),
                    }

                if actual_files:

                    section["detected"]["files_count"] = len(actual_files)
                    section["detected"]["files"] = actual_files

                    if code == "journals":

                        section["status"] = "Документы сформированы"

                    else:

                        section["status"] = "Документы обнаружены"

            # -----------------------------------------------------
            # 08. ИТОГОВЫЕ ДОКУМЕНТЫ
            # -----------------------------------------------------

            if code == "final_documents":

                final_files = self._output_documents(project_name)

                section["detected"] = {
                    "files_count": (len(final_files)),
                    "files": (final_files),
                }

                if final_files:

                    section["status"] = "Документы сформированы"

            sections.append(section)

        return sections

    def _missing_requirements(
        self,
        project_name: str,
    ) -> dict:

        completeness = document_completeness.check(project_name)

        return {
            "status": (completeness.get("status")),
            "required_count": (completeness.get("required_count")),
            "found_count": (completeness.get("found_count")),
            "missing_count": (completeness.get("missing_count")),
            "completeness_percent": (completeness.get("completeness_percent")),
            "missing_sheets": (
                completeness.get(
                    "missing_sheets",
                    [],
                )
            ),
        }

    def create(
        self,
        project_name: str,
    ) -> dict:

        project_path = self._project_path(project_name)

        if not project_path.exists():

            raise FileNotFoundError("Проект не найден: " f"{project_name}")

        # ---------------------------------------------------------
        # 1. СОЗДАЁМ СТРУКТУРУ ПАПОК
        # ---------------------------------------------------------

        folders = self._create_folders(project_name)

        # ---------------------------------------------------------
        # 2. ОПРЕДЕЛЯЕМ ПОТЕНЦИАЛЬНЫЕ АОСР
        # ---------------------------------------------------------

        hidden_works_result = hidden_works_registry.analyze_project(project_name)

        # ---------------------------------------------------------
        # 3. ФОРМИРУЕМ РАЗДЕЛЫ
        # ---------------------------------------------------------

        sections = self._build_sections(
            project_name,
            folders,
            hidden_works_result,
        )

        # ---------------------------------------------------------
        # 4. КОМПЛЕКТНОСТЬ ПРОЕКТА
        # ---------------------------------------------------------

        completeness = self._missing_requirements(project_name)

        # ---------------------------------------------------------
        # 5. СТАТИСТИКА ПО ФАКТИЧЕСКИМ ФАЙЛАМ
        # ---------------------------------------------------------

        actual_files_count = sum(
            section.get(
                "actual_files_count",
                0,
            )
            for section in sections
        )

        sections_with_files = sum(
            1
            for section in sections
            if section.get(
                "actual_files_count",
                0,
            )
            > 0
        )

        # ---------------------------------------------------------
        # 6. КАРТА ИСПОЛНИТЕЛЬНОЙ ДОКУМЕНТАЦИИ
        # ---------------------------------------------------------

        result = {
            "project": (project_name),
            "created_at": (datetime.now().isoformat(timespec="seconds")),
            "status": ("Готово"),
            "root_folder": str(self._executive_root(project_name)),
            "sections_count": (len(sections)),
            "sections_with_files": (sections_with_files),
            "actual_files_count": (actual_files_count),
            "sections": (sections),
            "hidden_works": {
                "status": (hidden_works_result.get("status")),
                "acts_count": (
                    hidden_works_result.get(
                        "acts_count",
                        0,
                    )
                ),
                "high_priority_count": (
                    hidden_works_result.get(
                        "high_priority_count",
                        0,
                    )
                ),
                "requires_field_confirmation": (
                    hidden_works_result.get(
                        "requires_field_confirmation",
                        False,
                    )
                ),
            },
            "project_completeness": (completeness),
        }

        # ---------------------------------------------------------
        # 7. СОХРАНЯЕМ JSON
        # ---------------------------------------------------------

        analysis_folder = self._analysis_path(project_name)

        analysis_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = analysis_folder / "project_document_set.json"

        with open(
            output_file,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=2,
            )

        result["analysis_file"] = str(output_file)

        return result


project_document_set = ProjectDocumentSet()
