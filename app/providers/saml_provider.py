from hashlib import sha256
import logging
from inject import autoparams

from max_core.exceptions.max_exceptions import UnauthorizedError
from max_core.exceptions.oidc_exceptions import TEMPORARILY_UNAVAILABLE
from max_core.models.saml.artifact_response_mock import ArtifactResponseMock
from max_core.models.saml.assertion_consumer_service_request import (
    AssertionConsumerServiceRequest,
)

from max_core.storage.auth_session_cache import AuthSessionCache
from max_core.providers.saml_provider import SAMLProvider as BaseSAMLProvider

log = logging.getLogger(__package__)


class SAMLProvider(BaseSAMLProvider):
    """
    Custom SAML provider override:

    - Generates a hashed `user_id` from the BSN for PyOP to produce a consistent `sub`.
    - Passes this `user_id` to the OIDC provider to ensure the same `sub` is returned
      in the userinfo response.
    """

    @autoparams("auth_session_cache")
    def __init__(self, auth_session_cache: AuthSessionCache, **kwargs):
        super().__init__(**kwargs)
        self._auth_session_cache = auth_session_cache

    def handle_assertion_consumer_service(
        self,
        request: AssertionConsumerServiceRequest,
    ):
        authentication_context = self._oidc_provider.get_authentication_request_state(
            request.RelayState
        )

        digid_mock = authentication_context.authentication_method == "digid_mock"

        if not self._environment.startswith("prod") and digid_mock:
            artifact_response = ArtifactResponseMock(request.SAMLart)
        else:
            identity_provider = (
                self._saml_identity_provider_service.get_identity_provider(
                    authentication_context.authentication_state[
                        "identity_provider_name"
                    ]
                )
            )
            artifact_response = identity_provider.resolve_artifact(request.SAMLart)  # type: ignore[assignment]

        if artifact_response.saml_status.code.lower() != "success":
            error_description = (
                artifact_response.saml_status.message
                if artifact_response.saml_status.message
                else TEMPORARILY_UNAVAILABLE
            )
            raise UnauthorizedError(
                log_message=(
                    "Invalid saml response received with status: "
                    f"{artifact_response.saml_status.code}, "
                    f"{artifact_response.saml_status.message}"
                ),
                error_description=error_description,
            )

        bsn = artifact_response.get_bsn(authorization_by_proxy=False)
        user_id = sha256(bsn.encode("utf-8")).hexdigest()

        pyop_authorization_response = self._oidc_provider.py_op_authorize(  # type: ignore[call-arg]
            authentication_context.authorization_request,
            user_id,
        )

        subject_identifier = self._oidc_provider.get_subject_identifier(
            pyop_authorization_response["code"]
        )

        userinfo = self._userinfo_service.request_userinfo_for_saml_artifact(
            authentication_context,
            artifact_response,
            subject_identifier,
        )

        return self._oidc_provider.authenticate(
            authentication_context, userinfo, pyop_authorization_response
        )
