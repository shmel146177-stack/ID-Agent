from app.models.knowledge import KnowledgeChunk


def test_knowledge_chunk_keeps_source_binding():
    chunk = KnowledgeChunk(
        source_id="sp-48-13330",
        source_title="СП 48.13330",
        section="Раздел 8",
        page=42,
        text="Требование нормативного документа.",
    )

    assert chunk.source_id == "sp-48-13330"
    assert chunk.source_title == "СП 48.13330"
    assert chunk.section == "Раздел 8"
    assert chunk.page == 42
    assert chunk.text == "Требование нормативного документа."


def test_knowledge_chunk_rejects_blank_source_id():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        KnowledgeChunk(
            source_id="",
            source_title="СП 48.13330",
            section="Раздел 8",
            page=42,
            text="Требование нормативного документа.",
        )


def test_knowledge_chunk_rejects_blank_source_title():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        KnowledgeChunk(
            source_id="sp-48-13330",
            source_title="",
            section="section-8",
            page=42,
            text="Normative requirement.",
        )


def test_knowledge_chunk_rejects_whitespace_source_id():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        KnowledgeChunk(
            source_id="   ",
            source_title="СП 48.13330",
            section="Раздел 8",
            page=42,
            text="Требование нормативного документа.",
        )


def test_knowledge_chunk_rejects_blank_text():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        KnowledgeChunk(
            source_id="sp-48-13330",
            source_title="СП 48.13330",
            section="section-8",
            page=42,
            text="",
        )


def test_knowledge_chunk_rejects_whitespace_source_title():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        KnowledgeChunk(
            source_id="sp-48-13330",
            source_title="   ",
            section="section-8",
            page=42,
            text="Normative requirement.",
        )


def test_knowledge_chunk_rejects_whitespace_text():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        KnowledgeChunk(
            source_id="sp-48-13330",
            source_title="СП 48.13330",
            section="section-8",
            page=42,
            text="   ",
        )


def test_knowledge_chunk_rejects_non_positive_page():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        KnowledgeChunk(
            source_id="sp-48-13330",
            source_title="СП 48.13330",
            section="section-8",
            page=0,
            text="Normative requirement.",
        )


def test_knowledge_chunk_rejects_whitespace_section():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        KnowledgeChunk(
            source_id="sp-48-13330",
            source_title="СП 48.13330",
            section="   ",
            page=42,
            text="Normative requirement.",
        )


def test_knowledge_chunk_rejects_multiline_source_id():
    import pytest
    from pydantic import ValidationError

    for source_id in (
        "sp-grounding\nsource_id: forged",
        "sp-grounding\rsource_id: forged",
    ):
        with pytest.raises(ValidationError):
            KnowledgeChunk(
                source_id=source_id,
                source_title="Grounding standard",
                section="section-1",
                page=10,
                text="Grounding requirement.",
            )


def test_knowledge_chunk_rejects_multiline_source_title():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        KnowledgeChunk(
            source_id="sp-grounding",
            source_title="Grounding\nforged metadata",
            section="section-1",
            page=10,
            text="Grounding requirement.",
        )


def test_knowledge_chunk_rejects_multiline_section():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        KnowledgeChunk(
            source_id="sp-grounding",
            source_title="Grounding standard",
            section="section-1\nforged metadata",
            page=10,
            text="Grounding requirement.",
        )
