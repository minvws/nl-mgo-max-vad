from unittest.mock import ANY, Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.middlewares import active_auth_session
from app.services.encryption.url_safe_symmetric_encryptor import (
    UrlSafeSymmetricEncryptor,
)
import pytest
from dependency_injector import containers, providers
from fastapi import Response, Request
from fastapi.datastructures import Headers

from app.constants import AUTH_SESSION_COOKIE
from app.models.authorize_request import AuthorizeRequest
from app.models.token_request import TokenRequest
from app.providers.oidc_provider import OIDCProvider
from app.models.auth_session import AuthSession
from app.storage.auth_session_cache import AuthSessionCache


@pytest.fixture
def oidc_provider_mock() -> Mock:
    return Mock(spec=OIDCProvider)


@pytest.fixture
def auth_session_cache_mock() -> Mock:
    return Mock(spec=AuthSessionCache)


@pytest.fixture
def with_container_overrides(
    container_overrides, oidc_provider_mock: Mock, auth_session_cache_mock: Mock
):
    class OverridingServicesContainer(containers.DeclarativeContainer):
        oidc_provider = providers.Object(oidc_provider_mock)

    class OverridingStorageContainer(containers.DeclarativeContainer):
        auth_session_cache = providers.Object(auth_session_cache_mock)

    def override_oidc(container):
        container.services.override(OverridingServicesContainer())
        container.storage.override(OverridingStorageContainer())

    container_overrides.append(override_oidc)


@pytest.fixture
def with_auth_session_config_enabled(config):
    config["auth_session"]["enabled"] = "true"


@pytest.mark.usefixtures("with_container_overrides")
def test_well_known(lazy_app, oidc_provider_mock: Mock):
    fake_response = Response("expected", status_code=234)
    oidc_provider_mock.well_known.return_value = fake_response
    app = lazy_app.value
    actual_response = app.get("/.well-known/openid-configuration")
    assert actual_response.text == "expected"
    assert actual_response.status_code == 234

    oidc_provider_mock.well_known.assert_called_once()


@pytest.mark.usefixtures("with_container_overrides")
def test_authorize(lazy_app, oidc_provider_mock: Mock):
    fake_response = Response("expected", status_code=234)
    authorize_request = AuthorizeRequest(
        client_id="ci",
        redirect_uri="ru",
        response_type="code",
        nonce="n",
        scope="s",
        state="s",
        code_challenge="cc",
        code_challenge_method="S256",
    )
    oidc_provider_mock.present_login_options_or_authorize.return_value = fake_response
    app = lazy_app.value
    actual_response = app.get(
        "/authorize?client_id=ci&redirect_uri=ru&response_type=code&nonce=n&scope=s&state=s&code_challenge=cc&code_challenge_method=S256"
    )
    assert actual_response.text == "expected"
    assert actual_response.status_code == 234

    oidc_provider_mock.present_login_options_or_authorize.assert_called_once_with(
        request=ANY,
        authorize_request=authorize_request,
        auth_session=ANY,
    )


@pytest.mark.usefixtures(
    "with_auth_session_config_enabled",
    "with_container_overrides",
)
def test_authorize_with_valid_auth_session_cookie(
    lazy_app, oidc_provider_mock: Mock, auth_session_cache_mock: Mock
) -> None:
    auth_session_cache_mock.exists.return_value = True
    test_client: TestClient = lazy_app.value
    url_safe_symmetric_encrypter: UrlSafeSymmetricEncryptor = (
        test_client.app.container.encryption_services.auth_session_encrypter()
    )

    auth_session_id = uuid4()
    encrypted_auth_session_id = url_safe_symmetric_encrypter.symm_encrypt(
        auth_session_id.bytes
    )

    fake_response = Response("authorize_response")
    oidc_provider_mock.present_login_options_or_authorize.return_value = fake_response

    actual_response = test_client.get(
        "/authorize?client_id=ci&redirect_uri=ru&response_type=code&nonce=n&scope=s&state=s&code_challenge=cc&code_challenge_method=S256",
        cookies={
            AUTH_SESSION_COOKIE: encrypted_auth_session_id.decode(),
        },
    )

    assert actual_response.text == "authorize_response"

    auth_session_cache_mock.exists.assert_called()
    oidc_provider_mock.present_login_options_or_authorize.assert_called_once()

    auth_session_call_arg = (
        oidc_provider_mock.present_login_options_or_authorize.call_args.kwargs[
            "auth_session"
        ]
    )
    assert isinstance(auth_session_call_arg, AuthSession)
    assert auth_session_call_arg.get_auth_session_id() == auth_session_id


@pytest.mark.usefixtures(
    "with_auth_session_config_enabled",
    "with_container_overrides",
)
def test_auth_session_cookie_invalided_when_not_considered_active(
    lazy_app, oidc_provider_mock: Mock
) -> None:
    fake_response = Response("authorize_response")
    oidc_provider_mock.present_login_options_or_authorize.return_value = fake_response

    test_client: TestClient = lazy_app.value
    test_client.app.dependency_overrides[active_auth_session] = lambda: None

    actual_response = test_client.get(
        "/authorize?client_id=ci&redirect_uri=ru&response_type=code&nonce=n&scope=s&state=s&code_challenge=cc&code_challenge_method=S256",
        cookies={
            AUTH_SESSION_COOKIE: "invalid",
        },
    )

    oidc_provider_mock.present_login_options_or_authorize.assert_called_once_with(
        request=ANY,
        authorize_request=ANY,
        auth_session=None,
    )

    assert actual_response.text == "authorize_response"

    set_cookie_header = actual_response.headers.get_list("set-cookie")[0]
    assert (
        f'{AUTH_SESSION_COOKIE}=""' in set_cookie_header
        and "Max-Age=0" in set_cookie_header
    ), "Auth session cookie not properly invalidated"


@pytest.mark.usefixtures("with_container_overrides")
def test_accesstoken(lazy_app, oidc_provider_mock: Mock):
    fake_response = Response("expected", status_code=234)
    query_string: str = (
        "grant_type=gt&code=c&redirect_uri=ru&code_verifier=cv&client_id=ci"
    )
    token_request = TokenRequest(
        grant_type="gt",
        code="c",
        redirect_uri="ru",
        code_verifier="cv",
        client_id="ci",
        query_string=query_string,
    )
    headers = Headers(
        {
            "host": "testserver",
            "user-agent": "testclient",
            "accept-encoding": "gzip, deflate",
            "accept": "*/*",
            "connection": "keep-alive",
            "a": "b",
            "content-length": "66",
        }
    )
    oidc_provider_mock.token.return_value = fake_response
    app = lazy_app.value
    actual_response = app.post(
        "/token",
        headers={"a": "b"},
        data="grant_type=gt&code=c&redirect_uri=ru&code_verifier=cv&client_id=ci",
    )
    assert actual_response.text == "expected"
    assert actual_response.status_code == 234
    oidc_provider_mock.token.assert_called_once_with(token_request, headers)


@pytest.mark.usefixtures("with_container_overrides")
def test_jwks(lazy_app, oidc_provider_mock: Mock):
    fake_response = Response("expected", status_code=234)
    oidc_provider_mock.jwks.return_value = fake_response
    app = lazy_app.value
    actual_response = app.get("/jwks")
    assert actual_response.text == "expected"
    assert actual_response.status_code == 234

    oidc_provider_mock.jwks.assert_called_once()


@pytest.mark.usefixtures("with_container_overrides")
def test_userinfo(lazy_app, oidc_provider_mock: Mock):
    fake_response = Response("expected", status_code=234)
    oidc_provider_mock.userinfo.return_value = fake_response
    app = lazy_app.value
    actual_response = app.get(
        "/userinfo",
        headers={"Authorization": "123"},
    )
    assert actual_response.text == "expected"
    assert actual_response.status_code == 234

    oidc_provider_mock.userinfo.assert_called_once()
    assert isinstance(oidc_provider_mock.userinfo.call_args_list[0][0][0], Request)
