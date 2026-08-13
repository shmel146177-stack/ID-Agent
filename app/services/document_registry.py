import json
import os


class DocumentRegistry:

    def build(self, project_name: str):

        project_path = os.path.join(
            "projects",
            project_name
        )

        analysis_path = os.path.join(
            project_path,
            "analysis"
        )

        project_analysis_path = os.path.join(
            analysis_path,
            "project_analysis.json"
        )

        if not os.path.exists(project_analysis_path):
            return {
                "project": project_name,
                "status": "project_analysis.json не найден",
                "documents": []
            }

        with open(
            project_analysis_path,
            "r",
            encoding="utf-8"
        ) as file:
            project_analysis = json.load(file)

        registry_documents = []

        for number, document in enumerate(
            project_analysis.get("documents", []),
            start=1
        ):

            analysis = document.get("analysis", {})

            registry_documents.append(
                {
                    "number": number,
                    "filename": document.get("filename", ""),
                    "classification": document.get(
                        "classification",
                        "Не определён"
                    ),
                    "status": document.get("status", ""),
                    "extension": document.get("extension", ""),
                    "drawing_number": analysis.get(
                        "drawing_number"
                    ),
                    "date": analysis.get("date"),
                    "manufacturer": analysis.get(
                        "manufacturer"
                    ),
                    "equipment": analysis.get(
                        "equipment"
                    )
                }
            )

        registry = {
            "project": project_name,
            "documents_count": len(registry_documents),
            "documents": registry_documents
        }

        registry_path = os.path.join(
            analysis_path,
            "document_registry.json"
        )

        with open(
            registry_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                registry,
                file,
                ensure_ascii=False,
                indent=4
            )

        return registry


document_registry = DocumentRegistry()