import json
from pathlib import Path

from app.models.knowledge import KnowledgeChunk


class KnowledgeRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

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
