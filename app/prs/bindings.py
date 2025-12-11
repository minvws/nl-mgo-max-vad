import httpx
from inject import Binder

from app.config.schemas import PrsConfig, PrsRepositoryType

from .repositories import ApiPrsRepository, MockPrsRepository, PrsRepository


class PrsBindings:
    def __init__(self, prs_config: PrsConfig) -> None:
        self.__prs_config = prs_config

    def __call__(self, binder: Binder) -> None:
        self.__bind_prs_repository(binder)

    def __bind_prs_repository(self, binder: Binder) -> None:
        if self.__prs_config.prs_repository == PrsRepositoryType.MOCK:
            binder.bind(PrsRepository, MockPrsRepository())
        elif self.__prs_config.prs_repository == PrsRepositoryType.API:
            binder.bind_to_constructor(
                PrsRepository,
                lambda: ApiPrsRepository(  # pylint: disable=no-value-for-parameter
                    # Pydantic validates this
                    repo_base_url=self.__prs_config.repo_base_url,  # type: ignore
                    organisation_id=self.__prs_config.organisation_id,
                    client=httpx.Client(),
                ),
            )
        else:
            raise NotImplementedError(
                f"PRS repository type not implemented: {self.__prs_config.prs_repository}"
            )
