import re

from app.models.knowledge import KnowledgeChunk, KnowledgeSearchResult


class KnowledgeService:
    def __init__(self, chunks: list[KnowledgeChunk] | None = None):
        self.chunks = list(chunks or [])

    def add(self, chunk: KnowledgeChunk) -> None:
        self.chunks.append(chunk)

    def search_results(self, query: str) -> list[KnowledgeSearchResult]:
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

        return results

    def search(self, query: str) -> list[KnowledgeChunk]:
        return [result.chunk for result in self.search_results(query)]
