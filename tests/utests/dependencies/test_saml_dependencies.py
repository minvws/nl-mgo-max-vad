from uuid import UUID
from unittest.mock import patch
from app.dependencies.saml_dependencies import new_auth_session_id


def test_new_auth_session_id_enabled() -> None:
    with patch("dependency_injector.wiring.inject"):
        result = new_auth_session_id(auth_session_enabled=True)
        assert isinstance(result, UUID)


def test_new_auth_session_id_disabled() -> None:
    with patch("dependency_injector.wiring.inject"):
        result = new_auth_session_id(auth_session_enabled=False)
        assert result is None
