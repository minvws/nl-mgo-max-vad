from inject import Binder
from max_core.services.userinfo.userinfo_service import UserinfoService

from .services import VadUserinfoService


class UserinfoBindings:
    def __call__(self, binder: Binder) -> None:
        binder.bind_to_constructor(
            UserinfoService,
            lambda: VadUserinfoService(),  # pylint: disable=no-value-for-parameter, unnecessary-lambda
        )
