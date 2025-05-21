from email.utils import formatdate
from uuid import UUID

from app.models.auth_session_cookie import AuthSessionCookie
from app.services.auth_session.auth_session_encrypter import AuthSessionEncrypter
from app.storage.auth_session_cache import AuthSessionCache


class AuthSessionCookieBuilder:
    def __init__(
        self,
        auth_session_encrypter: AuthSessionEncrypter,
        auth_session_cache: AuthSessionCache,
        enforce_secure_cookie: bool,
        cookie_expiry_offset_seconds: int,
    ) -> None:
        self.__auth_session_encrypter = auth_session_encrypter
        self._auth_session_cache = auth_session_cache
        self._enforce_secure_cookie = enforce_secure_cookie
        self._cookie_expiry_offset_seconds = cookie_expiry_offset_seconds

    def create(self, auth_session_id: UUID) -> AuthSessionCookie:
        encrypted_auth_session_id = self.__auth_session_encrypter.encrypt(
            auth_session_id
        )
        cookie_expiry_date = self._calculate_cookie_expiry_date(auth_session_id)

        return self._build_auth_session_cookie(
            encrypted_auth_session_id, cookie_expiry_date
        )

    def _calculate_cookie_expiry_date(self, auth_session_id: UUID) -> str:
        cache_expiry_time = self._auth_session_cache.expire_time(str(auth_session_id))
        return formatdate(
            cache_expiry_time - self._cookie_expiry_offset_seconds, usegmt=True
        )

    def _build_auth_session_cookie(
        self, encrypted_auth_session_id: str, cookie_expiry_date: str
    ) -> AuthSessionCookie:
        return AuthSessionCookie(
            value=encrypted_auth_session_id,
            secure=self._enforce_secure_cookie,
            expires=cookie_expiry_date,
        )
