import logging
from typing import Optional
from uuid import UUID

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends

from app.dependencies.saml_dependencies import new_auth_session_id
from app.models.saml.assertion_consumer_service_request import (
    AssertionConsumerServiceRequest,
)

from app.providers.saml_provider import SAMLProvider
from app.services.auth_session.auth_session_cookie_builder import (
    AuthSessionCookieBuilder,
)

saml_router = APIRouter()

logger = logging.getLogger(__name__)


@saml_router.get("/acs")
@inject
def assertion_consumer_service(
    assertion_consumer_service_request: AssertionConsumerServiceRequest = Depends(
        AssertionConsumerServiceRequest.from_request
    ),
    saml_provider: SAMLProvider = Depends(Provide["services.saml_provider"]),
    auth_session_id: Optional[UUID] = Depends(new_auth_session_id),
    auth_session_cookie_builder: AuthSessionCookieBuilder = Depends(
        Provide["services.auth_session_cookie_builder"]
    ),
):
    response = saml_provider.handle_assertion_consumer_service(
        assertion_consumer_service_request,
        auth_session_id,
    )

    if auth_session_id:
        auth_session_cookie = auth_session_cookie_builder.create(auth_session_id)
        response.set_cookie(**auth_session_cookie.to_dict())

    return response


@saml_router.get("/metadata/{id_provider}")
@inject
def metadata(
    id_provider: str,
    saml_provider: SAMLProvider = Depends(Provide["services.saml_provider"]),
):
    return saml_provider.metadata(id_provider)
