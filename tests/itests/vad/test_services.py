from inject import instance

from app.storage.auth_session_cache import AuthSessionCache
from app.vad.services import UserinfoProvider


def test_userinfo_provider_dependency_injection(
    lazy_app, vad_userinfo_service_config
) -> None:
    _ = lazy_app.value
    userinfo_provider = instance(UserinfoProvider)

    assert userinfo_provider is not None
    # noinspection PyUnresolvedReferences
    assert (
        userinfo_provider._UserinfoProvider__auth_session_cache.__class__
        == AuthSessionCache
    )
