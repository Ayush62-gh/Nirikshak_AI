"""
Pydantic validation schemas.
"""

from app.schemas.common import (
    APIResponse,
    ErrorResponse,
    ErrorDetail,
    PaginatedResponse,
    PaginationMeta,
)
from app.schemas.health import HealthResponse
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)
from app.schemas.declaration import (
    DeclarationBase,
    DeclarationCreate,
    DeclarationResponse,
)
from app.schemas.violation import (
    ViolationBase,
    ViolationCreate,
    ViolationResponse,
)
from app.schemas.inspection import (
    InspectionCreate,
    InspectionResponse,
    InspectionDetailResponse,
    InspectionImageResponse,
)
from app.schemas.compliance import (
    RuleResultSchema,
    ComplianceScoreSchema,
    ComplianceResultResponse,
)

__all__ = [
    "APIResponse",
    "ErrorResponse",
    "ErrorDetail",
    "PaginatedResponse",
    "PaginationMeta",
    "HealthResponse",
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "DeclarationBase",
    "DeclarationCreate",
    "DeclarationResponse",
    "ViolationBase",
    "ViolationCreate",
    "ViolationResponse",
    "InspectionCreate",
    "InspectionResponse",
    "InspectionDetailResponse",
    "InspectionImageResponse",
    "RuleResultSchema",
    "ComplianceScoreSchema",
    "ComplianceResultResponse",
]
