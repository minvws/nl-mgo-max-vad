from unittest.mock import MagicMock

import inject
import pytest
from pytest_mock import MockerFixture

from app.vad.config.schemas import (
    Config,
    AppConfig,
    PrsConfig,
    PrsRepositoryType,
    BrpConfig,
)
from app.vad.prs.repositories import PrsRepository, MockPrsRepository, ApiPrsRepository

TEST_CONFIG = Config(
    app=AppConfig(name="VAD"),
    prs=PrsConfig(
        prs_repository=PrsRepositoryType.MOCK,
        repo_base_url="localhost",
        organisation_id="test-org-id",
    ),
    brp=BrpConfig(mock_brp=True),
)


def test_bind_prs_repository_registers_mock(
    lazy_app,
    lazy_container,
    app_mode_default,
    vad_userinfo_service_config,
    mocker: MockerFixture,
) -> None:
    inject.clear()

    global TEST_CONFIG
    config = TEST_CONFIG.model_copy(deep=True)
    config.prs.prs_repository = PrsRepositoryType.MOCK

    mocker.patch("app.vad.bindings.__parse_app_config", return_value=config)

    _ = lazy_app.value

    assert inject.instance(PrsRepository).__class__ == MockPrsRepository


def test_bind_prs_repository_registers_api(
    lazy_app,
    lazy_container,
    app_mode_default,
    vad_userinfo_service_config,
    mocker: MockerFixture,
) -> None:
    inject.clear()

    global TEST_CONFIG
    config = TEST_CONFIG.model_copy(deep=True)
    config.prs.prs_repository = PrsRepositoryType.API

    mocker.patch("app.vad.bindings.__parse_app_config", return_value=config)

    _ = lazy_app.value

    assert inject.instance(PrsRepository).__class__ == ApiPrsRepository


def test_bind_prs_repository_raises_exception(
    lazy_app,
    lazy_container,
    app_mode_default,
    vad_userinfo_service_config,
    mocker: MockerFixture,
) -> None:
    inject.clear()

    global TEST_CONFIG
    config = TEST_CONFIG.model_copy(deep=True)
    mock_prs_repository_type = MagicMock(spec=PrsRepositoryType)
    mock_prs_repository_type.NOT_YET_IMPLEMENTED = "not_yet_implemented"
    config.prs.prs_repository = mock_prs_repository_type.NOT_YET_IMPLEMENTED

    mocker.patch("app.vad.bindings.__parse_app_config", return_value=config)

    """ Can't make this assertion any more specific due to the Lazy class catching the
    NotImplementedError and reraising a ValueError without passing the previous context """
    with pytest.raises(Exception):
        _ = lazy_app.value
