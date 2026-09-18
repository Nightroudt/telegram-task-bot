from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskCreate(BaseModel):
    title: str = Field(max_length=255)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        # The sole source of truth for blankness: min_length=1 on the field
        # would only ever catch a literal "", while this also catches
        # whitespace-only input ("   ") — the same case, just later in the
        # pipeline, so keeping both meant two error messages for one problem.
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        return v


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    is_done: bool
    created_at: datetime
    completed_at: datetime | None


class TaskPage(BaseModel):
    items: list[TaskRead]
    page: int
    total_pages: int
    total: int
