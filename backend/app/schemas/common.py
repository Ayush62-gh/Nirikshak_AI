from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class APIResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = "Operation successful"


class PaginationMeta(BaseModel):
    page: int = 1
    page_size: int = 20
    total_items: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    pagination: PaginationMeta
    message: Optional[str] = "Data retrieved successfully"
