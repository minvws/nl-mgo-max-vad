from typing import Optional
from uuid import UUID, uuid4
from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.dependency_injection.container import Container
from app.misc.utils import as_bool


@inject
def new_auth_session_id(
    auth_session_enabled: bool = Depends(
        Provide[Container.config.auth_session.enabled.as_(as_bool)]
    ),
) -> Optional[UUID]:
    if not auth_session_enabled:
        return None

    return uuid4()
