import json
import shutil
from pathlib import Path

from app.generators.project_document_set import ProjectDocumentSet


class ExecutiveDocumentRouter:
    ROUTES = {
        "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430": "executive_schemes",
        "\u041f\u0430\u0441\u043f\u043e\u0440\u0442 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u044f": "quality_documents",
        "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442": "quality_documents",
        "\u0414\u0435\u043a\u043b\u0430\u0440\u0430\u0446\u0438\u044f": "quality_documents",
        "\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0446\u0438\u044f \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u044f": "quality_documents",
        "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b": "tests",
    }

    def _project_path(self, project_name: str) -> Path:
        return Path("projects") / project_name

    def _executive_root(self, project_name: str) -> Path:
        return (
            self._project_path(project_name)
            / "executive_docs"
            / "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f_\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0446\u0438\u044f"
        )

    def _load_project_analysis(self, project_name: str) -> dict:
        path = (
            self._project_path(project_name)
            / "analysis"
            / "project_analysis.json"
        )

        if not path.exists():
            raise FileNotFoundError(
                f"project_analysis.json not found: {path}"
            )

        return json.loads(
            path.read_text(encoding="utf-8")
        )

    def _section_folders(self) -> dict:
        return {
            section["code"]: section["folder"]
            for section in ProjectDocumentSet.SECTIONS
        }

    def _files_equal(
        self,
        source: Path,
        destination: Path,
    ) -> bool:
        if source.stat().st_size != destination.stat().st_size:
            return False

        with source.open("rb") as source_file:
            with destination.open("rb") as destination_file:
                while True:
                    source_chunk = source_file.read(1024 * 1024)
                    destination_chunk = destination_file.read(1024 * 1024)

                    if source_chunk != destination_chunk:
                        return False

                    if not source_chunk:
                        return True

    def _copy_without_overwrite(
        self,
        source: Path,
        destination: Path,
    ) -> str:
        """Copy a new route target without replacing an existing file."""

        if destination.exists():
            if self._files_equal(source, destination):
                return "already_routed"

            return "conflict"

        try:
            with source.open("rb") as source_file:
                with destination.open("xb") as destination_file:
                    shutil.copyfileobj(source_file, destination_file)

            shutil.copystat(source, destination)

        except FileExistsError:
            if self._files_equal(source, destination):
                return "already_routed"

            return "conflict"

        except Exception:
            destination.unlink(missing_ok=True)
            raise

        return "routed"

    def route(self, project_name: str) -> dict:
        project_analysis = self._load_project_analysis(project_name)
        section_folders = self._section_folders()

        routed = []
        already_routed = []
        conflicts = []
        skipped = []
        missing_source = []

        for document in project_analysis.get("documents", []):
            filename = document.get("filename", "")
            classification = document.get(
                "classification",
                "\u041d\u0435 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0451\u043d",
            )

            section_code = self.ROUTES.get(classification)

            if not section_code:
                skipped.append(
                    {
                        "filename": filename,
                        "classification": classification,
                        "reason": "no_route",
                    }
                )
                continue

            source_value = document.get("path")

            if not source_value:
                missing_source.append(
                    {
                        "filename": filename,
                        "classification": classification,
                        "reason": "path_missing",
                    }
                )
                continue

            source = Path(source_value)

            if not source.is_file():
                missing_source.append(
                    {
                        "filename": filename,
                        "classification": classification,
                        "path": str(source),
                        "reason": "source_not_found",
                    }
                )
                continue

            folder_name = section_folders.get(section_code)

            if not folder_name:
                skipped.append(
                    {
                        "filename": filename,
                        "classification": classification,
                        "reason": "section_not_found",
                    }
                )
                continue

            destination_folder = (
                self._executive_root(project_name)
                / folder_name
            )

            destination_folder.mkdir(
                parents=True,
                exist_ok=True,
            )

            destination = destination_folder / source.name

            copy_status = self._copy_without_overwrite(
                source,
                destination,
            )

            route_data = {
                "filename": filename,
                "classification": classification,
                "section": section_code,
                "destination": str(destination),
            }

            if copy_status == "already_routed":
                already_routed.append(
                    {
                        **route_data,
                        "reason": "already_routed_same_content",
                    }
                )
                continue

            if copy_status == "conflict":
                conflicts.append(
                    {
                        **route_data,
                        "source": str(source),
                        "reason": (
                            "destination_exists_different_content"
                        ),
                    }
                )
                continue

            routed.append(route_data)

        return {
            "project": project_name,
            "routed_count": len(routed),
            "already_routed_count": len(already_routed),
            "conflict_count": len(conflicts),
            "skipped_count": len(skipped),
            "missing_source_count": len(missing_source),
            "routed": routed,
            "already_routed": already_routed,
            "conflicts": conflicts,
            "skipped": skipped,
            "missing_source": missing_source,
        }


executive_document_router = ExecutiveDocumentRouter()
