from inject import Binder

from app.config.schemas import BrpConfig

from .repositories import ApiBrpRepository, BrpRepository, MockBrpRepository


class BrpBindings:
    def __init__(self, brp_config: BrpConfig) -> None:
        self.__brp_config = brp_config

    def __call__(self, binder: Binder) -> None:
        self.__bind_brp_repository(binder)

    def __bind_brp_repository(self, binder: Binder) -> None:
        if self.__brp_config.mock_brp:
            binder.bind(BrpRepository, MockBrpRepository())
        else:
            if self.__brp_config.base_url is None:
                raise ValueError("config.brp.base_url must be set")

            base_url: str = self.__brp_config.base_url

            binder.bind_to_constructor(
                BrpRepository,
                lambda: ApiBrpRepository(base_url, api_key=self.__brp_config.api_key),
            )
