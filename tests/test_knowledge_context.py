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
