"""
Centralized FastAPI Exception Handlers.
Ensures standardized error JSON structures without leaking stack traces or internal paths.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.exceptions.custom_exceptions import RuleEngineBaseException


def register_exception_handlers(app):
    """Register custom exception handlers with the FastAPI application."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        formatted_errors = []
        for error in exc.errors():
            field_path = " -> ".join([str(loc) for loc in error.get("loc", []) if loc != "body"])
            formatted_errors.append({
                "field": field_path,
                "message": error.get("msg"),
                "type": error.get("type")
            })

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid product input payload.",
                    "details": formatted_errors
                }
            }
        )

    @app.exception_handler(RuleEngineBaseException)
    async def rule_engine_exception_handler(request: Request, exc: RuleEngineBaseException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.__class__.__name__.upper(),
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )

    @app.exception_handler(Exception)
    async def generic_uncaught_exception_handler(request: Request, exc: Exception):
        """Catch-all exception handler to prevent leaking internal stack traces or paths."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred while processing the compliance request."
                }
            }
        )
