from unittest.mock import Mock

from app.services.auth_session.auth_session_cookie_builder import (
    AuthSessionCookieBuilder,
)
from app.storage.auth_session_cache import AuthSessionCache
import pytest
from dependency_injector import containers, providers
from faker import Faker
from fastapi import Cookie
from fastapi.testclient import TestClient

from app.constants import AUTH_SESSION_COOKIE
from app.middlewares import active_auth_session
from app.models.auth_session import AuthSession
from app.models.auth_session_cookie import AuthSessionCookie


@pytest.fixture
def auth_session_cache_mock() -> Mock:
    return Mock(spec=AuthSessionCache)


@pytest.fixture
def auth_session_cookie_builder_mock() -> Mock:
    return Mock(spec=AuthSessionCookieBuilder)


@pytest.fixture
def with_container_overrides(
    container_overrides,
    auth_session_cache_mock: Mock,
    auth_session_cookie_builder_mock: Mock,
) -> None:
    class OverridingStorageContainer(containers.DeclarativeContainer):
        auth_session_cache = providers.Object(auth_session_cache_mock)

    class OverridingServicesContainer(containers.DeclarativeContainer):
        auth_session_cookie_builder = providers.Object(auth_session_cookie_builder_mock)

    def overrides(container):
        container.storage.override(OverridingStorageContainer())
        container.services.override(OverridingServicesContainer())

    container_overrides.append(overrides)


@pytest.mark.usefixtures("with_container_overrides")
def test_auth_session_renew_returns_410_gone_if_session_is_disabled(
    lazy_app,
    config,
    faker: Faker,
    auth_session_cache_mock: Mock,
    auth_session_cookie_builder_mock: Mock,
) -> None:
    config["auth_session"]["enabled"] = "False"

    test_client: TestClient = lazy_app.value

    response = test_client.post(
        "/auth/session/renew", cookies={AUTH_SESSION_COOKIE: faker.sha256()}
    )

    assert response.status_code == 410
    assert "set-cookie" in response.headers
    assert "Max-Age=0" in response.headers["set-cookie"]

    auth_session_cache_mock.renew.assert_not_called()
    auth_session_cookie_builder_mock.create.assert_not_called()


@pytest.mark.usefixtures("with_container_overrides")
def test_auth_session_renew_returns_410_gone_if_no_session(
    lazy_app,
    config,
    faker: Faker,
    auth_session_cache_mock: Mock,
    auth_session_cookie_builder_mock: Mock,
) -> None:
    config["auth_session"]["enabled"] = "True"

    test_client: TestClient = lazy_app.value
    test_client.app.dependency_overrides[active_auth_session] = lambda: None

    response = test_client.post(
        "/auth/session/renew", cookies={AUTH_SESSION_COOKIE: faker.sha256()}
    )

    assert response.status_code == 410
    assert "set-cookie" in response.headers
    assert "Max-Age=0" in response.headers["set-cookie"]

    auth_session_cache_mock.renew.assert_not_called()
    auth_session_cookie_builder_mock.create.assert_not_called()


@pytest.mark.usefixtures("with_container_overrides")
def test_auth_session_renew_returns_410_gone_if_ttl_could_not_be_extended(
    lazy_app,
    config,
    faker: Faker,
    auth_session_cache_mock: Mock,
    auth_session_cookie_builder_mock: Mock,
):
    config["auth_session"]["enabled"] = "True"
    auth_session_id = faker.uuid4(cast_to=None)

    auth_session_cache_mock.renew.return_value = False
    auth_session_cookie_builder_mock.create.return_value = AuthSessionCookie(
        value=faker.sha256(),
        secure=True,
        expires=faker.unix_time(),
    )

    def assert_and_return_auth_session(
        cookie_auth_session_id: str = Cookie(None, alias=AUTH_SESSION_COOKIE),
    ) -> AuthSession:
        assert cookie_auth_session_id == str(auth_session_id)
        return AuthSession(auth_session_id)

    test_client: TestClient = lazy_app.value
    test_client.app.dependency_overrides[active_auth_session] = (
        assert_and_return_auth_session
    )

    response = test_client.post(
        "/auth/session/renew", cookies={AUTH_SESSION_COOKIE: str(auth_session_id)}
    )

    assert response.status_code == 410
    assert "set-cookie" in response.headers
    assert "Max-Age=0" in response.headers["set-cookie"]

    auth_session_cache_mock.renew.assert_called_with(str(auth_session_id))
    auth_session_cookie_builder_mock.create.assert_not_called()


@pytest.mark.usefixtures("with_container_overrides")
def test_auth_session_renew_returns_cookie_with_extended_ttl(
    lazy_app,
    config,
    faker: Faker,
    auth_session_cache_mock: Mock,
    auth_session_cookie_builder_mock: Mock,
):
    config["auth_session"]["enabled"] = "True"
    auth_session_id = faker.uuid4(cast_to=None)
    renewed_cookie_expire_date = "Mon, 24 Mar 2025 13:57:45 GMT;"

    auth_session_cache_mock.renew.return_value = True
    auth_session_cookie_builder_mock.create.return_value = AuthSessionCookie(
        value=faker.sha256(),
        secure=True,
        expires=renewed_cookie_expire_date,
    )

    def assert_and_return_auth_session(
        cookie_auth_session_id: str = Cookie(None, alias=AUTH_SESSION_COOKIE),
    ) -> AuthSession:
        assert cookie_auth_session_id == str(auth_session_id)
        return AuthSession(auth_session_id)

    test_client: TestClient = lazy_app.value
    test_client.app.dependency_overrides[active_auth_session] = (
        assert_and_return_auth_session
    )

    response = test_client.post(
        "/auth/session/renew", cookies={AUTH_SESSION_COOKIE: str(auth_session_id)}
    )

    assert response.status_code == 204
    assert "set-cookie" in response.headers
    assert f"expires={renewed_cookie_expire_date}" in response.headers["set-cookie"]

    auth_session_cache_mock.renew.assert_called_with(str(auth_session_id))
    auth_session_cookie_builder_mock.create.assert_called_with(auth_session_id)
