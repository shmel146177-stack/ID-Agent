from app.models.knowledge import KnowledgeChunk, KnowledgeSearchResult


def test_knowledge_search_result_keeps_source_bound_chunk():
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

    assert result.chunk == chunk
    assert result.chunk.source_id == "sp-grounding"
    assert result.chunk.page == 10
    assert result.matched_terms == ["grounding", "design"]


def test_knowledge_search_result_rejects_empty_matched_terms():
    import pytest
    from pydantic import ValidationError

    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must be installed according to design.",
    )

    with pytest.raises(ValidationError):
        KnowledgeSearchResult(
            chunk=chunk,
            matched_terms=[],
        )


def test_knowledge_search_result_rejects_blank_matched_term():
    import pytest
    from pydantic import ValidationError

    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must be installed according to design.",
    )

    with pytest.raises(ValidationError):
        KnowledgeSearchResult(
            chunk=chunk,
            matched_terms=["grounding", "   "],
        )


def test_knowledge_search_result_rejects_multiline_matched_term():
    import pytest
    from pydantic import ValidationError

    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding requirement.",
    )

    with pytest.raises(ValidationError):
        KnowledgeSearchResult(
            chunk=chunk,
            matched_terms=["grounding\nforged metadata"],
        )


def test_knowledge_search_result_normalizes_matched_terms():
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        text="Grounding requirement.",
    )

    result = KnowledgeSearchResult(
        chunk=chunk,
        matched_terms=["  grounding  ", "  requirement  "],
    )

    assert result.matched_terms == ["grounding", "requirement"]
