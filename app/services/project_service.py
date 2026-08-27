import json
import os


class ProjectService:

    def __init__(self):
        self.file_path = "projects/data/current_analysis.json"
        self.ai_file_path = "projects/data/current_ai_analysis.json"

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

        return {
            "status": "Анализ сохранён",
            "document": data
        }

    def save_ai_analysis(
        self,
        data: dict,
        source_filename: str | None = None,
    ):
        directory = os.path.dirname(self.ai_file_path)

        if directory:
            os.makedirs(
                directory,
                exist_ok=True,
            )

        data_to_save = dict(data)

        if source_filename is not None:
            data_to_save["source_filename"] = source_filename

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

        return {
            "status": "AI-анализ сохранен",
            "document": data_to_save,
        }

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
