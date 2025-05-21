from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.middlewares import active_auth_session
from app.models.auth_session import AuthSession
from app.services.auth_session.auth_session_resolver import AuthSessionResolver


@pytest.fixture()
def auth_session_resolver_mock() -> Mock:
    return Mock(spec=AuthSessionResolver)


def test_active_auth_session_with_valid_auth_session_id(
    auth_session_resolver_mock: Mock,
) -> None:
    auth_session_id = uuid4()
    resolved_auth_session = AuthSession(auth_session_id)
    auth_session_resolver_mock.resolve.return_value = resolved_auth_session

    with patch("dependency_injector.wiring.inject"):
        actual_auth_session = active_auth_session(
            auth_session_id=str(auth_session_id),
            auth_session_enabled=True,
            auth_session_resolver=auth_session_resolver_mock,
        )

    auth_session_resolver_mock.resolve.assert_called_once_with(str(auth_session_id))

    assert actual_auth_session is resolved_auth_session


def test_active_auth_session_returns_none_when_feature_is_disabled(
    auth_session_resolver_mock: Mock,
) -> None:
    auth_session_id = str(uuid4())
    with patch("dependency_injector.wiring.inject"):
        auth_session = active_auth_session(
            auth_session_id=auth_session_id,
            auth_session_enabled=False,
            auth_session_resolver=auth_session_resolver_mock,
        )

    assert auth_session is None
    auth_session_resolver_mock.resolve.assert_not_called()


def test_active_auth_session_returns_none_when_cookie_is_not_provided(
    auth_session_resolver_mock: Mock,
) -> None:
    with patch("dependency_injector.wiring.inject"):
        auth_session = active_auth_session(
            auth_session_id=None,
            auth_session_enabled=True,
            auth_session_resolver=auth_session_resolver_mock,
        )

    assert auth_session is None
    auth_session_resolver_mock.resolve.assert_not_called()
