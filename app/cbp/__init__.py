from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from inject import instance
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from .router import ClientsSyncRouter


def init_cbp_module(app: FastAPI) -> None:
    app.state.limiter = instance(Limiter)

    app.include_router(instance(ClientsSyncRouter))

    app.add_exception_handler(
        RateLimitExceeded,
        _rate_limit_exception_handler,
    )


def _rate_limit_exception_handler(_request: Request, _exc: Exception) -> Response:
    return JSONResponse({"detail": "Too many requests"}, status_code=429)
