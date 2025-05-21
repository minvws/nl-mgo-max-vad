from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Cookie, Depends

from app.constants import AUTH_SESSION_COOKIE
from app.dependency_injection.container import Container
from app.misc.utils import as_bool
from app.models.auth_session import AuthSession
from app.services.auth_session.auth_session_resolver import AuthSessionResolver


@inject
def active_auth_session(
    auth_session_id: Optional[str] = Cookie(None, alias=AUTH_SESSION_COOKIE),
    auth_session_enabled: bool = Depends(
        Provide[Container.config.auth_session.enabled.as_(as_bool)]
    ),
    auth_session_resolver: AuthSessionResolver = Depends(
        Provide["services.auth_session_resolver"]
    ),
) -> Optional[AuthSession]:
    if not auth_session_enabled or not auth_session_id:
        return None

    return auth_session_resolver.resolve(auth_session_id)
