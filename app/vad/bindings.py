import configparser
import logging

from inject import Binder

from app.dependency_injection.container import Container as MaxContainer
from app.services.auth_session.auth_session_encrypter import AuthSessionEncrypter
from app.storage.auth_session_cache import AuthSessionCache
from .brp.repositories import ApiBrpRepository, BrpRepository, MockBrpRepository
from .config.schemas import Config, PrsRepositoryType
from .config.services import ConfigParser
from .prs.repositories import PrsRepository, MockPrsRepository, ApiPrsRepository
from .utils import root_path


def configure_bindings(
    binder: Binder, config_file: str, max_container: MaxContainer
) -> None:
    """
    Configure dependency bindings for the application.
    """
    config: Config = __parse_app_config(config_file=config_file)
    binder.bind(Config, config)

    setup_logging(binder=binder, config=config)

    __bind_prs_repository(binder, config)
    __bind_brp_repository(binder, config)
    __bind_auth_session_cache(binder, max_container)
    __bind_auth_session_encrypter(binder, max_container)


def setup_logging(binder: Binder, config: Config) -> None:
    logging.basicConfig(level=config.app.loglevel.upper())
    logger: logging.Logger = logging.getLogger(name=config.app.name)
    binder.bind(logging.Logger, logger)


def __parse_app_config(config_file: str) -> Config:
    config_parser = ConfigParser(
        config_parser=configparser.ConfigParser(
            interpolation=configparser.ExtendedInterpolation(),
        ),
        config_path=root_path(config_file),
    )
    return config_parser.parse()


def __bind_prs_repository(binder: Binder, config: Config) -> None:
    if config.prs.prs_repository == PrsRepositoryType.MOCK:
        binder.bind(PrsRepository, MockPrsRepository())
    elif config.prs.prs_repository == PrsRepositoryType.API:
        binder.bind_to_constructor(
            PrsRepository,
            lambda: ApiPrsRepository(  # pylint: disable=no-value-for-parameter
                repo_base_url=config.prs.repo_base_url,
                organisation_id=config.prs.organisation_id,
            ),
        )
    else:
        raise NotImplementedError(
            f"PRS repository type not implemented: {config.prs.prs_repository}"
        )


def __bind_brp_repository(binder: Binder, config: Config) -> None:
    if config.brp.mock_brp:
        binder.bind(BrpRepository, MockBrpRepository())
    else:
        binder.bind_to_constructor(
            BrpRepository,
            lambda: ApiBrpRepository(config.brp.base_url, api_key=config.brp.api_key),
        )


def __bind_auth_session_cache(binder: Binder, max_container: MaxContainer) -> None:
    binder.bind(AuthSessionCache, max_container.storage.auth_session_cache())


def __bind_auth_session_encrypter(binder: Binder, max_container: MaxContainer) -> None:
    binder.bind(AuthSessionEncrypter, max_container.services.auth_session_encrypter())
