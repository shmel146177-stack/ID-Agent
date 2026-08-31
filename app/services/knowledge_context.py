from app.models.knowledge import KnowledgeSearchResult


def build_knowledge_context(
    results: list[KnowledgeSearchResult],
) -> str:
    blocks = []

    for index, result in enumerate(results, start=1):
        chunk = result.chunk
        section = chunk.section or "not specified"
        page = str(chunk.page) if chunk.page is not None else "not specified"

        blocks.append(
            "\n".join(
                (
                    f"[SOURCE {index}]",
                    f"source_id: {chunk.source_id}",
                    f"source_title: {chunk.source_title}",
                    f"section: {section}",
                    f"page: {page}",
                    f"matched_terms: {', '.join(result.matched_terms)}",
                    "text:",
                    chunk.text,
                    "[/SOURCE]",
                )
            )
        )

    return "\n\n".join(blocks)
