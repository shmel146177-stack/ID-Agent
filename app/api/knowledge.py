from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.models.knowledge import KnowledgeChunk, KnowledgeSearchResult
from app.services.knowledge_repository import KnowledgeRepository
from app.services.knowledge_service import KnowledgeService

DEFAULT_KNOWLEDGE_SEARCH_RESULTS = 20


router = APIRouter(prefix="/knowledge", tags=["Knowledge"])
knowledge_repository = KnowledgeRepository()


@router.get(
    "/search",
    response_model=list[KnowledgeSearchResult],
)
def search_knowledge(
    query: Annotated[str, Query(min_length=1)],
    project_name: Annotated[str | None, Query(min_length=1)] = None,
    max_results: Annotated[int, Query(ge=1)] = DEFAULT_KNOWLEDGE_SEARCH_RESULTS,
):
    try:
        repository = (
            KnowledgeRepository.for_project(project_name)
            if project_name is not None
            else knowledge_repository
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    service = KnowledgeService.from_repository(repository)

    return service.search_results(
        query,
        max_results=max_results,
    )


@router.get(
    "/review/pending",
    response_model=list[KnowledgeChunk],
)
def list_pending_knowledge_reviews(
    project_name: Annotated[str, Query(min_length=1)],
):
    try:
        repository = KnowledgeRepository.for_project(
            project_name
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    service = KnowledgeService.from_repository(repository)

    return [
        chunk
        for chunk in service.chunks
        if (
            chunk.text_origin == "ocr"
            and chunk.requires_human_review
        )
    ]
