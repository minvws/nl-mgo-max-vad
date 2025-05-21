from email.utils import parsedate_to_datetime
from uuid import uuid4
from unittest.mock import ANY, MagicMock, Mock

from fastapi.testclient import TestClient

from app.middlewares import active_auth_session
from app.services.encryption.url_safe_symmetric_encryptor import (
    UrlSafeSymmetricEncryptor,
)
from app.storage.auth_session_cache import AuthSessionCache
import pytest
from dependency_injector import containers, providers
from fastapi import Response

from app.constants import AUTH_SESSION_COOKIE
from app.dependencies.saml_dependencies import new_auth_session_id
from app.models.saml.assertion_consumer_service_request import (
    AssertionConsumerServiceRequest,
)
from app.providers.saml_provider import SAMLProvider


@pytest.fixture
def saml_provider_mock() -> Mock:
    return Mock(spec=SAMLProvider)


@pytest.fixture
def url_safe_symmetric_encryptor_mock() -> Mock:
    return Mock(spec=UrlSafeSymmetricEncryptor)


@pytest.fixture
def auth_session_cache_mock() -> Mock:
    return Mock(spec=AuthSessionCache)


@pytest.fixture
def with_container_overrides(
    container_overrides,
    saml_provider_mock: Mock,
    url_safe_symmetric_encryptor_mock: Mock,
    auth_session_cache_mock: Mock,
) -> None:
    class OverridingServicesContainer(containers.DeclarativeContainer):
        saml_provider = providers.Object(saml_provider_mock)

    class OverridingStorageContainer(containers.DeclarativeContainer):
        auth_session_cache = providers.Object(auth_session_cache_mock)

    class OverridingEncryptionServicesContainer(containers.DeclarativeContainer):
        auth_session_encrypter = providers.Object(url_safe_symmetric_encryptor_mock)

    def override_containers(container):
        container.services.override(OverridingServicesContainer())
        container.storage.override(OverridingStorageContainer())
        container.encryption_services.override(OverridingEncryptionServicesContainer())

    container_overrides.append(override_containers)


@pytest.mark.usefixtures("with_container_overrides")
def test_assertion_consumer_service(lazy_app, saml_provider_mock: Mock):
    fake_response = Response("expected", status_code=234)
    request = AssertionConsumerServiceRequest(SAMLart="s", RelayState="r", mocking=True)
    saml_provider_mock.handle_assertion_consumer_service.return_value = fake_response
    test_client: TestClient = lazy_app.value
    test_client.app.dependency_overrides[new_auth_session_id] = lambda: None
    actual = test_client.get("/acs?SAMLart=s&RelayState=r&mocking=1")
    assert actual.text == "expected"
    assert actual.status_code == 234

    saml_provider_mock.handle_assertion_consumer_service.assert_called_once_with(
        request, ANY
    )


@pytest.mark.usefixtures("with_container_overrides")
def test_assertion_consumer_service_without_mocking(lazy_app, saml_provider_mock: Mock):
    fake_response = Response("expected", status_code=234)
    request = AssertionConsumerServiceRequest(
        SAMLart="s", RelayState="r", mocking=False
    )
    saml_provider_mock.handle_assertion_consumer_service.return_value = fake_response
    test_client: TestClient = lazy_app.value
    test_client.app.dependency_overrides[new_auth_session_id] = lambda: None
    actual = test_client.get("/acs?SAMLart=s&RelayState=r")
    assert actual.text == "expected"
    assert actual.status_code == 234

    saml_provider_mock.handle_assertion_consumer_service.assert_called_once_with(
        request, ANY
    )


@pytest.mark.usefixtures("with_container_overrides")
@pytest.mark.parametrize(
    "use_ssl, expect_secure",
    [
        ("True", True),
        ("False", False),
    ],
)
def test_assertion_consumer_returns_auth_session_cookie(
    lazy_app,
    config,
    use_ssl: str,
    expect_secure: bool,
    auth_session_cache_mock: Mock,
    url_safe_symmetric_encryptor_mock: Mock,
    saml_provider_mock: Mock,
):
    expire_margin_in_seconds = 10
    session_expire_date = "Mon, 24 Mar 2025 13:50:10 GMT"
    expected_cookie_expire_date = "Mon, 24 Mar 2025 13:50:00 GMT"

    config["auth_session"]["enabled"] = "True"
    config["auth_session"]["cookie_expiry_offset_seconds"] = str(
        expire_margin_in_seconds
    )
    config["uvicorn"]["use_ssl"] = use_ssl

    session_expire_time = parsedate_to_datetime(session_expire_date).timestamp()
    auth_session_cache_mock.expire_time.return_value = session_expire_time

    encrypted_auth_session_id = "encrypted_auth_session_id"
    url_safe_symmetric_encryptor_mock.symm_encrypt.return_value = (
        encrypted_auth_session_id.encode()
    )

    auth_session_id = uuid4()
    acs_response = Response("expected", status_code=234)

    saml_provider_mock.handle_assertion_consumer_service.return_value = acs_response

    app = lazy_app.value
    fastapi = app.app
    fastapi.dependency_overrides[new_auth_session_id] = lambda: auth_session_id

    response = app.get("/acs?SAMLart=s&RelayState=r&mocking=1")

    saml_provider_mock.handle_assertion_consumer_service.assert_called_once_with(
        ANY,
        auth_session_id,
    )

    actual_cookie = response.headers.get("set-cookie")
    expected_cookie = (
        f"auth_session={encrypted_auth_session_id}; "
        f"expires={expected_cookie_expire_date}; "
        "HttpOnly; "
        "Path=/; "
        "SameSite=lax"
    )

    if expect_secure:
        expected_cookie += "; Secure"

    assert actual_cookie == expected_cookie


@pytest.mark.usefixtures("with_container_overrides")
def test_assertion_consumer_conditionally_returns_no_auth_session_cookie_when_disabled(
    lazy_app,
    config,
    saml_provider_mock: Mock,
):
    config["auth_session"]["enabled"] = "False"

    fake_response = Response("expected", status_code=234)
    saml_provider_mock.handle_assertion_consumer_service.return_value = fake_response

    app = lazy_app.value
    response = app.get("/acs?SAMLart=s&RelayState=r&mocking=1")

    saml_provider_mock.handle_assertion_consumer_service.assert_called_once()

    assert AUTH_SESSION_COOKIE not in response.cookies


@pytest.mark.usefixtures("with_container_overrides")
def test_metadata(lazy_app, saml_provider_mock: Mock):
    fake_response = Response("expected", status_code=234)
    saml_provider_mock.metadata.return_value = fake_response
    test_client: TestClient = lazy_app.value
    test_client.app.dependency_overrides[new_auth_session_id] = lambda: None
    actual_response = test_client.get("/metadata/id_provider")

    assert actual_response.text == "expected"
    assert actual_response.status_code == 234

    saml_provider_mock.metadata.assert_called_once_with("id_provider")
