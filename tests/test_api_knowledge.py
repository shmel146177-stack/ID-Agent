import pytest

from fastapi.testclient import TestClient

from app.models.knowledge import KnowledgeChunk
from app.services.knowledge_repository import KnowledgeRepository
from main import app


client = TestClient(app)


def test_knowledge_search_reads_default_repository(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        section="section-1",
        page=10,
        text="Grounding conductors must follow the design.",
    )
    KnowledgeRepository().save([chunk])

    response = client.get(
        "/knowledge/search",
        params={"query": "grounding"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "chunk": chunk.model_dump(mode="json"),
            "matched_terms": ["grounding"],
        }
    ]

def test_knowledge_search_limits_default_results(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    chunks = [
        KnowledgeChunk(
            source_id=f"sp-{index}",
            source_title=f"Standard {index}",
            text="Shared engineering requirement.",
        )
        for index in range(21)
    ]
    KnowledgeRepository().save(chunks)

    response = client.get(
        "/knowledge/search",
        params={"query": "engineering"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 20

def test_knowledge_search_reads_project_repository(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    chunk = KnowledgeChunk(
        source_id="project-drawing",
        source_title="Project working documentation",
        page=1,
        text="Grounding requirement for this project.",
    )
    repository = KnowledgeRepository.for_project(
        "project-a"
    )
    repository.save([chunk])

    response = client.get(
        "/knowledge/search",
        params={
            "query": "grounding",
            "project_name": "project-a",
        },
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "chunk": chunk.model_dump(mode="json"),
            "matched_terms": ["grounding"],
        }
    ]

def test_knowledge_search_rejects_invalid_project_name():
    response = client.get(
        "/knowledge/search",
        params={
            "query": "grounding",
            "project_name": "../outside",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith(
        "project_name must"
    )


def test_knowledge_review_lists_pending_project_pages(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    native = KnowledgeChunk(
        source_id="project-drawing",
        source_title="Project working documentation",
        page=1,
        text="Native page text.",
    )
    pending = KnowledgeChunk(
        source_id="project-drawing",
        source_title="Project working documentation",
        page=2,
        text="OCR page awaiting review.",
        text_origin="ocr",
        requires_human_review=True,
    )
    reviewed = KnowledgeChunk(
        source_id="project-drawing",
        source_title="Project working documentation",
        page=3,
        text="Reviewed OCR page.",
        text_origin="ocr",
        requires_human_review=False,
    )
    repository = KnowledgeRepository.for_project(
        "project-a"
    )
    repository.save([native, pending, reviewed])

    response = client.get(
        "/knowledge/review/pending",
        params={"project_name": "project-a"},
    )

    assert response.status_code == 200
    assert response.json() == [
        pending.model_dump(mode="json")
    ]


def test_knowledge_review_corrects_ocr_page(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    pending = KnowledgeChunk(
        source_id="project-drawing",
        source_title="Project working documentation",
        page=2,
        text="Incorrect OCR page text.",
        text_origin="ocr",
        requires_human_review=True,
    )
    repository = KnowledgeRepository.for_project(
        "project-a"
    )
    repository.save([pending])

    response = client.patch(
        "/knowledge/review",
        params={"project_name": "project-a"},
        json={
            "source_id": "project-drawing",
            "page": 2,
            "text": "Corrected OCR page text.",
            "reviewed_by": "Test engineer",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["text"] == "Corrected OCR page text."
    assert result["text_origin"] == "ocr"
    assert result["requires_human_review"] is False
    assert result["reviewed_by"] == "Test engineer"
    assert result["reviewed_at"] is not None

    saved = repository.load()

    assert len(saved) == 1
    assert saved[0].text == "Corrected OCR page text."
    assert saved[0].requires_human_review is False
    assert saved[0].reviewed_by == "Test engineer"
    assert saved[0].reviewed_at is not None


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("source_id", "   "),
        ("text", "   "),
        ("reviewed_by", "   "),
    ],
)
def test_knowledge_review_rejects_blank_fields(
    tmp_path,
    monkeypatch,
    field_name,
    field_value,
):
    monkeypatch.chdir(tmp_path)
    pending = KnowledgeChunk(
        source_id="project-drawing",
        source_title="Project working documentation",
        page=2,
        text="Incorrect OCR page text.",
        text_origin="ocr",
        requires_human_review=True,
    )
    repository = KnowledgeRepository.for_project(
        "project-a"
    )
    repository.save([pending])
    request_data = {
        "source_id": "project-drawing",
        "page": 2,
        "text": "Corrected OCR page text.",
        "reviewed_by": "Test engineer",
    }
    request_data[field_name] = field_value

    response = client.patch(
        "/knowledge/review",
        params={"project_name": "project-a"},
        json=request_data,
    )

    assert response.status_code == 422
    assert repository.load() == [pending]
