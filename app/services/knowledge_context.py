import re

from app.models.knowledge import KnowledgeSearchResult


MAX_KNOWLEDGE_CONTEXT_CHARS = 20_000


def _escape_source_markers(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    return re.sub(
        r"(?m)^(\[SOURCE \d+\]|\[/SOURCE\])$",
        r"\\\1",
        normalized,
    )


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
        safe_text = _escape_source_markers(chunk.text)

        block = "\n".join(
            (
                f"[SOURCE {index}]",
                f"source_id: {chunk.source_id}",
                f"source_title: {chunk.source_title}",
                f"section: {section}",
                f"page: {page}",
                f"text_origin: {chunk.text_origin}",
                (
                    "requires_human_review: "
                    f"{str(chunk.requires_human_review).lower()}"
                ),
                f"matched_terms: {', '.join(result.matched_terms)}",
                "text:",
                safe_text,
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
    normalized = (
        (context or "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .strip()
    )
    pattern = re.compile(
        r"^\[SOURCE (?P<source_number>\d+)\]\n"
        r"source_id: (?P<source_id>[^\n]+)\n"
        r".*?^\[/SOURCE\]$",
        re.MULTILINE | re.DOTALL,
    )
    matches = list(pattern.finditer(normalized))

    if not matches:
        return []

    source_ids = []
    seen = set()
    cursor = 0

    for match_index, match in enumerate(matches):
        expected_separator = "" if match_index == 0 else "\n\n"

        if normalized[cursor:match.start()] != expected_separator:
            return []

        source_number = int(match.group("source_number"))

        if source_number != match_index + 1:
            return []

        source_id = match.group("source_id").strip()

        if not source_id:
            return []

        if source_id not in seen:
            source_ids.append(source_id)
            seen.add(source_id)

        cursor = match.end()

    if cursor != len(normalized):
        return []

    return source_ids
