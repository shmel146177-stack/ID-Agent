import re
from typing import Self

from app.models.knowledge import KnowledgeChunk, KnowledgeSearchResult
from app.services.knowledge_context import build_knowledge_context
from app.services.knowledge_repository import KnowledgeRepository


class KnowledgeService:
    def __init__(
        self,
        chunks: list[KnowledgeChunk] | None = None,
        repository: KnowledgeRepository | None = None,
    ):
        self.chunks = list(chunks or [])
        self.repository = repository

    @classmethod
    def from_repository(
        cls,
        repository: KnowledgeRepository,
    ) -> Self:
        return cls(repository.load(), repository=repository)

    def add(self, chunk: KnowledgeChunk) -> None:
        self.chunks.append(chunk)

        if self.repository is not None:
            self.repository.save(self.chunks)

    def search_results(
        self,
        query: str,
        max_results: int | None = None,
    ) -> list[KnowledgeSearchResult]:
        if max_results is not None and max_results <= 0:
            raise ValueError("max_results must be positive")

        terms = list(dict.fromkeys(re.findall(r"\w+", (query or "").casefold())))

        if not terms:
            return []

        results = []

        for chunk in self.chunks:
            searchable_text = " ".join(
                part
                for part in (
                    chunk.source_id,
                    chunk.source_title,
                    chunk.section,
                    chunk.text,
                )
                if part is not None
            ).casefold()

            searchable_terms = set(re.findall(r"\w+", searchable_text))

            if all(term in searchable_terms for term in terms):
                results.append(
                    KnowledgeSearchResult(
                        chunk=chunk,
                        matched_terms=terms,
                    )
                )

        if max_results is not None:
            return results[:max_results]

        return results

    def search(
        self,
        query: str,
        max_results: int | None = None,
    ) -> list[KnowledgeChunk]:
        if max_results is None:
            results = self.search_results(query)
        else:
            results = self.search_results(
                query,
                max_results=max_results,
            )

        return [result.chunk for result in results]

    def build_context(
        self,
        query: str,
        max_results: int | None = None,
        max_chars: int | None = None,
    ) -> str:
        results = self.search_results(
            query,
            max_results=max_results,
        )

        return build_knowledge_context(
            results,
            max_chars=max_chars,
        )
