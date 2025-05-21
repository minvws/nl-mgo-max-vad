from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response

from app.constants import AUTH_SESSION_COOKIE
from app.middlewares import active_auth_session
from app.models.auth_session import AuthSession
from app.services.auth_session.auth_session_cookie_builder import (
    AuthSessionCookieBuilder,
)
from app.storage.auth_session_cache import AuthSessionCache

auth_session_router = APIRouter()


@auth_session_router.post(
    "/auth/session/renew",
    status_code=204,
    responses={
        204: {
            "description": "Auth session successfully renewed",
        },
        410: {
            "description": "Auth session is gone",
        },
    },
)
@inject
def auth_session_renew(
    auth_session: Optional[AuthSession] = Depends(active_auth_session),
    auth_session_cache: AuthSessionCache = Depends(
        Provide["storage.auth_session_cache"]
    ),
    auth_session_cookie_builder: AuthSessionCookieBuilder = Depends(
        Provide["services.auth_session_cookie_builder"]
    ),
) -> Response:
    """
    Send request to renew the current auth session by resetting the TTL to a preconfigured amount of time.

    If successful, the response will contain a 'Set-Cookie' header with the new TTL.

    A 410 'Gone' response will be returned in either of the following cases:
    - the session feature is disabled;
    - the session ID refers to a non-existing session;
    - the application failed to renew the session.
    The response will also contain a 'Set-Cookie' header with Max-Age of 0, expiring the cookie in the browser.
    Upon receiving this response, the client should refrain from trying to renew this session again.
    """

    if not auth_session:
        return __make_410_gone_response()

    auth_session_id = auth_session.get_auth_session_id()
    if not auth_session_cache.renew(str(auth_session_id)):
        return __make_410_gone_response()

    response = Response(status_code=204)
    auth_session_cookie = auth_session_cookie_builder.create(auth_session_id)
    response.set_cookie(**auth_session_cookie.to_dict())

    return response


def __make_410_gone_response() -> Response:
    response = Response(status_code=410, content="Session is gone")
    response.delete_cookie(AUTH_SESSION_COOKIE)

    return response
