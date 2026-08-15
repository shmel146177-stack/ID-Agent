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

    def route(self, project_name: str) -> dict:
        project_analysis = self._load_project_analysis(project_name)
        section_folders = self._section_folders()

        routed = []
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

            shutil.copy2(
                source,
                destination,
            )

            routed.append(
                {
                    "filename": filename,
                    "classification": classification,
                    "section": section_code,
                    "destination": str(destination),
                }
            )

        return {
            "project": project_name,
            "routed_count": len(routed),
            "skipped_count": len(skipped),
            "missing_source_count": len(missing_source),
            "routed": routed,
            "skipped": skipped,
            "missing_source": missing_source,
        }


executive_document_router = ExecutiveDocumentRouter()
