from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


FeedbackCategory = Literal["bug", "slow", "format", "ai", "suggestion", "other"]


class FeedbackRequest(BaseModel):
    category: FeedbackCategory
    description: str = Field(min_length=1, max_length=5000)
    contact: str | None = Field(default=None, max_length=320)
    route: str | None = Field(default=None, max_length=500)
    task_id: str | None = Field(default=None, max_length=36)
