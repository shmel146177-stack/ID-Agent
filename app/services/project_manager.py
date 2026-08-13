import json
import os

from app.models.project_card import ProjectCard


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

        return os.path.join(
            self.projects_root,
            project_name
        )

    def _project_file(
        self,
        project_name: str
    ) -> str:

        return os.path.join(
            self._project_path(
                project_name
            ),
            "project.json"
        )

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

            os.makedirs(
                folder,
                exist_ok=True
            )

    def create_project(
        self,
        project_name: str
    ):

        project_name = (
            project_name.strip()
        )

        if not project_name:
            raise ValueError(
                "Имя проекта не указано"
            )

        project_path = self._project_path(
            project_name
        )

        project_file = self._project_file(
            project_name
        )

        # Создаём полную структуру проекта
        self._create_folders(
            project_name
        )

        # Если карточка уже существует,
        # не перезаписываем её
        if os.path.exists(
            project_file
        ):

            return self.get_project(
                project_name
            )

        card = ProjectCard(
            project_name=project_name
        )

        data = {
            "project_name": card.project_name,
            "object_name": card.object_name,
            "address": card.address,
            "customer": card.customer,
            "contractor": card.contractor,
            "designer": card.designer,
            "contract_number": card.contract_number,
            "start_date": card.start_date,
            "finish_date": card.finish_date,
            "chief_engineer": card.chief_engineer
        }

        with open(
            project_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

        return data

    def get_project(
        self,
        project_name: str
    ):

        project_file = self._project_file(
            project_name
        )

        if not os.path.exists(
            project_file
        ):
            raise FileNotFoundError(
                f"Проект не найден: {project_name}"
            )

        with open(
            project_file,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )

    def update_project(
        self,
        project_name: str,
        data: dict
    ):

        project_file = self._project_file(
            project_name
        )

        if not os.path.exists(
            project_file
        ):
            raise FileNotFoundError(
                f"Проект не найден: {project_name}"
            )

        project = self.get_project(
            project_name
        )

        allowed_fields = [
            "object_name",
            "address",
            "customer",
            "contractor",
            "designer",
            "contract_number",
            "start_date",
            "finish_date",
            "chief_engineer"
        ]

        for field in allowed_fields:

            if field in data:
                project[field] = (
                    data[field]
                )

        # Имя проекта всегда сохраняем
        project["project_name"] = (
            project_name
        )

        with open(
            project_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                project,
                file,
                ensure_ascii=False,
                indent=4
            )

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

            project_path = os.path.join(
                self.projects_root,
                name
            )

            if not os.path.isdir(
                project_path
            ):
                continue

            project_file = os.path.join(
                project_path,
                "project.json"
            )

            if not os.path.exists(
                project_file
            ):
                continue

            try:

                with open(
                    project_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    project = json.load(
                        file
                    )

            except (
                json.JSONDecodeError,
                OSError
            ):

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