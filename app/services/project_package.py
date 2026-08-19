import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from app.generators.project_document_set import project_document_set
from app.services.project_processor import project_processor


class ProjectPackage:
    """
    Формирование полного итогового пакета проекта.

    Версия v6.59:
    - запускает полный конвейер ID-Agent;
    - формирует исполнительную документацию;
    - копирует итоговый Excel и DOCX
      в раздел 08_Итоговые_документы;
    - оригиналы в output сохраняются;
    - учитывает реальные файлы внутри разделов;
    - формирует package_manifest.json.
    """

    ANALYSIS_FILES = [
        "project_analysis.json",
        "page_analysis.json",
        "drawing_register.json",
        "drawing_sheet_match.json",
        "hidden_works_registry.json",
        "supporting_documents_registry.json",
        "project_document_set.json",
    ]

    def _project_path(
        self,
        project_name: str,
    ) -> Path:

        return Path("projects") / project_name

    def _executive_docs_path(
        self,
        project_name: str,
    ) -> Path:

        return self._project_path(project_name) / "executive_docs"

    def _final_documents_folder(
        self,
        project_name: str,
    ) -> Path:

        return (
            self._executive_docs_path(project_name)
            / "Исполнительная_документация"
            / "08_Итоговые_документы"
        )

    def _copy_file(
        self,
        source: Path,
        destination_folder: Path,
    ) -> str | None:

        if not source.exists():
            return None

        destination_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = destination_folder / source.name

        shutil.copy2(
            source,
            destination,
        )

        return str(destination)

    def _copy_analysis_files(
        self,
        project_name: str,
        destination_folder: Path,
    ) -> list[str]:

        copied_files = []

        analysis_folder = self._project_path(project_name) / "analysis"

        for filename in self.ANALYSIS_FILES:

            source = analysis_folder / filename

            copied = self._copy_file(
                source,
                destination_folder,
            )

            if copied:

                copied_files.append(copied)

        return copied_files

    def _copy_project_card(
        self,
        project_name: str,
        destination_folder: Path,
    ) -> str | None:

        source = self._project_path(project_name) / "project.json"

        return self._copy_file(
            source,
            destination_folder,
        )

    def _load_project_card(
        self,
        project_name: str,
    ) -> dict:

        project_file = self._project_path(project_name) / "project.json"

        if not project_file.exists():
            return {}

        try:
            return json.loads(
                project_file.read_text(
                    encoding="utf-8",
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {}

    def _copy_output_documents(
        self,
        project_name: str,
        destination_folder: Path,
    ) -> list[str]:

        copied_files = []

        output_folder = self._project_path(project_name) / "output"

        if not output_folder.exists():

            return copied_files

        allowed_extensions = {
            ".docx",
            ".xlsx",
            ".xlsm",
            ".pdf",
        }

        for source in sorted(output_folder.iterdir()):

            if not source.is_file():
                continue

            if source.suffix.lower() not in allowed_extensions:
                continue

            copied = self._copy_file(
                source,
                destination_folder,
            )

            if copied:

                copied_files.append(copied)

        return copied_files

    def _sync_final_documents(
        self,
        project_name: str,
        processor_result: dict,
    ) -> list[str]:
        """
        Копирует итоговые документы,
        сформированные project_processor,
        в раздел 08_Итоговые_документы.

        Файлы из output не удаляются.
        """

        destination_folder = self._final_documents_folder(project_name)

        destination_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        copied_files = []

        source_files = [
            processor_result.get("excel"),
            processor_result.get("report"),
        ]

        for file_path in source_files:

            if not file_path:
                continue

            source = Path(file_path)

            copied = self._copy_file(
                source,
                destination_folder,
            )

            if copied:

                copied_files.append(copied)

        return copied_files

    def _relative_path(
        self,
        file_path: str | Path | None,
        package_folder: Path,
    ) -> str | None:

        if not file_path:
            return None

        path = Path(file_path)

        try:

            return path.relative_to(package_folder).as_posix()

        except ValueError:

            return str(path)

    def _inventory_package(
        self,
        package_folder: Path,
    ) -> dict:

        files = []
        folders = []

        if not package_folder.exists():

            return {
                "files": files,
                "folders": folders,
            }

        for path in sorted(package_folder.rglob("*")):

            relative_path = path.relative_to(package_folder)

            if path.is_dir():

                folders.append(str(relative_path))

                continue

            if path.name == "package_manifest.json":
                continue

            files.append(
                {
                    "name": (path.name),
                    "relative_path": str(relative_path),
                    "extension": (path.suffix.lower()),
                    "size_bytes": (path.stat().st_size),
                }
            )

        return {
            "files": files,
            "folders": folders,
        }

    def _build_generated_acts(
        self,
        processor_result: dict,
        package_folder: Path,
    ) -> dict:

        hidden_works = processor_result.get(
            "hidden_works_acts",
            {},
        )

        created = []

        for act in hidden_works.get(
            "created",
            [],
        ):

            created.append(
                {
                    "code": (act.get("code")),
                    "title": (act.get("title")),
                    "priority": (act.get("priority")),
                    "file": (
                        self._relative_path(
                            act.get("file"),
                            package_folder,
                        )
                    ),
                    "status": ("Черновик. " "Требует подтверждения"),
                }
            )

        return {
            "acts_detected": (
                hidden_works.get(
                    "acts_detected",
                    0,
                )
            ),
            "acts_created": (
                hidden_works.get(
                    "acts_created",
                    0,
                )
            ),
            "acts_skipped": (
                hidden_works.get(
                    "acts_skipped",
                    0,
                )
            ),
            "requires_field_confirmation": (
                hidden_works.get(
                    "requires_field_confirmation",
                    False,
                )
            ),
            "created": (created),
        }

    def _build_journal(
        self,
        processor_result: dict,
        package_folder: Path,
    ) -> dict:

        journal_path = processor_result.get("hidden_works_journal")

        if not journal_path:

            return {
                "status": ("Не сформирован"),
                "file": None,
            }

        journal_file = Path(journal_path)

        return {
            "status": ("Черновик. " "Требует подтверждения"),
            "file": (
                self._relative_path(
                    journal_path,
                    package_folder,
                )
            ),
            "exists": (journal_file.exists()),
            "size_bytes": (
                journal_file.stat().st_size if journal_file.exists() else None
            ),
        }

    def _build_document_sections(
        self,
        document_set_result: dict,
        package_folder: Path,
    ) -> list[dict]:

        sections = []

        for section in document_set_result.get(
            "sections",
            [],
        ):

            section_path = section.get("path")

            relative_path = (
                self._relative_path(
                    section_path,
                    package_folder,
                )
                if section_path
                else None
            )

            actual_files = []

            for file_data in section.get(
                "actual_files",
                [],
            ):

                actual_files.append(
                    {
                        "name": (file_data.get("name")),
                        "relative_path": (file_data.get("relative_path")),
                        "extension": (file_data.get("extension")),
                        "size_bytes": (file_data.get("size_bytes")),
                    }
                )

            section_data = {
                "number": (section.get("number")),
                "code": (section.get("code")),
                "title": (section.get("title")),
                "status": (section.get("status")),
                "folder": (relative_path),
                "actual_files_count": (
                    section.get(
                        "actual_files_count",
                        0,
                    )
                ),
                "actual_files": (actual_files),
            }

            detected = section.get("detected", {})

            code = section.get("code")

            if code == "hidden_works_acts":

                section_data["acts_detected"] = detected.get(
                    "acts_count",
                    0,
                )

                section_data["acts_created_files"] = detected.get(
                    "created_files_count",
                    0,
                )

                section_data["requires_field_confirmation"] = detected.get(
                    "requires_field_confirmation",
                    False,
                )

            elif code in {
                "executive_schemes",
                "tests",
                "quality_documents",
            }:

                section_data["required_count"] = detected.get(
                    "required_count",
                    0,
                )

                section_data["found_count"] = detected.get(
                    "found_count",
                    0,
                )

                section_data["missing_count"] = detected.get(
                    "missing_count",
                    0,
                )

                section_data["high_priority_count"] = detected.get(
                    "high_priority_count",
                    0,
                )

                section_data["required_documents"] = detected.get(
                    "documents",
                    [],
                )

            elif code == "final_documents":

                section_data["generated_files_count"] = detected.get(
                    "files_count",
                    0,
                )

                section_data["generated_files"] = detected.get(
                    "files",
                    [],
                )

            sections.append(section_data)

        return sections

    def _resolve_manifest_status(
        self,
        processor_result: dict,
        generated_acts: dict,
        hidden_works_journal: dict,
        supporting_documents: dict,
        project_mode: str = "production",
    ) -> str:

        if project_mode == "training":
            return "Учебный комплект"

        incomplete_status = (
            "\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 "
            "\u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442"
        )

        draft_status = (
            "\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a. "
            "\u0422\u0440\u0435\u0431\u0443\u0435\u0442 "
            "\u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f"
        )

        waiting_documents_status = (
            "\u041e\u0436\u0438\u0434\u0430\u0435\u0442 "
            "\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432"
        )

        not_formed_status = (
            "\u041d\u0435 "
            "\u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d"
        )

        completeness = processor_result.get(
            "completeness",
            {},
        )

        if (
            completeness.get(
                "missing_count",
                0,
            )
            or 0
        ) > 0:
            return incomplete_status

        incomplete_section_statuses = {
            waiting_documents_status,
            incomplete_status,
        }

        for section in supporting_documents.get(
            "sections",
            [],
        ):
            if section.get("status") in incomplete_section_statuses:
                return incomplete_status

        journal_status = hidden_works_journal.get("status")

        if (
            generated_acts.get(
                "acts_detected",
                0,
            ) > 0
            and journal_status == not_formed_status
        ):
            return incomplete_status

        if (
            generated_acts.get(
                "requires_field_confirmation",
                False,
            )
            or supporting_documents.get(
                "requires_field_confirmation",
                False,
            )
            or journal_status == draft_status
        ):
            return draft_status

        return (
            processor_result.get("status")
            or "\u0413\u043e\u0442\u043e\u0432\u043e"
        )

    def _create_manifest(
        self,
        project_name: str,
        destination_folder: Path,
        processor_result: dict,
        document_set_result: dict,
        inventory: dict,
        final_documents_copied: list[str],
    ) -> str:

        completeness = processor_result.get(
            "completeness",
            {},
        )

        generated_acts = self._build_generated_acts(
            processor_result,
            destination_folder,
        )

        supporting_documents = processor_result.get(
            "supporting_documents",
            {},
        )

        hidden_works_journal = self._build_journal(
            processor_result,
            destination_folder,
        )

        document_sections = self._build_document_sections(
            document_set_result,
            destination_folder,
        )

        project_card = self._load_project_card(project_name)

        project_mode = project_card.get(
            "project_mode",
            "production",
        )

        manifest_status = self._resolve_manifest_status(
            processor_result,
            generated_acts,
            hidden_works_journal,
            supporting_documents,
            project_mode=project_mode,
        )

        files = inventory.get(
            "files",
            [],
        )

        folders = inventory.get(
            "folders",
            [],
        )

        manifest = {
            "project": (project_name),
            "project_mode": (project_mode),
            "project_note": (
                project_card.get(
                    "project_note",
                    "",
                )
            ),
            "created_at": (datetime.now().isoformat(timespec="seconds")),
            "status": (manifest_status),
            "package": {
                "root_folder": str(destination_folder),
                "files_count": (len(files)),
                "folders_count": (len(folders)),
                "total_files_with_manifest": (len(files) + 1),
            },
            "completeness": {
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
            },
            "hidden_works_acts": (generated_acts),
            "hidden_works_journal": (hidden_works_journal),
            "supporting_documents": {
                "status": (supporting_documents.get("status")),
                "requirements_count": (
                    supporting_documents.get("requirements_count", 0)
                ),
                "high_priority_count": (
                    supporting_documents.get("high_priority_count", 0)
                ),
                "requires_field_confirmation": (
                    supporting_documents.get(
                        "requires_field_confirmation",
                        False,
                    )
                ),
                "sections": (supporting_documents.get("sections", [])),
            },
            "document_set": {
                "sections_count": (
                    document_set_result.get(
                        "sections_count",
                        0,
                    )
                ),
                "sections_with_files": (
                    document_set_result.get(
                        "sections_with_files",
                        0,
                    )
                ),
                "actual_files_count": (
                    document_set_result.get(
                        "actual_files_count",
                        0,
                    )
                ),
            },
            "document_sections": (document_sections),
            "generated_documents": {
                "excel": (
                    self._relative_path(
                        processor_result.get("excel"),
                        destination_folder,
                    )
                ),
                "report": (
                    self._relative_path(
                        processor_result.get("report"),
                        destination_folder,
                    )
                ),
                "hidden_works_journal": (hidden_works_journal.get("file")),
                "final_documents_section": [
                    self._relative_path(
                        file_path,
                        destination_folder,
                    )
                    for file_path in final_documents_copied
                ],
            },
            "folders": (folders),
            "files": (files),
            "note": (
                "Итоговые Excel и DOCX автоматически "
                "скопированы в раздел "
                "08_Итоговые_документы. "
                "Оригиналы файлов в папке output "
                "сохранены. АОСР и журнал являются "
                "черновиками ID-Agent и требуют "
                "инженерной проверки и подтверждения "
                "фактических работ."
            ),
        }

        manifest_path = destination_folder / "package_manifest.json"

        with open(
            manifest_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                manifest,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return str(manifest_path)

    def create(
        self,
        project_name: str,
    ) -> dict:

        project_path = self._project_path(project_name)

        if not project_path.exists():

            raise FileNotFoundError("Проект не найден: " f"{project_name}")

        # ---------------------------------------------------------
        # 1. ПОЛНЫЙ КОНВЕЙЕР ID-AGENT
        # ---------------------------------------------------------

        processor_result = project_processor.process(project_name)

        # ---------------------------------------------------------
        # 2. КОПИРУЕМ ИТОГОВЫЕ ДОКУМЕНТЫ
        #    В РАЗДЕЛ 08
        # ---------------------------------------------------------

        final_documents_copied = self._sync_final_documents(
            project_name,
            processor_result,
        )

        # ---------------------------------------------------------
        # 3. ФАКТИЧЕСКАЯ СТРУКТУРА
        #    ИСПОЛНИТЕЛЬНОЙ ДОКУМЕНТАЦИИ
        #
        # ВАЖНО:
        # вызывается ПОСЛЕ копирования,
        # поэтому раздел 08 уже увидит
        # реальные файлы.
        # ---------------------------------------------------------

        document_set_result = project_document_set.create(project_name)

        # ---------------------------------------------------------
        # 4. ПАПКА ПАКЕТА
        # ---------------------------------------------------------

        destination_folder = self._executive_docs_path(project_name)

        destination_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        copied_files = []

        # ---------------------------------------------------------
        # 5. ИТОГОВЫЕ DOCX / XLSX / PDF
        #    НА ВЕРХНИЙ УРОВЕНЬ ПАКЕТА
        # ---------------------------------------------------------

        copied_files.extend(
            self._copy_output_documents(
                project_name,
                destination_folder,
            )
        )

        # ---------------------------------------------------------
        # 6. КАРТОЧКА ПРОЕКТА
        # ---------------------------------------------------------

        project_card = self._copy_project_card(
            project_name,
            destination_folder,
        )

        if project_card:

            copied_files.append(project_card)

        # ---------------------------------------------------------
        # 7. JSON АНАЛИЗА
        # ---------------------------------------------------------

        copied_files.extend(
            self._copy_analysis_files(
                project_name,
                destination_folder,
            )
        )

        copied_files = list(dict.fromkeys(copied_files))

        # ---------------------------------------------------------
        # 8. ПОЛНАЯ ИНВЕНТАРИЗАЦИЯ
        # ---------------------------------------------------------

        inventory = self._inventory_package(destination_folder)

        # ---------------------------------------------------------
        # 9. MANIFEST
        # ---------------------------------------------------------

        manifest_path = self._create_manifest(
            project_name,
            destination_folder,
            processor_result,
            document_set_result,
            inventory,
            final_documents_copied,
        )

        manifest_data = json.loads(
            Path(manifest_path).read_text(
                encoding="utf-8",
            )
        )

        manifest_status = (
            manifest_data.get("status")
            or processor_result.get("status")
            or "\u0413\u043e\u0442\u043e\u0432\u043e"
        )

        completeness = processor_result.get(
            "completeness",
            {},
        )

        hidden_works = processor_result.get(
            "hidden_works_acts",
            {},
        )

        return {
            "project": (project_name),
            "status": (manifest_status),
            "package_folder": str(destination_folder),
            "files_count": (
                len(
                    inventory.get(
                        "files",
                        [],
                    )
                )
            ),
            "folders_count": (
                len(
                    inventory.get(
                        "folders",
                        [],
                    )
                )
            ),
            "total_files_with_manifest": (
                len(
                    inventory.get(
                        "files",
                        [],
                    )
                )
                + 1
            ),
            "manifest": (manifest_path),
            "completeness_percent": (completeness.get("completeness_percent")),
            "missing_sheets": (
                completeness.get(
                    "missing_sheets",
                    [],
                )
            ),
            "acts_detected": (
                hidden_works.get(
                    "acts_detected",
                    0,
                )
            ),
            "acts_created": (
                hidden_works.get(
                    "acts_created",
                    0,
                )
            ),
            "acts_skipped": (
                hidden_works.get(
                    "acts_skipped",
                    0,
                )
            ),
            "hidden_works_journal": (processor_result.get("hidden_works_journal")),
            "final_documents_copied": (len(final_documents_copied)),
            "final_documents_files": (final_documents_copied),
            "document_sections": (
                document_set_result.get(
                    "sections_count",
                    0,
                )
            ),
            "sections_with_files": (
                document_set_result.get(
                    "sections_with_files",
                    0,
                )
            ),
            "section_files_count": (
                document_set_result.get(
                    "actual_files_count",
                    0,
                )
            ),
            "copied_files": (copied_files),
        }



    def create_zip(
        self,
        project_name: str,
    ) -> str:

        package_result = self.create(project_name)

        package_folder = Path(
            package_result["package_folder"]
        )

        output_folder = (
            self._project_path(project_name)
            / "output"
        )

        output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        zip_path = (
            output_folder
            / f"Комплект_{project_name}.zip"
        )

        with zipfile.ZipFile(
            zip_path,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as archive:

            for file_path in sorted(
                package_folder.rglob("*")
            ):

                if not file_path.is_file():
                    continue

                archive.write(
                    file_path,
                    arcname=file_path.relative_to(
                        package_folder
                    ),
                )

        return str(zip_path)


project_package = ProjectPackage()
