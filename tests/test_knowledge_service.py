import pytest

from app.models.knowledge import KnowledgeChunk, KnowledgeSearchResult
from app.services.knowledge_repository import KnowledgeRepository
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


def test_knowledge_service_returns_source_bound_search_results():
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must be installed according to design.",
    )

    service = KnowledgeService([chunk])

    results = service.search_results("grounding design")

    assert len(results) == 1
    assert results[0].chunk == chunk
    assert results[0].matched_terms == ["grounding", "design"]


def test_knowledge_service_search_uses_search_results(monkeypatch):
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must be installed according to design.",
    )
    result = KnowledgeSearchResult(
        chunk=chunk,
        matched_terms=["grounding"],
    )
    service = KnowledgeService()
    calls = []

    def fake_search_results(query):
        calls.append(query)
        return [result]

    monkeypatch.setattr(service, "search_results", fake_search_results)

    assert service.search("grounding") == [chunk]
    assert calls == ["grounding"]


def test_knowledge_service_deduplicates_query_terms():
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must be installed according to design.",
    )
    service = KnowledgeService([chunk])

    results = service.search_results("grounding grounding design")

    assert len(results) == 1
    assert results[0].matched_terms == ["grounding", "design"]


def test_knowledge_service_limits_search_results():
    first = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        text="Grounding requirements.",
    )
    second = KnowledgeChunk(
        source_id="sp-concrete",
        source_title="Concrete standard",
        text="Concrete requirements.",
    )
    service = KnowledgeService([first, second])

    results = service.search_results("standard", max_results=1)

    assert len(results) == 1
    assert results[0].chunk == first


@pytest.mark.parametrize("max_results", [0, -1])
def test_knowledge_service_rejects_nonpositive_max_results(max_results):
    service = KnowledgeService()

    with pytest.raises(ValueError, match="max_results must be positive"):
        service.search_results("standard", max_results=max_results)


def test_knowledge_service_search_limits_chunks():
    first = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        text="Grounding requirements.",
    )
    second = KnowledgeChunk(
        source_id="sp-concrete",
        source_title="Concrete standard",
        text="Concrete requirements.",
    )
    service = KnowledgeService([first, second])

    chunks = service.search("standard", max_results=1)

    assert chunks == [first]


def test_knowledge_service_builds_limited_source_context():
    first = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        text="Shared engineering requirement.",
    )
    second = KnowledgeChunk(
        source_id="sp-concrete",
        source_title="Concrete standard",
        text="Shared engineering requirement.",
    )
    service = KnowledgeService([first, second])

    context = service.build_context(
        "engineering",
        max_results=1,
    )

    assert "[SOURCE 1]" in context
    assert "source_id: sp-grounding" in context
    assert "sp-concrete" not in context


def test_knowledge_service_build_context_respects_character_limit():
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        text="Grounding requirement.",
    )
    service = KnowledgeService([chunk])

    context = service.build_context(
        "grounding",
        max_chars=1,
    )

    assert context == ""

def test_knowledge_service_loads_chunks_from_repository(tmp_path):
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must follow the design.",
    )
    repository = KnowledgeRepository(
        tmp_path / "knowledge" / "chunks.json"
    )
    repository.save([chunk])

    service = KnowledgeService.from_repository(repository)

    assert service.search("grounding") == [chunk]

def test_knowledge_service_persists_added_chunk_in_repository(
    tmp_path,
):
    repository = KnowledgeRepository(
        tmp_path / "knowledge" / "chunks.json"
    )
    service = KnowledgeService.from_repository(repository)
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must follow the design.",
    )

    service.add(chunk)

    assert repository.load() == [chunk]

def test_knowledge_service_does_not_persist_duplicate_chunk(
    tmp_path,
):
    repository = KnowledgeRepository(
        tmp_path / "knowledge" / "chunks.json"
    )
    service = KnowledgeService.from_repository(repository)
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must follow the design.",
    )

    service.add(chunk)
    service.add(chunk)

    assert service.chunks == [chunk]
    assert repository.load() == [chunk]


def test_knowledge_service_upserts_existing_source_page(
    tmp_path,
):
    repository = KnowledgeRepository(
        tmp_path / "knowledge" / "chunks.json"
    )
    original = KnowledgeChunk(
        source_id="drawing-11240-24-as",
        source_title="Working documentation",
        page=18,
        text="Old OCR text.",
        text_origin="ocr",
        requires_human_review=True,
    )
    repository.save([original])
    service = KnowledgeService.from_repository(repository)

    updated = KnowledgeChunk(
        source_id="drawing-11240-24-as",
        source_title="Working documentation",
        page=18,
        text="Updated OCR table text.",
        text_origin="ocr",
        requires_human_review=True,
    )

    service.upsert(updated)

    assert service.chunks == [updated]
    assert repository.load() == [updated]


def test_knowledge_service_build_context_excludes_unreviewed_ocr_by_default():
    native = KnowledgeChunk(
        source_id="native-source",
        source_title="Native source",
        page=1,
        text="Shared safety requirement from native text.",
    )
    reviewed_ocr = KnowledgeChunk(
        source_id="reviewed-ocr",
        source_title="Reviewed OCR",
        page=2,
        text_origin="ocr",
        requires_human_review=False,
        text="Shared safety requirement from reviewed OCR.",
    )
    pending_ocr = KnowledgeChunk(
        source_id="pending-ocr",
        source_title="Pending OCR",
        page=3,
        text_origin="ocr",
        requires_human_review=True,
        text="Shared safety requirement from pending OCR.",
    )
    service = KnowledgeService(
        [native, reviewed_ocr, pending_ocr]
    )

    context = service.build_context("safety")

    assert "source_id: native-source" in context
    assert "source_id: reviewed-ocr" in context
    assert "source_id: pending-ocr" not in context


def test_knowledge_service_build_context_can_include_unreviewed_ocr():
    pending_ocr = KnowledgeChunk(
        source_id="pending-ocr",
        source_title="Pending OCR",
        page=3,
        text_origin="ocr",
        requires_human_review=True,
        text="Shared safety requirement from pending OCR.",
    )
    service = KnowledgeService([pending_ocr])

    context = service.build_context(
        "safety",
        include_unreviewed_ocr=True,
    )

    assert "source_id: pending-ocr" in context
    assert "requires_human_review: true" in context


def test_knowledge_service_build_context_limits_after_ocr_filtering():
    pending_ocr = KnowledgeChunk(
        source_id="pending-ocr",
        source_title="Pending OCR",
        page=1,
        text_origin="ocr",
        requires_human_review=True,
        text="Shared safety requirement from pending OCR.",
    )
    native = KnowledgeChunk(
        source_id="native-source",
        source_title="Native source",
        page=2,
        text="Shared safety requirement from native text.",
    )
    service = KnowledgeService([pending_ocr, native])

    context = service.build_context(
        "safety",
        max_results=1,
    )

    assert "source_id: native-source" in context
    assert "source_id: pending-ocr" not in context
