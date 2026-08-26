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

        return {
            "status": "?????? ????????",
            "document": data
        }

    def save_ai_analysis(self, data: dict):
        directory = os.path.dirname(self.ai_file_path)

        if directory:
            os.makedirs(
                directory,
                exist_ok=True,
            )

        with open(
            self.ai_file_path,
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
            "status": "AI-?????? ????????",
            "document": data,
        }

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
