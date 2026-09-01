import pytest

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

def test_knowledge_repository_uses_project_specific_path(
    tmp_path,
):
    projects_root = tmp_path / "projects"
    repository = KnowledgeRepository.for_project(
        "project-a",
        projects_root=projects_root,
    )
    chunk = KnowledgeChunk(
        source_id="drawing-11240-24-as",
        source_title="Working documentation",
        page=1,
        text="Project-specific engineering information.",
    )

    repository.save([chunk])

    expected_path = (
        projects_root
        / "project-a"
        / "knowledge"
        / "knowledge_chunks.json"
    )
    assert expected_path.is_file()
    assert repository.load() == [chunk]

@pytest.mark.parametrize(
    "project_name",
    [
        "",
        "../outside",
        "nested/project",
    ],
)
def test_knowledge_repository_rejects_invalid_project_name(
    tmp_path,
    project_name,
):
    with pytest.raises(
        ValueError,
        match="project_name must",
    ):
        KnowledgeRepository.for_project(
            project_name,
            projects_root=tmp_path / "projects",
        )
