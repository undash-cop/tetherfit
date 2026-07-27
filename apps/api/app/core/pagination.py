from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int


class Page[T](BaseModel):
    items: list[T]
    meta: PageMeta


class PaginationParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    q: str | None = None
