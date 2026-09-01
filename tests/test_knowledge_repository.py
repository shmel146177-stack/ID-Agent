from app.models.knowledge import KnowledgeChunk
from app.services.knowledge_repository import KnowledgeRepository


def test_knowledge_repository_saves_and_loads_chunks(tmp_path):
    path = tmp_path / "knowledge" / "chunks.json"
    repository = KnowledgeRepository(path)
    chunks = [
        KnowledgeChunk(
            source_id="sp-grounding",
            source_title="Grounding standard",
            section="section-1",
            page=10,
            text=(
                "Grounding conductors must be installed "
                "according to design."
            ),
        )
    ]

    repository.save(chunks)

    assert repository.load() == chunks

def test_knowledge_repository_loads_empty_list_when_file_is_missing(
    tmp_path,
):
    repository = KnowledgeRepository(
        tmp_path / "missing" / "knowledge.json"
    )

    assert repository.load() == []

def test_knowledge_repository_uses_default_project_path(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    repository = KnowledgeRepository()
    chunk = KnowledgeChunk(
        source_id="sp-grounding",
        source_title="Grounding standard",
        text="Grounding requirement.",
    )

    repository.save([chunk])

    expected_path = (
        tmp_path
        / "projects"
        / "data"
        / "knowledge_chunks.json"
    )
    assert expected_path.is_file()
    assert repository.load() == [chunk]
