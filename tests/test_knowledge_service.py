from app.models.knowledge import KnowledgeChunk
from app.services.knowledge_service import KnowledgeService


def test_knowledge_service_finds_chunk_by_text():
    grounding = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must be installed according to design.",
    )
    concrete = KnowledgeChunk(
        source_id="sp-concrete",
        source_title="Concrete standard",
        section="section-2",
        page=20,
        text="Concrete works require quality control.",
    )

    service = KnowledgeService([grounding, concrete])

    result = service.search("grounding")

    assert result == [grounding]


def test_knowledge_service_adds_chunk():
    service = KnowledgeService()

    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must be installed according to design.",
    )

    service.add(chunk)

    assert service.search("grounding") == [chunk]


def test_knowledge_service_matches_separate_query_terms():
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must be installed according to design.",
    )

    service = KnowledgeService([chunk])

    assert service.search("grounding design") == [chunk]


def test_knowledge_service_searches_source_metadata():
    chunk = KnowledgeChunk(
        source_id="sp-48-13330",
        source_title="Construction standard 48",
        section="acceptance-section",
        page=42,
        text="Works must be inspected before acceptance.",
    )

    service = KnowledgeService([chunk])

    assert service.search("construction standard") == [chunk]


def test_knowledge_service_ignores_query_punctuation():
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must be installed according to design.",
    )

    service = KnowledgeService([chunk])

    assert service.search("grounding design?") == [chunk]


def test_knowledge_service_does_not_match_partial_words():
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must be installed according to design.",
    )

    service = KnowledgeService([chunk])

    assert service.search("sign") == []
