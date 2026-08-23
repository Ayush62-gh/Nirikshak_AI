import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.schemas.scan_schemas import ErrorResponse

logger = logging.getLogger("nirikshak.errors")


class ExternalServiceError(Exception):
    """Raised when an external service (OCR or Rule Engine) fails or returns an error."""
    def __init__(self, detail: str = "External service integration failed"):
        self.detail = detail
        super().__init__(self.detail)


async def external_service_error_handler(request: Request, exc: ExternalServiceError):
    logger.error(f"ExternalServiceError on path {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=ErrorResponse(
            error="external_service_error",
            detail=exc.detail,
        ).model_dump(),
    )


async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"RequestValidationError on path {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="validation_error",
            detail="Invalid request parameters or payload",
        ).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on path {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="internal_server_error",
            detail="Internal server error",
        ).model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ExternalServiceError, external_service_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
