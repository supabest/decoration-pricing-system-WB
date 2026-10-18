"""通用 Pydantic 模型"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


class BatchOperationRequest(BaseModel):
    ids: List[int]


class BatchOperationResponse(BaseModel):
    success_count: int
    fail_count: int
    errors: Optional[List[str]] = None
