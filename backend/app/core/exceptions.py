from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logging import logger


class NirikshakException(Exception):
    """Base exception for all domain-specific Nirikshak errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ValidationError(NirikshakException):
    """Raised when incoming payload or data validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class AuthenticationError(NirikshakException):
    """Raised when authentication fails or token is invalid/expired."""

    def __init__(self, message: str = "Invalid authentication credentials", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class AuthorizationError(NirikshakException):
    """Raised when an authenticated user lacks permissions for an operation."""

    def __init__(self, message: str = "Insufficient permissions for this action", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class NotFoundError(NirikshakException):
    """Raised when a requested entity is not found."""

    def __init__(self, message: str = "Requested resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class OCRProcessingError(NirikshakException):
    """Raised when OCR or image preprocessing fails."""

    def __init__(self, message: str = "OCR processing failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="OCR_PROCESSING_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


class ComplianceEngineError(NirikshakException):
    """Raised when rule engine evaluation encounters an unexpected state."""

    def __init__(self, message: str = "Compliance engine evaluation error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="COMPLIANCE_ENGINE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ReportGenerationError(NirikshakException):
    """Raised when PDF report generation fails."""

    def __init__(self, message: str = "Report generation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="REPORT_GENERATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


async def nirikshak_exception_handler(request: Request, exc: NirikshakException) -> JSONResponse:
    """Handler for all custom domain exceptions."""
    logger.warning(f"Domain Exception [{exc.code}] on {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for FastAPI / Pydantic request validation errors."""
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        errors.append({"field": loc, "issue": msg, "type": err.get("type")})

    logger.warning(f"Validation Error on {request.url.path}: {errors}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": {"validation_errors": errors},
            },
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handler for standard Starlette/FastAPI HTTPExceptions."""
    logger.info(f"HTTP Exception [{exc.status_code}] on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": {},
            },
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unhandled server exceptions."""
    logger.exception(f"Unhandled Exception on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "details": {"error_type": type(exc).__name__},
            },
        },
    )
