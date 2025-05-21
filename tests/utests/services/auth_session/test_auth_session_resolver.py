from unittest.mock import Mock
from uuid import uuid4
from nacl.exceptions import CryptoError

import pytest

from app.models.auth_session import AuthSession
from app.services.auth_session.auth_session_encrypter import AuthSessionEncrypter
from app.services.auth_session.auth_session_resolver import AuthSessionResolver
from app.storage.auth_session_cache import AuthSessionCache


class TestAuthSessionResolver:
    @pytest.fixture()
    def auth_session_cache_mock(self) -> Mock:
        return Mock(spec=AuthSessionCache)

    @pytest.fixture()
    def auth_session_encrypter_mock(self) -> Mock:
        return Mock(spec=AuthSessionEncrypter)

    def test_auth_session_can_be_resolved(
        self,
        auth_session_cache_mock: Mock,
        auth_session_encrypter_mock: Mock,
    ) -> None:
        auth_session_id = uuid4()

        auth_session_cache_mock.exists.return_value = True
        auth_session_encrypter_mock.decrypt.return_value = auth_session_id

        auth_session_resolver = AuthSessionResolver(
            auth_session_cache_mock,
            auth_session_encrypter_mock,
        )
        auth_session = auth_session_resolver.resolve(str(auth_session_id))

        auth_session_encrypter_mock.decrypt.assert_called_once_with(
            str(auth_session_id)
        )
        auth_session_cache_mock.exists.assert_called_once_with(str(auth_session_id))

        assert isinstance(auth_session, AuthSession)
        assert auth_session_id == auth_session.get_auth_session_id()

    def test_auth_session_not_resolved_when_not_cached(
        self,
        auth_session_cache_mock: Mock,
        auth_session_encrypter_mock: Mock,
    ) -> None:
        auth_session_id = uuid4()
        decrypted_value = auth_session_id

        auth_session_cache_mock.exists.return_value = False
        auth_session_encrypter_mock.decrypt.return_value = decrypted_value

        auth_session_resolver = AuthSessionResolver(
            auth_session_cache_mock,
            auth_session_encrypter_mock,
        )
        auth_session = auth_session_resolver.resolve(str(auth_session_id))
        assert auth_session is None

        auth_session_encrypter_mock.decrypt.assert_called_once_with(
            str(auth_session_id)
        )
        auth_session_cache_mock.exists.assert_called_once_with(str(auth_session_id))

    def test_auth_session_not_resolved_on_decryption_error(
        self,
        auth_session_cache_mock: Mock,
        auth_session_encrypter_mock: Mock,
    ) -> None:
        auth_session_id = str(uuid4())

        auth_session_encrypter_mock.decrypt.return_value = None

        auth_session_resolver = AuthSessionResolver(
            auth_session_cache_mock,
            auth_session_encrypter_mock,
        )
        auth_session = auth_session_resolver.resolve(auth_session_id)
        assert auth_session is None

        auth_session_cache_mock.exists.assert_not_called()
        auth_session_encrypter_mock.decrypt.assert_called_once_with(auth_session_id)

    def test_exception_raised_when_decrypted_value_is_no_valid_uuid(
        self,
        auth_session_cache_mock: Mock,
        auth_session_encrypter_mock: Mock,
    ) -> None:
        auth_session_id = "invalid_uuid"
        auth_session_encrypter_mock.decrypt.side_effect = ValueError(
            "bytes is not a 16-char string"
        )

        auth_session_resolver = AuthSessionResolver(
            auth_session_cache_mock,
            auth_session_encrypter_mock,
        )

        with pytest.raises(ValueError, match="bytes is not a 16-char string"):
            auth_session_resolver.resolve(auth_session_id)

        auth_session_cache_mock.exists.assert_not_called()
        auth_session_encrypter_mock.decrypt.assert_called_once_with(
            auth_session_id,
        )
