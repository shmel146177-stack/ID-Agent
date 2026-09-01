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
