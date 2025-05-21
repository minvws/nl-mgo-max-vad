import json
from typing import Any, Dict, Optional
from app.constants import AUTH_SESSION_PREFIX
from app.services.encryption.sym_encryption_service import SymEncryptionService
from app.storage.cache import Cache


class AuthSessionCache:
    def __init__(
        self,
        cache: Cache,
        sym_encryption_service: SymEncryptionService,
        cache_ttl_seconds: int,
    ) -> None:
        self._cache = cache
        self._sym_encryption_service = sym_encryption_service
        self._cache_ttl_seconds = cache_ttl_seconds

    def _cache_key(self, auth_session_id: str):
        return f"{AUTH_SESSION_PREFIX}:{auth_session_id}"

    def exists(self, auth_session_id: str) -> bool:
        key = self._cache_key(auth_session_id)
        return self._cache.exists(key)

    def expire_time(self, auth_session_id: str) -> int:
        key = self._cache_key(auth_session_id)
        return self._cache.expire_time(key)

    def get(self, auth_session_id: str) -> Optional[Dict[str, Any]]:
        encrypted_context = self._cache.get(self._cache_key(auth_session_id))
        if not isinstance(encrypted_context, bytes):
            return None

        return json.loads(
            self._sym_encryption_service.symm_decrypt(encrypted_context).decode("utf-8")
        )

    def renew(self, auth_session_id: str) -> bool:
        key = self._cache_key(auth_session_id)
        return self._cache.expire(key, self._cache_ttl_seconds)

    def set(self, auth_session_id: str, data: Dict[str, Any]) -> None:
        encrypted_context = self._sym_encryption_service.symm_encrypt(
            json.dumps(data).encode("utf-8")
        )

        self._cache.set(
            self._cache_key(auth_session_id),
            encrypted_context,
            self._cache_ttl_seconds,
        )
