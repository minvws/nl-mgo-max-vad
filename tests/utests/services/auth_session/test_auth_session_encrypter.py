from unittest.mock import Mock
from faker.proxy import Faker
import pytest

from nacl.exceptions import CryptoError

from app.services.auth_session.auth_session_encrypter import AuthSessionEncrypter
from app.services.encryption.url_safe_symmetric_encryptor import (
    UrlSafeSymmetricEncryptor,
)


class TestAuthSessionEncrypter:
    @pytest.fixture()
    def url_safe_symmetric_encrypter(self) -> Mock:
        return Mock(spec=UrlSafeSymmetricEncryptor)

    def test_encrypt_returns_symm_encrypted_string(
        self, url_safe_symmetric_encrypter: Mock, faker: Faker
    ) -> None:
        auth_session_id = faker.uuid4(cast_to=None)
        url_safe_symmetric_encrypter.symm_encrypt.return_value = b"encrypted_bytes"

        auth_session_encrypter = AuthSessionEncrypter(url_safe_symmetric_encrypter)

        result = auth_session_encrypter.encrypt(auth_session_id)

        assert result == "encrypted_bytes"
        url_safe_symmetric_encrypter.symm_encrypt.assert_called_once_with(
            auth_session_id.bytes
        )

    def test_decrypt_returns_decrypted_uuid(
        self,
        url_safe_symmetric_encrypter: Mock,
        faker: Faker,
    ) -> None:
        encrypted_auth_session_id = faker.pystr()
        decrypted_auth_session_id = faker.uuid4(cast_to=None)
        url_safe_symmetric_encrypter.symm_decrypt.return_value = (
            decrypted_auth_session_id.bytes
        )

        auth_session_encrypter = AuthSessionEncrypter(url_safe_symmetric_encrypter)

        result = auth_session_encrypter.decrypt(encrypted_auth_session_id)

        assert result == decrypted_auth_session_id
        url_safe_symmetric_encrypter.symm_decrypt.assert_called_once_with(
            encrypted_auth_session_id.encode("utf-8")
        )

    def test_decrypt_returns_none_if_symm_encryption_raises_crypto_error(
        self,
        url_safe_symmetric_encrypter: Mock,
    ) -> None:
        encrypted_auth_session_id = "invalid_uuid"
        url_safe_symmetric_encrypter.symm_decrypt.side_effect = CryptoError(
            "Failed to decrypt"
        )

        auth_session_encrypter = AuthSessionEncrypter(url_safe_symmetric_encrypter)

        logger_mock = Mock()
        auth_session_encrypter._AuthSessionEncrypter__logger = logger_mock

        result = auth_session_encrypter.decrypt(encrypted_auth_session_id)

        assert result is None
        logger_mock.warning.assert_called_once_with(
            "Failed to decrypt session", exc_info=True
        )

    def test_decrypt_raises_exception_when_uuid_cannot_be_instantiated(
        self,
        url_safe_symmetric_encrypter: Mock,
    ) -> None:
        encrypted_auth_session_id = "invalid_uuid"
        url_safe_symmetric_encrypter.symm_decrypt.return_value = b"invalid_bytes"

        auth_session_encrypter = AuthSessionEncrypter(url_safe_symmetric_encrypter)

        with pytest.raises(ValueError, match="bytes is not a 16-char string"):
            auth_session_encrypter.decrypt(encrypted_auth_session_id)
