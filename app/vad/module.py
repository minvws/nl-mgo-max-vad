import inject
from dependency_injector import providers
from dependency_injector.providers import Singleton

from app.dependency_injection.container import Container as MaxContainer

from .bindings import configure_bindings
from .services import VadUserinfoService


def init_module(max_container: MaxContainer) -> None:
    if not inject.is_configured():
        inject.configure(
            lambda binder: configure_bindings(
                binder=binder, config_file="vad.conf", max_container=max_container
            )
        )

    __inject_vad_userinfo_service(max_container=max_container)


def __inject_vad_userinfo_service(max_container: MaxContainer) -> None:
    vad_userinfo_service: Singleton[VadUserinfoService] = providers.Singleton(
        VadUserinfoService,
    )

    userinfo_providers = max_container.services.userinfo_service.providers.copy()  # type: ignore[attr-defined]
    userinfo_providers["vad"] = vad_userinfo_service

    userinfo_service = providers.Selector(
        selector=max_container.config.app.userinfo_service, **userinfo_providers
    )

    max_container.services.userinfo_service.override(userinfo_service)
