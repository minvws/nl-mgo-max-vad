from inject import autoparams
from fastapi import Response
from max_core.services.userinfo.auth_session_based_userinfo_service import (
    AuthSessionBasedUserinfoService,
)
from max_core.storage.auth_session_cache import AuthSessionCache
from pyop.message import AuthorizationRequest

from max_core.models.auth_session import AuthSession
from max_core.models.login_method import LoginMethod
from max_core.models.acs_context import AcsContext
from max_core.exceptions.max_exceptions import ServerErrorException
from max_core.providers.oidc_provider import OIDCProvider as BaseOIDCProvider
from pyop.provider import AuthorizationResponse

from app.schemas import AuthSessionContextDTO


class OIDCProvider(BaseOIDCProvider):
    """
    OIDC provider that ensures consistent `sub` claims using cached auth session data.

    - `authorize_with_active_session`: retrieves the cached `user_id` to use as the
    `sub` claim in the context of an active auth session. This is necessary because
    authentication is skipped at DigiD, so there is no artifact response with a BSN
    to generate the `user_id`.
    - `py_op_authorize`: passes the cached `user_id` to PyOP to ensure the same `sub`
    is used.

    Used as part of a temporary binding override to maintain `sub` consistency
    across the OIDC flow with SAML-generated user IDs.
    """

    @autoparams("auth_session_cache")
    def __init__(self, auth_session_cache: AuthSessionCache, **kwargs):
        super().__init__(**kwargs)
        self._auth_session_cache = auth_session_cache

    def authorize_with_active_session(
        self,
        userinfo_service: AuthSessionBasedUserinfoService,
        authorization_request: AuthorizationRequest,
        client_id: str,
        login_method: LoginMethod,
        auth_session: AuthSession,
    ) -> Response:
        auth_session_context_data = self._auth_session_cache.get(
            auth_session.auth_session_id
        )
        if not auth_session_context_data:
            raise ServerErrorException(
                error_description="No auth session context found in cache"
            )

        auth_session_context = AuthSessionContextDTO(**auth_session_context_data)
        user_id = auth_session_context.user_id

        pyop_authorization_response = self.py_op_authorize(
            authorization_request, user_id
        )

        subject_identifier = self.get_subject_identifier(
            pyop_authorization_response["code"]
        )

        userinfo = userinfo_service.provide_userinfo_from_active_auth_session(
            auth_session, subject_identifier
        )

        self._authentication_cache.cache_acs_context(
            pyop_authorization_response["code"],
            AcsContext(
                client_id=client_id,
                authentication_method=login_method.name,
                userinfo=userinfo.body,
                userinfo_content_type=userinfo.content_type,
            ),
        )

        response_url = pyop_authorization_response.request(
            authorization_request["redirect_uri"],
            False,
        )

        return self._response_factory.create_redirect_response(response_url)

    def py_op_authorize(  # type: ignore[override]
        self,
        authorization_request: AuthorizationRequest,
        user_id: str,
    ) -> AuthorizationResponse:
        return self._pyop_provider.authorize(authorization_request, user_id)
