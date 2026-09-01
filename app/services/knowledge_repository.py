import json
from pathlib import Path
from typing import Self

from app.models.knowledge import KnowledgeChunk

DEFAULT_KNOWLEDGE_PATH = Path("projects/data/knowledge_chunks.json")


class KnowledgeRepository:
    def __init__(self, path: str | Path = DEFAULT_KNOWLEDGE_PATH):
        self.path = Path(path)

    @classmethod
    def for_project(
        cls,
        project_name: str,
        projects_root: str | Path = "projects",
    ) -> Self:
        root = Path(projects_root).resolve()
        project_path = (root / project_name).resolve()

        try:
            relative_path = project_path.relative_to(root)
        except ValueError as error:
            raise ValueError(
                "project_name must stay within projects_root"
            ) from error

        if len(relative_path.parts) != 1:
            raise ValueError(
                "project_name must identify one project"
            )

        return cls(
            project_path
            / "knowledge"
            / "knowledge_chunks.json"
        )
    def save(self, chunks: list[KnowledgeChunk]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        data = [
            chunk.model_dump(mode="json")
            for chunk in chunks
        ]

        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

    def load(self) -> list[KnowledgeChunk]:
        if not self.path.is_file():
            return []

        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return [
            KnowledgeChunk.model_validate(item)
            for item in data
        ]
