from unittest.mock import Mock
from uuid import uuid4
from faker import Faker

from app.constants import AUTH_SESSION_PREFIX
from app.services.encryption.sym_encryption_service import SymEncryptionService
from app.storage.auth_session_cache import AuthSessionCache
from app.storage.cache import Cache


class TestAuthSessionCache:
    def test_set(self, faker: Faker) -> None:
        mock_cache = Mock(spec=Cache)
        mock_encryption_service = Mock(spec=SymEncryptionService)
        auth_session_id = str(uuid4())
        cache_ttl_seconds = faker.random_int()

        data = {"key": "value"}
        encrypted_context = faker.pystr()
        auth_session_cache = self.create_auth_session_cache(
            cache=mock_cache,
            sym_encryption_service=mock_encryption_service,
            cache_ttl_seconds=cache_ttl_seconds,
        )

        mock_encryption_service.symm_encrypt.return_value = encrypted_context

        auth_session_cache.set(auth_session_id, data)

        mock_cache.set.assert_called_with(
            f"{AUTH_SESSION_PREFIX}:{auth_session_id}",
            encrypted_context,
            cache_ttl_seconds,
        )
        mock_encryption_service.symm_encrypt.assert_called_with(
            '{"key": "value"}'.encode("utf-8")
        )

    def test_get_returns_data(self, faker: Faker) -> None:
        mock_cache = Mock(spec=Cache)
        mock_encryption_service = Mock(spec=SymEncryptionService)
        auth_session_id = str(uuid4())
        encrypted_context = faker.pystr().encode("utf-8")
        auth_session_cache = self.create_auth_session_cache(
            cache=mock_cache,
            sym_encryption_service=mock_encryption_service,
        )

        mock_cache.get.return_value = encrypted_context
        mock_encryption_service.symm_decrypt.return_value = '{"key": "value"}'.encode(
            "utf-8"
        )

        result = auth_session_cache.get(auth_session_id)

        assert result == {"key": "value"}
        mock_cache.get.assert_called_with(f"{AUTH_SESSION_PREFIX}:{auth_session_id}")
        mock_encryption_service.symm_decrypt.assert_called_with(encrypted_context)

    def test_get_returns_none_for_non_bytes_value(
        self,
        faker: Faker,
    ) -> None:
        mock_cache = Mock(spec=Cache)
        auth_session_id = str(uuid4())
        auth_session_cache = self.create_auth_session_cache(cache=mock_cache)

        mock_cache.get.return_value = faker.pystr()

        result = auth_session_cache.get(auth_session_id)

        assert result is None

    def test_renew_sets_new_expire_time(
        self,
        faker: Faker,
    ) -> None:
        auth_session_id = str(uuid4())
        cache_ttl_seconds = faker.random_int()

        mock_cache = Mock(spec=Cache)
        auth_session_cache = self.create_auth_session_cache(
            cache=mock_cache,
            cache_ttl_seconds=cache_ttl_seconds,
        )

        mock_cache.expire.return_value = None

        assert auth_session_cache.renew(auth_session_id) is None
        mock_cache.expire.assert_called_with(
            f"{AUTH_SESSION_PREFIX}:{auth_session_id}",
            cache_ttl_seconds,
        )

    def test_expire_time(self, faker: Faker) -> None:
        auth_session_id = str(uuid4())
        cache_expire_time = faker.random_int()

        mock_cache = Mock(spec=Cache)
        auth_session_cache = self.create_auth_session_cache(
            cache=mock_cache,
            cache_ttl_seconds=faker.random_int(),
        )

        mock_cache.expire_time.return_value = cache_expire_time

        result = auth_session_cache.expire_time(auth_session_id)

        assert result is cache_expire_time
        mock_cache.expire_time.assert_called_with(
            f"{AUTH_SESSION_PREFIX}:{auth_session_id}",
        )

    def test_exists(self, faker: Faker) -> None:
        auth_session_id = str(uuid4())
        cache_exists = faker.boolean()

        mock_cache = Mock(spec=Cache)
        auth_session_cache = self.create_auth_session_cache(
            cache=mock_cache,
            cache_ttl_seconds=faker.random_int(),
        )

        mock_cache.exists.return_value = cache_exists

        result = auth_session_cache.exists(auth_session_id)

        assert result is cache_exists
        mock_cache.exists.assert_called_with(
            f"{AUTH_SESSION_PREFIX}:{auth_session_id}",
        )

    def create_auth_session_cache(
        self,
        cache: Cache = Mock(spec=Cache),
        sym_encryption_service: SymEncryptionService = Mock(spec=SymEncryptionService),
        cache_ttl_seconds: int = 10,
    ) -> AuthSessionCache:
        return AuthSessionCache(
            cache=cache,
            sym_encryption_service=sym_encryption_service,
            cache_ttl_seconds=cache_ttl_seconds,
        )
