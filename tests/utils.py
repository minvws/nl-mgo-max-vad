import inject
from inject import BinderCallable

from app.bindings import AppBindings
from app.config.schemas import VadConfig


def configure_bindings(
    config: VadConfig,
    bindings_override: BinderCallable | None = None,
) -> None:
    """
    Configure dependency injection bindings for the application.

    If `bindings_override` is provided, the callback is invoked to override the default bindings.
    """

    def bindings_config(binder: inject.Binder) -> None:
        binder.install(AppBindings(config))

        if bindings_override:
            binder.install(bindings_override)

    inject.configure(bindings_config, clear=True, allow_override=True)
