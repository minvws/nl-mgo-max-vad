import pytest

from pydantic import ValidationError
from max_core.config.schemas import AppConfig


from app.config.schemas import (
    BrpConfig,
    PrsConfig,
    PrsRepositoryType,
    VadConfig,
)


def test_it_throws_error_on_invalid_config() -> None:
    with pytest.raises(ValidationError):
        VadConfig(
            app=AppConfig(name="VAD"),
            prs=PrsConfig(
                prs_repository=PrsRepositoryType.MOCK,
                repo_base_url="http://localhost:8000",
                organisation_id="123456789",
            ),
            brp=BrpConfig(mock_brp=True),
        )


@pytest.mark.parametrize(
    "base_url, expected_error",
    [
        ("", "repo_base_url is required when prs_repository is 'api'"),
    ],
)
def test_it_requires_base_url_when_using_prs_api_repo(
    base_url: str, expected_error: str
) -> None:
    with pytest.raises(ValidationError) as e:
        PrsConfig(
            prs_repository=PrsRepositoryType.API,
            repo_base_url=base_url,
            organisation_id="123456789",
        )

    assert expected_error in str(e.value)
