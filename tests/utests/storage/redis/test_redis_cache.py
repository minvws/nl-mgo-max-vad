import uuid
from typing import Dict, Optional, Type
from unittest.mock import MagicMock, Mock, patch

from faker import Faker
import pytest

from app.storage.redis.redis_cache import RedisCache

A_NAMESPACE = str(uuid.uuid4())
A_KEY = str(uuid.uuid4())
A_VALUE = str(uuid.uuid4()).encode("utf-8")


def create_redis_cache(
    redis_client=MagicMock(),
    redis_get_debugger_factory=MagicMock(),
    redis_get_debugger=MagicMock(),
    enable_debugger=False,
    expire_in_seconds=53,
):
    redis_get_debugger_factory.create.return_value = redis_get_debugger
    return RedisCache(
        A_NAMESPACE,
        enable_debugger,
        expire_in_seconds,
        redis_client,
        redis_get_debugger_factory,
    )


def test_setup_redis_debugger():
    redis_get_debugger_factory = MagicMock()
    redis_get_debugger = MagicMock()
    create_redis_cache(
        redis_get_debugger=redis_get_debugger,
        redis_get_debugger_factory=redis_get_debugger_factory,
        enable_debugger=True,
    )

    redis_get_debugger_factory.create.assert_called_with(daemon=True)
    redis_get_debugger.start.assert_called()
    redis_get_debugger.run.assert_not_called()


def test_get():
    redis_client = MagicMock()
    cache = create_redis_cache(
        redis_client=redis_client,
    )
    redis_client.get.return_value = A_VALUE

    actual = cache.get(A_KEY)
    assert actual == A_VALUE
    redis_client.get.assert_called_with(f"{A_NAMESPACE}:{A_KEY}")


def test_get_with_debug_enabled():
    redis_client = MagicMock()
    redis_debugger = MagicMock()
    cache = create_redis_cache(
        redis_client=redis_client,
        enable_debugger=True,
        redis_get_debugger=redis_debugger,
    )
    redis_client.get.return_value = A_VALUE
    redis_client.exists.return_value = 0

    actual = cache.get(A_KEY)
    assert actual == A_VALUE
    redis_client.get.assert_called_with(f"{A_NAMESPACE}:DEBUG:{A_KEY}")
    redis_client.exists.assert_called_with(f"{A_NAMESPACE}:{A_KEY}")
    redis_debugger.debug_get.assert_called_with(f"{A_NAMESPACE}:DEBUG:{A_KEY}", A_VALUE)


def test_get_with_debug_enabled_and_key_already_exists():
    redis_client = MagicMock()
    redis_debugger = MagicMock()
    cache = create_redis_cache(
        redis_client=redis_client,
        enable_debugger=True,
        redis_get_debugger=redis_debugger,
    )
    redis_client.get.return_value = A_VALUE
    redis_client.exists.return_value = 1

    actual = cache.get(A_KEY)
    assert actual == A_VALUE
    redis_client.get.assert_called_with(f"{A_NAMESPACE}:{A_KEY}")
    redis_client.exists.assert_called_with(f"{A_NAMESPACE}:{A_KEY}")
    redis_debugger.debug_get.assert_called_with(f"{A_NAMESPACE}:{A_KEY}", A_VALUE)


def test_get_int():
    cache = create_redis_cache()
    # noinspection PyShadowingNames
    # pylint:disable=redefined-outer-name
    value = b"5"
    expected = 5
    with patch.object(RedisCache, "get", return_value=value) as get_method:
        actual = cache.get_int(A_KEY)
        assert actual == expected
        get_method.assert_called_with(A_KEY)


def test_get_int_when_not_parsable_returns_none():
    cache = create_redis_cache()
    # noinspection PyShadowingNames
    # pylint:disable=redefined-outer-name
    with patch.object(RedisCache, "get", return_value=A_VALUE) as get_method:
        actual = cache.get_int(A_KEY)
        assert actual is None
        get_method.assert_called_with(A_KEY)


def test_get_string():
    cache = create_redis_cache()
    with patch.object(RedisCache, "get", return_value=A_VALUE) as get_method:
        actual = cache.get_string(A_KEY)
        assert actual == A_VALUE.decode("utf-8")
        get_method.assert_called_with(A_KEY)


def test_get_bool_non_true_returns_false():
    cache = create_redis_cache()
    # noinspection PyShadowingNames
    with patch.object(RedisCache, "get", return_value=A_VALUE) as get_method:
        actual = cache.get_bool(A_KEY)
        assert actual is False
        get_method.assert_called_with(A_KEY)


def test_get_bool_from_string():
    cache = create_redis_cache()
    # noinspection PyShadowingNames
    # pylint:disable=redefined-outer-name
    value = b"TruE"
    with patch.object(RedisCache, "get", return_value=value) as get_method:
        actual = cache.get_bool(A_KEY)
        assert actual is True
        get_method.assert_called_with(A_KEY)


def test_get_bool_from_int():
    cache = create_redis_cache()
    # noinspection PyShadowingNames
    # pylint:disable=redefined-outer-name
    value = b"1"
    with patch.object(RedisCache, "get", return_value=value) as get_method:
        actual = cache.get_bool(A_KEY)
        assert actual is True
        get_method.assert_called_with(A_KEY)


@pytest.mark.parametrize(
    "expires_in_seconds, expected_expiry",
    [
        (None, 4),
        (900, 900),
    ],
)
def test_set(expires_in_seconds: Optional[int], expected_expiry: int):
    redis_client = MagicMock()
    cache = create_redis_cache(redis_client=redis_client, expire_in_seconds=4)
    redis_client.set.side_effect = [True, False]

    assert cache.set(A_KEY, A_VALUE, expires_in_seconds) is True
    expected_expiry = expires_in_seconds if expires_in_seconds is not None else 4
    redis_client.set.assert_called_with(
        f"{A_NAMESPACE}:{A_KEY}", A_VALUE, ex=expected_expiry
    )
    assert cache.set(A_KEY, A_VALUE) is False


class SerializationTestObject:
    def __init__(self, key: str):
        self.key = key

    def to_dict(self):
        return {"key": self.key}

    @classmethod
    def from_dict(cls, dictionary: Dict[str, str]):
        return cls(dictionary["key"])


@pytest.mark.parametrize(
    "value, expected_serialized",
    [
        (SerializationTestObject("value"), b'{"key": "value"}'),
        ({"key": "value"}, b'{"key": "value"}'),
    ],
)
def test_set_complex_object(mocker, value, expected_serialized):
    cache = create_redis_cache()
    with patch.object(RedisCache, "set", side_effect=[True, False]) as set_method:
        actual = cache.set_complex_object(A_KEY, value, expires_in_seconds=None)
        assert actual is True
        set_method.assert_called_with(
            A_KEY, expected_serialized, expires_in_seconds=None
        )
        assert cache.set_complex_object(A_KEY, value) is False


@pytest.mark.parametrize(
    "value, clazz, expected_object",
    [
        (
            b'{"key": "value"}',
            SerializationTestObject,
            SerializationTestObject("value"),
        ),
        (b'{"key": "value"}', Dict, {"key": "value"}),
    ],
)
def test_get_complex_object(mocker, value, clazz, expected_object):
    cache = create_redis_cache()

    with patch.object(RedisCache, "get", side_effect=[value, None]) as get_method:
        actual = cache.get_complex_object(A_KEY, clazz)

        if isinstance(actual, dict):
            assert actual["key"] == expected_object["key"]
        else:
            assert actual.key == expected_object.key

        get_method.assert_called_with(A_KEY)
        assert cache.get_complex_object(A_KEY, clazz) is None


def test_gen_token():
    redis_client = MagicMock()
    expected = "truerandom"
    redis_client.acl_genpass.return_value = expected
    cache = create_redis_cache(redis_client=redis_client)
    actual = cache.gen_token()
    assert actual == expected


def test_incr():
    redis_client = MagicMock()
    expected = "5"
    redis_client.incr.return_value = expected
    cache = create_redis_cache(redis_client=redis_client)
    actual = cache.incr(A_KEY)
    assert actual == expected
    redis_client.incr.assert_called_with(f"{A_NAMESPACE}:{A_KEY}")


def test_expire_succeeds():
    redis_client = MagicMock()
    redis_client.expire.return_value = True
    cache = create_redis_cache(redis_client=redis_client)
    assert cache.expire(A_KEY, 5434) is True
    redis_client.expire.assert_called_with(f"{A_NAMESPACE}:{A_KEY}", 5434)


def test_expire_fails():
    redis_client = MagicMock()
    redis_client.expire.return_value = False
    cache = create_redis_cache(redis_client=redis_client)
    assert cache.expire(A_KEY, 5434) is False
    redis_client.expire.assert_called_with(f"{A_NAMESPACE}:{A_KEY}", 5434)


def test_expire_time() -> None:
    redis_ttl = 20
    current_time = 1672214930.6804628
    expected_expire_time = 1672214950

    redis_client = Mock()
    redis_client.ttl.return_value = redis_ttl

    with patch(
        "app.storage.redis.redis_cache.time", MagicMock(return_value=current_time)
    ):
        cache = create_redis_cache(redis_client=redis_client)
        actual_expire_time = cache.expire_time(A_KEY)
        redis_client.ttl.assert_called_with(f"{A_NAMESPACE}:{A_KEY}")
        assert actual_expire_time == expected_expire_time


@pytest.mark.parametrize(
    "ttl_failure_code, expected_exception, expected_message",
    [
        (-2, KeyError, "Key '{key}' does not exist in Redis."),
        (-1, RuntimeError, "Key '{key}' exists but has no associated expire."),
    ],
)
def test_expire_time_raises_exceptions_for_ttl_failure_codes(
    ttl_failure_code: int,
    expected_exception: Type[Exception],
    expected_message: str,
) -> None:
    redis_client = Mock()
    redis_client.ttl.return_value = ttl_failure_code
    cache = create_redis_cache(redis_client=redis_client)

    assert isinstance(expected_message, str)
    with pytest.raises(expected_exception, match=expected_message.format(key=A_KEY)):
        cache.expire_time(A_KEY)


@pytest.mark.parametrize(
    "redis_return_value, expected",
    [
        (0, False),
        (1, True),
    ],
)
def test_exists(redis_return_value: int, expected: bool) -> None:
    redis_client = Mock()
    redis_client.exists.return_value = redis_return_value
    cache = create_redis_cache(redis_client=redis_client)
    assert cache.exists(A_KEY) is expected
    redis_client.exists.assert_called_with(f"{A_NAMESPACE}:{A_KEY}")


def test_delete():
    redis_client = MagicMock()
    cache = create_redis_cache(redis_client=redis_client)
    cache.delete(A_KEY)
    redis_client.delete.assert_called_with(f"{A_NAMESPACE}:{A_KEY}")


def test_prepend_with_namespace_when_debug_enabled():
    redis_client = MagicMock()
    cache = create_redis_cache(redis_client=redis_client, enable_debugger=True)
    redis_client.exists.return_value = 0
    expected = f"{A_NAMESPACE}:DEBUG:{A_KEY}"
    # pylint:disable=protected-access
    actual = cache._prepend_with_namespace(A_KEY)
    assert actual == expected
    redis_client.exists.assert_called_with(f"{A_NAMESPACE}:{A_KEY}")


def test_prepend_with_namespace_when_debug_enabled_end_non_debug_key_already_exists():
    redis_client = MagicMock()
    cache = create_redis_cache(redis_client=redis_client, enable_debugger=True)
    redis_client.exists.return_value = 1
    expected = f"{A_NAMESPACE}:{A_KEY}"
    # pylint:disable=protected-access
    actual = cache._prepend_with_namespace(A_KEY)
    assert actual == expected
    redis_client.exists.assert_called_with(f"{A_NAMESPACE}:{A_KEY}")


def test_prepend_with_namespace_when_debug_not_enabled():
    redis_client = MagicMock()
    cache = create_redis_cache(redis_client=redis_client, enable_debugger=False)
    expected = f"{A_NAMESPACE}:{A_KEY}"
    # pylint:disable=protected-access
    actual = cache._prepend_with_namespace(A_KEY)
    assert actual == expected
    redis_client.exists.assert_not_called()
