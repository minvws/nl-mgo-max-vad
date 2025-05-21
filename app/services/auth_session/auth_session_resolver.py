import logging
from typing import Optional
from uuid import UUID

from app.models.auth_session import AuthSession
from app.services.auth_session.auth_session_encrypter import AuthSessionEncrypter
from app.storage.auth_session_cache import AuthSessionCache


class AuthSessionResolver:
    def __init__(
        self,
        auth_session_cache: AuthSessionCache,
        auth_session_encrypter: AuthSessionEncrypter,
    ) -> None:
        self._auth_session_cache = auth_session_cache
        self.__auth_session_encrypter = auth_session_encrypter
        self._logger = logging.getLogger(__name__)

    def resolve(self, cookie_value: str) -> Optional[AuthSession]:
        auth_session_id = self.__auth_session_encrypter.decrypt(cookie_value)

        return (
            AuthSession(auth_session_id)
            if auth_session_id and self._is_session_active(auth_session_id)
            else None
        )

    def _is_session_active(self, auth_session_id: UUID) -> bool:
        if self._auth_session_cache.exists(str(auth_session_id)):
            return True

        self._logger.debug("Session %s not found in cache.", auth_session_id)

        return False
