from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.knowledge import KnowledgeChunk, KnowledgeSearchResult
from app.services.knowledge_repository import KnowledgeRepository
from app.services.knowledge_service import KnowledgeService

DEFAULT_KNOWLEDGE_SEARCH_RESULTS = 20


router = APIRouter(prefix="/knowledge", tags=["Knowledge"])
knowledge_repository = KnowledgeRepository()


class KnowledgeReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1, max_length=255)
    page: int = Field(ge=1)
    text: str = Field(min_length=1)
    reviewed_by: str = Field(min_length=1, max_length=255)

    @field_validator("source_id", "reviewed_by")
    @classmethod
    def validate_single_line(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError("value must not be blank")

        if "\n" in value or "\r" in value:
            raise ValueError("value must be single-line")

        return normalized

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be blank")

        return value


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


@router.patch(
    "/review",
    response_model=KnowledgeChunk,
)
def review_knowledge_page(
    request: KnowledgeReviewRequest,
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

    chunk = next(
        (
            current_chunk
            for current_chunk in service.chunks
            if (
                current_chunk.source_id
                == request.source_id
                and current_chunk.page == request.page
            )
        ),
        None,
    )

    if chunk is None:
        raise HTTPException(
            status_code=404,
            detail="Knowledge page not found",
        )

    if (
        chunk.text_origin != "ocr"
        or not chunk.requires_human_review
    ):
        raise HTTPException(
            status_code=409,
            detail="Knowledge page does not require OCR review",
        )

    reviewed_chunk = chunk.model_copy(
        update={
            "text": request.text,
            "requires_human_review": False,
            "reviewed_by": request.reviewed_by,
            "reviewed_at": datetime.now(timezone.utc),
        }
    )

    service.upsert(reviewed_chunk)

    return reviewed_chunk
