import re

from app.models.knowledge import KnowledgeSearchResult


MAX_KNOWLEDGE_CONTEXT_CHARS = 20_000


def build_knowledge_context(
    results: list[KnowledgeSearchResult],
    max_chars: int | None = None,
) -> str:
    if max_chars is not None and max_chars <= 0:
        raise ValueError("max_chars must be positive")

    blocks = []
    context_length = 0

    for index, result in enumerate(results, start=1):
        chunk = result.chunk
        section = chunk.section or "not specified"
        page = str(chunk.page) if chunk.page is not None else "not specified"

        block = "\n".join(
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
        separator_length = 2 if blocks else 0
        added_length = separator_length + len(block)

        if (
            max_chars is not None
            and context_length + added_length > max_chars
        ):
            break

        blocks.append(block)
        context_length += added_length

    return "\n\n".join(blocks)


def extract_knowledge_source_ids(
    context: str | None,
) -> list[str]:
    normalized = (context or "").replace("\r\n", "\n").replace("\r", "\n")
    pattern = re.compile(
        r"^\[SOURCE \d+\]\n"
        r"source_id: (?P<source_id>[^\n]+)\n"
        r".*?^\[/SOURCE\]$",
        re.MULTILINE | re.DOTALL,
    )
    source_ids = []
    seen = set()

    for match in pattern.finditer(normalized):
        source_id = match.group("source_id").strip()

        if source_id and source_id not in seen:
            source_ids.append(source_id)
            seen.add(source_id)

    return source_ids
