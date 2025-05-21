import inject
from app.vad.services import VadUserinfoService


def test_init_module_configures_inject_and_registers_vad_userinfo_service(
    lazy_app, lazy_container, app_mode_default, vad_userinfo_service_config
) -> None:
    _ = lazy_app.value
    max_container = lazy_container.value

    assert inject.is_configured()
    assert max_container.services.userinfo_service().__class__ == VadUserinfoService
