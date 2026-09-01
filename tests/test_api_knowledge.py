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
