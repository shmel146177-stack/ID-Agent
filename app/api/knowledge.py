from typing import Annotated

from fastapi import APIRouter, Query

from app.models.knowledge import KnowledgeSearchResult
from app.services.knowledge_repository import KnowledgeRepository
from app.services.knowledge_service import KnowledgeService


router = APIRouter(prefix="/knowledge", tags=["Knowledge"])
knowledge_repository = KnowledgeRepository()


@router.get(
    "/search",
    response_model=list[KnowledgeSearchResult],
)
def search_knowledge(
    query: Annotated[str, Query(min_length=1)],
    max_results: Annotated[int | None, Query(ge=1)] = None,
):
    service = KnowledgeService.from_repository(
        knowledge_repository
    )

    return service.search_results(
        query,
        max_results=max_results,
    )
