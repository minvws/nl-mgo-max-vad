from logging import getLogger
from typing import Optional
from uuid import UUID

from nacl.exceptions import CryptoError

from app.services.encryption.url_safe_symmetric_encryptor import (
    UrlSafeSymmetricEncryptor,
)


class AuthSessionEncrypter:
    def __init__(self, encrypter: UrlSafeSymmetricEncryptor):
        self.__encrypter = encrypter
        self.__logger = getLogger(__name__)

    def encrypt(self, auth_session_id: UUID) -> str:
        return self.__encrypter.symm_encrypt(auth_session_id.bytes).decode()

    def decrypt(self, encrypted_auth_session_id: str) -> Optional[UUID]:
        try:
            auth_session_id = self.__encrypter.symm_decrypt(
                encrypted_auth_session_id.encode("utf-8")
            )

            return UUID(bytes=auth_session_id)
        except CryptoError:
            self.__logger.warning("Failed to decrypt session", exc_info=True)

            return None
