import pytest

from app.models.knowledge import KnowledgeChunk, KnowledgeSearchResult
from app.services.knowledge_context import build_knowledge_context


def test_build_knowledge_context_binds_text_to_source():
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must be installed according to design.",
    )
    result = KnowledgeSearchResult(
        chunk=chunk,
        matched_terms=["grounding", "design"],
    )

    context = build_knowledge_context([result])

    assert context == (
        "[SOURCE 1]\n"
        "source_id: sp-grounding\n"
        "source_title: Grounding standard\n"
        "section: section-1\n"
        "page: 10\n"
        "matched_terms: grounding, design\n"
        "text:\n"
        "Grounding conductors must be installed according to design.\n"
        "[/SOURCE]"
    )


def test_build_knowledge_context_returns_empty_string_without_results():
    assert build_knowledge_context([]) == ""


def test_build_knowledge_context_marks_missing_source_location():
    chunk = KnowledgeChunk(
        source_id="sp-general",
        source_title="General standard",
        text="General engineering requirement.",
    )
    result = KnowledgeSearchResult(
        chunk=chunk,
        matched_terms=["engineering"],
    )

    context = build_knowledge_context([result])

    assert "section: not specified" in context
    assert "page: not specified" in context


def test_build_knowledge_context_limits_complete_source_blocks():
    first = KnowledgeSearchResult(
        chunk=KnowledgeChunk(
            source_id="sp-grounding",
            source_title="Grounding standard",
            page=10,
            text="Grounding requirement.",
        ),
        matched_terms=["requirement"],
    )
    second = KnowledgeSearchResult(
        chunk=KnowledgeChunk(
            source_id="sp-concrete",
            source_title="Concrete standard",
            page=20,
            text="Concrete requirement.",
        ),
        matched_terms=["requirement"],
    )
    first_context = build_knowledge_context([first])

    context = build_knowledge_context(
        [first, second],
        max_chars=len(first_context),
    )

    assert context == first_context
    assert "sp-concrete" not in context


@pytest.mark.parametrize("max_chars", [0, -1])
def test_build_knowledge_context_rejects_nonpositive_limit(max_chars):
    with pytest.raises(ValueError, match="max_chars must be positive"):
        build_knowledge_context([], max_chars=max_chars)


def test_build_knowledge_context_does_not_split_oversized_first_block():
    result = KnowledgeSearchResult(
        chunk=KnowledgeChunk(
            source_id="sp-grounding",
            source_title="Grounding standard",
            text="Grounding requirement.",
        ),
        matched_terms=["grounding"],
    )

    context = build_knowledge_context([result], max_chars=1)

    assert context == ""
