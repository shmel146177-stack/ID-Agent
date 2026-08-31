import json
import os
from uuid import uuid4


class ProjectService:

    def __init__(self):
        self.file_path = "projects/data/current_analysis.json"
        self.ai_file_path = "projects/data/current_ai_analysis.json"
        self.ai_review_file_path = "projects/data/current_ai_review.json"
        self.ai_comparison_file_path = (
            "projects/data/current_ai_comparison.json"
        )

    def save_analysis(self, data: dict):

        os.makedirs(
            "projects/data",
            exist_ok=True
        )

        with open(
            self.file_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

        if os.path.exists(self.ai_file_path):
            os.remove(self.ai_file_path)

        if os.path.exists(self.ai_review_file_path):
            os.remove(self.ai_review_file_path)

        if os.path.exists(self.ai_comparison_file_path):
            os.remove(self.ai_comparison_file_path)

        return {
            "status": "Анализ сохранён",
            "document": data
        }

    def save_ai_analysis(
        self,
        data: dict,
        source_filename: str | None = None,
        knowledge_source_ids: list[str] | None = None,
    ):
        directory = os.path.dirname(self.ai_file_path)

        if directory:
            os.makedirs(
                directory,
                exist_ok=True,
            )

        data_to_save = dict(data)
        data_to_save["analysis_id"] = str(uuid4())

        if source_filename is not None:
            data_to_save["source_filename"] = source_filename

        if knowledge_source_ids is not None:
            data_to_save["knowledge_source_ids"] = list(
                knowledge_source_ids
            )

        with open(
            self.ai_file_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data_to_save,
                file,
                ensure_ascii=False,
                indent=4,
            )

        if os.path.exists(self.ai_review_file_path):
            os.remove(self.ai_review_file_path)

        if os.path.exists(self.ai_comparison_file_path):
            os.remove(self.ai_comparison_file_path)

        return {
            "status": "AI-анализ сохранен",
            "document": data_to_save,
        }

    def save_ai_comparison(
        self,
        data: dict,
        analysis_id: str,
        source_filename: str,
    ):
        directory = os.path.dirname(
            self.ai_comparison_file_path
        )

        if directory:
            os.makedirs(
                directory,
                exist_ok=True,
            )

        data_to_save = dict(data)
        data_to_save["analysis_id"] = analysis_id
        data_to_save["source_filename"] = source_filename

        with open(
            self.ai_comparison_file_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data_to_save,
                file,
                ensure_ascii=False,
                indent=4,
            )

        return {
            "status": "AI comparison saved",
            "document": data_to_save,
        }

    def get_ai_comparison(self):

        if not os.path.exists(
            self.ai_comparison_file_path
        ):
            return None

        with open(
            self.ai_comparison_file_path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def save_ai_review(self, data: dict):
        directory = os.path.dirname(self.ai_review_file_path)

        if directory:
            os.makedirs(
                directory,
                exist_ok=True,
            )

        with open(
            self.ai_review_file_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4,
            )

        return {
            "status": "AI-review saved",
            "document": data,
        }

    def get_ai_review(self):

        if not os.path.exists(self.ai_review_file_path):
            return None

        with open(
            self.ai_review_file_path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def get_ai_analysis(self):

        if not os.path.exists(self.ai_file_path):
            return None

        with open(
            self.ai_file_path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)


    def get_analysis(self):

        if not os.path.exists(self.file_path):
            return None

        with open(
            self.file_path,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)


project_service = ProjectService()
