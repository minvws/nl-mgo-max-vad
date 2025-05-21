import secrets
from faker import Faker
import pytest
from nacl.exceptions import CryptoError
from nacl.secret import SecretBox
from app.services.encryption.url_safe_symmetric_encryptor import (
    UrlSafeSymmetricEncryptor,
)
from base64 import urlsafe_b64encode


class TestUrlSafeSymmetricEncryptor:
    @pytest.fixture
    def encryption_service(self) -> UrlSafeSymmetricEncryptor:
        raw_local_sym_key: str = secrets.token_hex(32)
        return UrlSafeSymmetricEncryptor(raw_local_sym_key)

    @pytest.fixture
    def fake_data(self, faker: Faker) -> bytes:
        return urlsafe_b64encode(faker.binary(length=64))

    def test_symm_encrypt(
        self, encryption_service: UrlSafeSymmetricEncryptor, fake_data: bytes
    ) -> None:
        encrypted_data: bytes = encryption_service.symm_encrypt(fake_data)
        assert encrypted_data != fake_data
        assert isinstance(encrypted_data, bytes)
        assert encrypted_data.isascii()
        assert b"=" not in encrypted_data

    def test_symm_decrypt(
        self, encryption_service: UrlSafeSymmetricEncryptor, fake_data: bytes
    ) -> None:
        encrypted_data: bytes = encryption_service.symm_encrypt(fake_data)
        decrypted_data: bytes = encryption_service.symm_decrypt(encrypted_data)
        assert decrypted_data == fake_data

    def test_symm_decrypt_invalid_data(
        self, encryption_service: UrlSafeSymmetricEncryptor, faker: Faker
    ) -> None:
        invalid_data: bytes = urlsafe_b64encode(faker.binary(length=64))
        with pytest.raises(CryptoError):
            encryption_service.symm_decrypt(invalid_data)

    def test_encrypt_decrypt_empty_data(
        self, encryption_service: UrlSafeSymmetricEncryptor
    ) -> None:
        data: bytes = b""
        encrypted_data: bytes = encryption_service.symm_encrypt(data)
        decrypted_data: bytes = encryption_service.symm_decrypt(encrypted_data)
        assert decrypted_data == data

    def test_decrypt_invalid_nonce(
        self, encryption_service: UrlSafeSymmetricEncryptor, fake_data: bytes
    ) -> None:
        encrypted_data: bytes = encryption_service.symm_encrypt(fake_data)
        invalid_encrypted_data: bytes = encrypted_data[:24] + b"0" + encrypted_data[25:]
        with pytest.raises(CryptoError):
            encryption_service.symm_decrypt(invalid_encrypted_data)

    def test_decrypt_modified_ciphertext(
        self, encryption_service: UrlSafeSymmetricEncryptor, fake_data: bytes
    ) -> None:
        encrypted_data: bytes = encryption_service.symm_encrypt(fake_data)
        modified_encrypted_data: bytes = (
            encrypted_data[: SecretBox.NONCE_SIZE]
            + b"0"
            + encrypted_data[SecretBox.NONCE_SIZE + 1 :]
        )
        with pytest.raises(CryptoError):
            encryption_service.symm_decrypt(modified_encrypted_data)
