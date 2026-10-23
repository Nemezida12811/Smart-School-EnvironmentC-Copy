"""Єдиний формат відповідей: {success, data} / {success: false, error: {...}}."""
import logging
from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("api")


class ApiError(Exception):
    def __init__(self, status: int, message: str, details: dict | None = None):
        self.status = status
        self.message = message
        self.details = details


def ok(data: dict | list | None = None, status: int = 200) -> JSONResponse:
    return JSONResponse({"success": True, "data": data if data is not None else {}}, status_code=status)


def _error_response(status: int, message: str, details: dict | None = None) -> JSONResponse:
    error: dict = {"message": message, "statusCode": status}
    if details:
        error["details"] = details
    return JSONResponse({"success": False, "error": error}, status_code=status)


@contextmanager
def failing_as(message: str, with_details: bool = False):
    """Аналог try/catch у роутах: будь-яка несподівана помилка -> 500 з потрібним текстом."""
    try:
        yield
    except ApiError:
        raise
    except Exception as exc:
        log.exception("❌ %s", message)
        raise ApiError(500, message, {"message": str(exc)} if with_details else None) from exc


def iso(dt: datetime | None) -> str | None:
    """Дата у форматі JS Date.toJSON(): 2025-12-16T15:00:00.000Z"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def register_handlers(app) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError):
        return _error_response(exc.status, exc.message, exc.details)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        return _error_response(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        return _error_response(400, "Invalid request body")

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        log.exception("❌ Unhandled error")
        return _error_response(500, "Internal server error")
