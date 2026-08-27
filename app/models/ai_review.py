from typing import Literal

from pydantic import BaseModel, ConfigDict


class AIReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_filename: str
    decision: Literal[
        "accepted",
        "rejected",
        "needs_changes",
    ]
    notes: str | None = None
