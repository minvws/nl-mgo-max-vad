from typing import Optional
from unittest.mock import MagicMock

import pytest

from faker import Faker
from fastapi import Response

from app.models.saml.artifact_response_mock import ArtifactResponseMock
from app.providers.oidc_provider import OIDCProvider
from app.providers.saml_provider import SAMLProvider
from app.models.saml.assertion_consumer_service_request import (
    AssertionConsumerServiceRequest,
)
from app.services.saml.saml_identity_provider_service import SamlIdentityProviderService
from app.services.userinfo.userinfo_service import UserinfoService


def create_saml_provider(
    oidc_provider: OIDCProvider = MagicMock(),
    userinfo_service: UserinfoService = MagicMock(),
    saml_identity_provider_service: SamlIdentityProviderService = MagicMock(),
) -> SAMLProvider:
    return SAMLProvider(
        saml_response_factory=MagicMock(),
        oidc_provider=oidc_provider,
        saml_identity_provider_service=saml_identity_provider_service,
        rate_limiter=MagicMock(),
        userinfo_service=userinfo_service,
        environment="test",
        clients={},
        authentication_cache=MagicMock(),
    )


@pytest.mark.parametrize("with_auth_session_id", [False, True])
def test_handle_assertion_consumer_service_with_and_without_auth_session_id(
    faker: Faker,
    with_auth_session_id: bool,
):
    auth_session_id: Optional[str] = (
        str(faker.uuid4()) if with_auth_session_id else None
    )

    auth_response = Response()

    mock_oidc_provider = MagicMock()
    mock_oidc_provider.get_authentication_request_state.return_value = MagicMock()
    mock_oidc_provider.py_op_authorize.return_value = {"code": "test_code"}
    mock_oidc_provider.get_subject_identifier.return_value = "test_subject_identifier"
    mock_oidc_provider.authenticate.return_value = auth_response

    request = AssertionConsumerServiceRequest(
        SAMLart="test_samlart", RelayState="test_relay_state", mocking=True
    )

    mock_userinfo_service = MagicMock()
    mock_userinfo_service.request_userinfo_for_digid_artifact.return_value = (
        "test_userinfo"
    )

    artifact_response_mock = ArtifactResponseMock("")

    identity_provider = MagicMock()
    identity_provider.resolve_artifact.return_value = artifact_response_mock

    mock_saml_identity_provider_service = MagicMock()
    mock_saml_identity_provider_service.get_identity_provider.return_value = (
        identity_provider
    )

    saml_provider = create_saml_provider(
        oidc_provider=mock_oidc_provider,
        userinfo_service=mock_userinfo_service,
        saml_identity_provider_service=mock_saml_identity_provider_service,
    )

    actual_response = saml_provider.handle_assertion_consumer_service(
        request, auth_session_id
    )

    mock_userinfo_service.request_userinfo_for_digid_artifact.assert_called_with(
        mock_oidc_provider.get_authentication_request_state.return_value,
        artifact_response_mock,
        mock_oidc_provider.get_subject_identifier.return_value,
        auth_session_id,
    )

    assert auth_response == actual_response
