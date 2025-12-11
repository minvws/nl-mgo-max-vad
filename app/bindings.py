from logging import Logger, getLogger

from inject import Binder

from max_core.bindings import MaxCoreBindings

from .brp.bindings import BrpBindings
from .cbp.bindings import CbpBindings
from .config.schemas import VadConfig
from .docs.bindings import DocsBindings
from .prs.bindings import PrsBindings
from .userinfo.bindings import UserinfoBindings


class AppBindings:
    def __init__(self, config: VadConfig) -> None:
        self.__config = config

    def __call__(self, binder: Binder) -> None:
        binder.install(MaxCoreBindings(self.__config))

        binder.bind(Logger, getLogger())
        binder.install(DocsBindings(self.__config.swagger))
        binder.install(PrsBindings(self.__config.prs))
        binder.install(BrpBindings(self.__config.brp))
        binder.install(CbpBindings(self.__config))
        binder.install(UserinfoBindings())
