from email.utils import parsedate_to_datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from faker import Faker

from app.services.auth_session.auth_session_cookie_builder import (
    AuthSessionCookieBuilder,
)
from app.services.auth_session.auth_session_encrypter import AuthSessionEncrypter
from app.storage.auth_session_cache import AuthSessionCache


class TestAuthSessionCookieBuilder:
    @pytest.fixture()
    def auth_session_encrypter_mock(self) -> Mock:
        return Mock(spec=AuthSessionEncrypter)

    @pytest.fixture()
    def auth_session_cache_mock(self) -> Mock:
        return Mock(spec=AuthSessionCache)

    def test_cookie_value_is_encrypted(
        self,
        faker: Faker,
        auth_session_encrypter_mock: Mock,
        auth_session_cache_mock: Mock,
    ) -> None:
        auth_session_id = uuid4()
        encrypted_auth_session_id = faker.pystr()
        auth_session_encrypter_mock.encrypt.return_value = encrypted_auth_session_id
        auth_session_cache_mock.expire_time.return_value = faker.random_int()
        auth_session_cookie_builder = AuthSessionCookieBuilder(
            auth_session_encrypter=auth_session_encrypter_mock,
            auth_session_cache=auth_session_cache_mock,
            enforce_secure_cookie=faker.boolean(),
            cookie_expiry_offset_seconds=faker.random_int(),
        )
        cookie = auth_session_cookie_builder.create(auth_session_id)
        auth_session_encrypter_mock.encrypt.assert_called_once_with(auth_session_id)
        assert cookie.value == encrypted_auth_session_id

    @pytest.mark.parametrize("enforce_secure_cookie", [True, False])
    def test_cookie_is_conditionally_secure_based_on_config(
        self,
        faker: Faker,
        auth_session_encrypter_mock: Mock,
        auth_session_cache_mock: Mock,
        enforce_secure_cookie: bool,
    ) -> None:
        auth_session_id = uuid4()
        auth_session_encrypter_mock.encrypt.return_value = faker.pystr()
        auth_session_cache_mock.expire_time.return_value = faker.unix_time()
        auth_session_cookie_builder = AuthSessionCookieBuilder(
            auth_session_encrypter=auth_session_encrypter_mock,
            auth_session_cache=auth_session_cache_mock,
            enforce_secure_cookie=enforce_secure_cookie,
            cookie_expiry_offset_seconds=faker.random_int(),
        )
        cookie = auth_session_cookie_builder.create(auth_session_id)
        assert cookie.secure == enforce_secure_cookie

    def test_cookie_is_http_only(
        self,
        faker: Faker,
        auth_session_encrypter_mock: Mock,
        auth_session_cache_mock: Mock,
    ) -> None:
        auth_session_id = uuid4()
        auth_session_encrypter_mock.encrypt.return_value = faker.pystr()
        auth_session_cache_mock.expire_time.return_value = faker.unix_time()
        auth_session_cookie_builder = AuthSessionCookieBuilder(
            auth_session_encrypter=auth_session_encrypter_mock,
            auth_session_cache=auth_session_cache_mock,
            enforce_secure_cookie=True,
            cookie_expiry_offset_seconds=faker.random_int(),
        )
        cookie = auth_session_cookie_builder.create(auth_session_id)
        assert cookie.httponly is True

    def test_cookie_expires_before_cache_with_offset(
        self,
        faker: Faker,
        auth_session_encrypter_mock: Mock,
        auth_session_cache_mock: Mock,
    ) -> None:
        cookie_expiry_offset_seconds = 5
        cache_expire_date = "Mon, 24 Jul 2006 03:22:15 GMT"
        expected_cookie_expire_date = "Mon, 24 Jul 2006 03:22:10 GMT"

        cache_expire_time = parsedate_to_datetime(cache_expire_date).timestamp()
        auth_session_cache_mock.expire_time.return_value = cache_expire_time

        auth_session_cookie_builder = AuthSessionCookieBuilder(
            auth_session_encrypter=auth_session_encrypter_mock,
            auth_session_cache=auth_session_cache_mock,
            enforce_secure_cookie=faker.boolean(),
            cookie_expiry_offset_seconds=cookie_expiry_offset_seconds,
        )
        cookie = auth_session_cookie_builder.create(auth_session_id=uuid4())
        assert cookie.expires == expected_cookie_expire_date
