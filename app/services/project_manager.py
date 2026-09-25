from app.services.safe_paths import safe_project_path, safe_child_path
import json
import logging
import os

from app.models.project_card import ProjectCard
from app.services.atomic_json import write_json_atomically
from app.services.interprocess_lock import exclusive_file_lock
from app.services.project_service import ProjectStateCorruptionError


logger = logging.getLogger(__name__)


class ProjectManager:

    def __init__(self):

        self.projects_root = "projects"

        os.makedirs(
            self.projects_root,
            exist_ok=True
        )

    def _project_path(
        self,
        project_name: str
    ) -> str:

        return str(safe_project_path(project_name, self.projects_root))

    def _project_file(
        self,
        project_name: str
    ) -> str:

        return str(safe_child_path(
            self._project_path(
                project_name
            ),
            "project.json"
        ))

    def _create_folders(
        self,
        project_name: str
    ):

        project_path = self._project_path(
            project_name
        )

        folders = [
            project_path,
            os.path.join(
                project_path,
                "input"
            ),
            os.path.join(
                project_path,
                "analysis"
            ),
            os.path.join(
                project_path,
                "output"
            ),
            os.path.join(
                project_path,
                "executive_docs"
            )
        ]

        for folder in folders:
            safe_child_path(project_path, os.path.relpath(folder, project_path))

        for folder in folders:
            os.makedirs(
                folder,
                exist_ok=True
            )

    def create_project(self, project_name: str):

        if not project_name:
            raise ValueError("Имя проекта не указано")

        project_file = self._project_file(project_name)

        # Создаём полную структуру проекта
        self._create_folders(project_name)

        lock_file = str(
            safe_child_path(self._project_path(project_name), "project.json.lock")
        )
        with exclusive_file_lock(lock_file):
            # Recheck under the lock so concurrent creation cannot reset a card.
            if os.path.exists(project_file):

                return self.get_project(project_name)

            card = ProjectCard(project_name=project_name)

            data = {
                "project_name": card.project_name,
                "project_mode": card.project_mode,
                "project_note": card.project_note,
                "object_name": card.object_name,
                "address": card.address,
                "customer": card.customer,
                "contractor": card.contractor,
                "designer": card.designer,
                "contract_number": card.contract_number,
                "start_date": card.start_date,
                "finish_date": card.finish_date,
                "chief_engineer": card.chief_engineer,
            }

            write_json_atomically(project_file, data)

            return data

    def get_project(self, project_name: str):

        project_file = self._project_file(project_name)

        if not os.path.exists(project_file):
            raise FileNotFoundError(f"Проект не найден: {project_name}")

        state_name = f"project card: {project_name}"
        try:
            with open(project_file, "r", encoding="utf-8") as file:
                project = json.load(file)
        except json.JSONDecodeError as error:
            raise ProjectStateCorruptionError(
                state_name,
                f"invalid JSON at line {error.lineno}, column {error.colno}",
            ) from error
        except UnicodeDecodeError as error:
            raise ProjectStateCorruptionError(
                state_name, "invalid UTF-8 encoding"
            ) from error

        if not isinstance(project, dict):
            raise ProjectStateCorruptionError(
                state_name, "top-level JSON value must be an object"
            )

        return project

    def update_project(self, project_name: str, data: dict):

        project_file = self._project_file(project_name)

        if not os.path.exists(project_file):
            raise FileNotFoundError(f"Проект не найден: {project_name}")

        lock_file = str(
            safe_child_path(self._project_path(project_name), "project.json.lock")
        )
        with exclusive_file_lock(lock_file):
            project = self.get_project(project_name)

            allowed_fields = [
                "project_mode",
                "project_note",
                "object_name",
                "address",
                "customer",
                "contractor",
                "designer",
                "contract_number",
                "start_date",
                "finish_date",
                "chief_engineer",
            ]

            for field in allowed_fields:

                if field in data:

                    if field == "project_mode" and data[field] not in {
                        "production",
                        "training",
                    }:
                        raise ValueError(
                            "Режим проекта должен быть production или training"
                        )

                    project[field] = data[field]

            # Preserve the identity and all fields absent from this update.
            project["project_name"] = project_name

            write_json_atomically(project_file, project)

            return project

    def list_projects(self):

        if not os.path.exists(
            self.projects_root
        ):

            return []

        projects = []

        for name in sorted(
            os.listdir(
                self.projects_root
            )
        ):

            try:
                project_path = self._project_path(name)
            except ValueError:
                continue

            if not os.path.isdir(
                project_path
            ):
                continue

            try:
                project = self.get_project(name)
            except FileNotFoundError:
                # Folders without a card are not registered projects.
                continue
            except (ProjectStateCorruptionError, OSError, ValueError) as error:
                logger.warning("Skipping unreadable project card %r: %s", name, error)
                continue

            input_path = os.path.join(
                project_path,
                "input"
            )

            output_path = os.path.join(
                project_path,
                "output"
            )

            executive_docs_path = os.path.join(
                project_path,
                "executive_docs"
            )

            input_files = 0
            output_files = 0
            executive_files = 0

            if os.path.exists(
                input_path
            ):
                input_files = len(
                    [
                        item
                        for item in os.listdir(
                            input_path
                        )
                        if os.path.isfile(
                            os.path.join(
                                input_path,
                                item
                            )
                        )
                    ]
                )

            if os.path.exists(
                output_path
            ):
                output_files = len(
                    [
                        item
                        for item in os.listdir(
                            output_path
                        )
                        if os.path.isfile(
                            os.path.join(
                                output_path,
                                item
                            )
                        )
                    ]
                )

            if os.path.exists(
                executive_docs_path
            ):
                executive_files = len(
                    [
                        item
                        for item in os.listdir(
                            executive_docs_path
                        )
                        if os.path.isfile(
                            os.path.join(
                                executive_docs_path,
                                item
                            )
                        )
                    ]
                )

            projects.append(
                {
                    "project_name": (
                        project.get(
                            "project_name"
                        )
                        or name
                    ),
                    "object_name": (
                        project.get(
                            "object_name"
                        )
                        or ""
                    ),
                    "project_mode": (
                        project.get(
                            "project_mode"
                        )
                        or "production"
                    ),
                    "project_note": (
                        project.get(
                            "project_note"
                        )
                        or ""
                    ),
                    "address": (
                        project.get(
                            "address"
                        )
                        or ""
                    ),
                    "customer": (
                        project.get(
                            "customer"
                        )
                        or ""
                    ),
                    "contractor": (
                        project.get(
                            "contractor"
                        )
                        or ""
                    ),
                    "input_files": (
                        input_files
                    ),
                    "output_files": (
                        output_files
                    ),
                    "executive_files": (
                        executive_files
                    )
                }
            )

        return projects


project_manager = ProjectManager()
