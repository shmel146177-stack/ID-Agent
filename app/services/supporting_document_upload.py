from pathlib import Path, PurePosixPath
from typing import BinaryIO


class SupportingDocumentUpload:
    """Загрузка сопроводительного документа с повторным анализом проекта."""

    DEFAULT_MAX_FILE_SIZE_BYTES = 512 * 1024 * 1024
    COPY_CHUNK_SIZE = 1024 * 1024

    SECTIONS = {
        "executive_schemes": {
            "number": "04",
            "title": "Исполнительные схемы",
        },
        "tests": {
            "number": "05",
            "title": "Протоколы и испытания",
        },
        "quality_documents": {
            "number": "06",
            "title": "Документы о качестве",
        },
    }

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".jpg",
        ".jpeg",
        ".png",
        ".tif",
        ".tiff",
    }

    def __init__(
        self,
        processor=None,
        max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    ):
        if max_file_size_bytes <= 0:
            raise ValueError(
                "Максимальный размер файла должен быть положительным"
            )

        self.projects_root = Path("projects")
        self.processor = processor
        self.max_file_size_bytes = max_file_size_bytes

    def _project_path(self, project_name: str) -> Path:
        value = (project_name or "").strip()
        normalized = value.replace("\\", "/")

        if (
            not value
            or normalized in {".", ".."}
            or PurePosixPath(normalized).name != normalized
        ):
            raise ValueError("Некорректное имя проекта")

        root = self.projects_root.resolve()
        project_path = self.projects_root / value

        try:
            project_path.resolve().relative_to(root)
        except ValueError as error:
            raise ValueError(
                "Путь проекта выходит за корень projects"
            ) from error

        return project_path

    def _get_processor(self):
        if self.processor is None:
            from app.services.project_processor import project_processor

            self.processor = project_processor

        return self.processor

    def _safe_filename(self, filename: str) -> str:
        value = (filename or "").strip().replace("\\", "/")
        safe_name = PurePosixPath(value).name

        if safe_name in {"", ".", ".."}:
            raise ValueError("Имя файла не указано")

        return safe_name

    def _validate_section(self, section_code: str) -> dict:
        section = self.SECTIONS.get(section_code)

        if section is None:
            allowed = ", ".join(self.SECTIONS)
            raise ValueError(
                "Раздел должен быть одним из: "
                f"{allowed}"
            )

        return section

    def _validate_extension(self, filename: str) -> str:
        extension = Path(filename).suffix.lower()

        if extension not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                "Неподдерживаемый формат файла: "
                f"{extension or 'без расширения'}"
            )

        return extension

    def _copy_upload(
        self,
        source: BinaryIO,
        target: BinaryIO,
    ) -> int:
        total_size = 0

        while True:
            chunk = source.read(self.COPY_CHUNK_SIZE)

            if not chunk:
                return total_size

            total_size += len(chunk)

            if total_size > self.max_file_size_bytes:
                raise ValueError(
                    "Файл превышает допустимый размер: "
                    f"{self.max_file_size_bytes} байт"
                )

            target.write(chunk)

    def _target_section(
        self,
        processing_result: dict,
        section_code: str,
    ) -> dict:
        supporting_documents = processing_result.get(
            "supporting_documents",
            {},
        )

        return next(
            (
                section
                for section in supporting_documents.get("sections", [])
                if section.get("code") == section_code
            ),
            {},
        )

    def _upload_verification(
        self,
        processing_result: dict,
        section_code: str,
        filename: str,
    ) -> dict:
        supporting_documents = processing_result.get(
            "supporting_documents",
            {},
        )
        requirements = {
            requirement.get("code"): requirement
            for requirement in supporting_documents.get(
                "requirements",
                [],
            )
            if requirement.get("code")
        }

        confirmed = []
        other_sections = []
        routing_conflicts = []

        for conflict in processing_result.get(
            "document_routing",
            {},
        ).get("conflicts", []):
            conflict_value = (
                conflict.get("filename", "")
                or conflict.get("destination", "")
                or ""
            ).replace("\\", "/")
            conflict_filename = (
                PurePosixPath(conflict_value).name
                if conflict_value
                else ""
            )

            if conflict_filename == filename:
                routing_conflicts.append(dict(conflict))

        for match in supporting_documents.get(
            "matching",
            {},
        ).get("matched", []):
            match_value = (
                match.get("filename", "")
                or ""
            ).replace("\\", "/")
            match_filename = (
                PurePosixPath(match_value).name
                if match_value
                else ""
            )

            if match_filename != filename:
                continue

            requirement = requirements.get(
                match.get("requirement_code"),
                {},
            )
            matched_section = (
                match.get("section_code")
                or requirement.get("section_code")
            )
            verified_match = {
                **match,
                "section_code": matched_section,
            }

            if matched_section == section_code:
                confirmed.append(verified_match)
            else:
                other_sections.append(verified_match)

        if routing_conflicts:
            status = "Конфликт маршрутизации"
        elif confirmed:
            status = "Подтверждён"
        elif other_sections:
            status = "Раздел не совпадает"
        else:
            status = "Не подтверждён"

        return {
            "status": status,
            "target_section_code": section_code,
            "filename": filename,
            "matched_requirements": confirmed,
            "other_section_matches": other_sections,
            "routing_conflicts": routing_conflicts,
        }

    def upload(
        self,
        project_name: str,
        section_code: str,
        filename: str,
        source: BinaryIO,
    ) -> dict:
        project_path = self._project_path(project_name)

        if not project_path.is_dir():
            raise FileNotFoundError(
                f"Проект не найден: {project_name}"
            )

        section = self._validate_section(section_code)
        safe_name = self._safe_filename(filename)
        extension = self._validate_extension(safe_name)

        input_path = project_path / "input"
        input_path.mkdir(parents=True, exist_ok=True)

        destination = input_path / safe_name

        try:
            with destination.open("xb") as target:
                file_size = self._copy_upload(source, target)
        except FileExistsError as error:
            raise FileExistsError(
                f"Файл уже существует: {safe_name}"
            ) from error
        except Exception:
            destination.unlink(missing_ok=True)
            raise

        if file_size == 0:
            destination.unlink()
            raise ValueError("Пустой файл не может быть загружен")

        try:
            processing_result = self._get_processor().process(project_name)
        except Exception as error:
            return {
                "status": "Файл загружен",
                "project": project_name,
                "filename": safe_name,
                "extension": extension,
                "size_bytes": file_size,
                "saved_to": str(destination),
                "target_section": {
                    "code": section_code,
                    **section,
                },
                "automatic_processing": {
                    "status": "Ошибка анализа",
                    "error": str(error),
                    "result": None,
                },
                "upload_verification": {
                    "status": "Не выполнена",
                    "target_section_code": section_code,
                    "filename": safe_name,
                    "matched_requirements": [],
                    "other_section_matches": [],
                    "routing_conflicts": [],
                },
            }

        upload_verification = self._upload_verification(
            processing_result,
            section_code,
            safe_name,
        )
        has_routing_conflict = (
            upload_verification["status"]
            == "Конфликт маршрутизации"
        )
        response_status = (
            "Файл загружен, но обнаружен конфликт маршрутизации"
            if has_routing_conflict
            else "Файл загружен и проект повторно проанализирован"
        )

        return {
            "status": response_status,
            "project": project_name,
            "filename": safe_name,
            "extension": extension,
            "size_bytes": file_size,
            "saved_to": str(destination),
            "target_section": {
                "code": section_code,
                **section,
            },
            "automatic_processing": {
                "status": "Готово",
                "error": None,
                "result": processing_result,
            },
            "section_analysis": self._target_section(
                processing_result,
                section_code,
            ),
            "upload_verification": upload_verification,
        }


supporting_document_upload = SupportingDocumentUpload()
