from pydantic import BaseModel, ConfigDict, Field, field_validator


class KnowledgeChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source_id must not be blank")

        if "\n" in value or "\r" in value:
            raise ValueError("source_id must be single-line")

        return value.strip()
    source_title: str = Field(min_length=1)

    @field_validator("source_title")
    @classmethod
    def validate_source_title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source_title must not be blank")

        if "\n" in value or "\r" in value:
            raise ValueError("source_title must be single-line")

        return value.strip()
    section: str | None = None

    @field_validator("section")
    @classmethod
    def validate_section(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("section must not be blank")

        if value is not None and (
            "\n" in value or "\r" in value
        ):
            raise ValueError("section must be single-line")

        return value.strip() if value is not None else None
    page: int | None = Field(default=None, ge=1)
    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be blank")
        return value

class KnowledgeSearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk: KnowledgeChunk
    matched_terms: list[str] = Field(min_length=1)

    @field_validator("matched_terms")
    @classmethod
    def validate_matched_terms(cls, value: list[str]) -> list[str]:
        if any(not term.strip() for term in value):
            raise ValueError("matched_terms must not contain blank values")

        if any(
            "\n" in term or "\r" in term
            for term in value
        ):
            raise ValueError("matched_terms must be single-line")

        return [term.strip() for term in value]
