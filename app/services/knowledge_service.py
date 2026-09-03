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
        if chunk in self.chunks:
            return

        self.chunks.append(chunk)

        if self.repository is not None:
            self.repository.save(self.chunks)

    def upsert(self, chunk: KnowledgeChunk) -> None:
        updated_chunks = []
        replaced = False

        for current_chunk in self.chunks:
            same_source_page = (
                current_chunk.source_id == chunk.source_id
                and current_chunk.page == chunk.page
            )

            if same_source_page:
                if not replaced:
                    updated_chunks.append(chunk)
                    replaced = True
                continue

            updated_chunks.append(current_chunk)

        if not replaced:
            updated_chunks.append(chunk)

        if updated_chunks == self.chunks:
            return

        self.chunks = updated_chunks

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

    def search_unreviewed_ocr_results(
        self,
        query: str,
    ) -> list[KnowledgeSearchResult]:
        return [
            result
            for result in self.search_results(query)
            if (
                result.chunk.text_origin == "ocr"
                and result.chunk.requires_human_review
            )
        ]

    def build_context(
        self,
        query: str,
        max_results: int | None = None,
        max_chars: int | None = None,
        include_unreviewed_ocr: bool = False,
    ) -> str:
        if max_results is not None and max_results <= 0:
            raise ValueError("max_results must be positive")

        results = self.search_results(query)

        if not include_unreviewed_ocr:
            results = [
                result
                for result in results
                if not (
                    result.chunk.text_origin == "ocr"
                    and result.chunk.requires_human_review
                )
            ]

        if max_results is not None:
            results = results[:max_results]

        return build_knowledge_context(
            results,
            max_chars=max_chars,
        )
