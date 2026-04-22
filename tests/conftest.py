from datetime import timezone
from typing import Any, Callable, Generator, TypeAlias

import inject
import pytest
from faker import Faker

from max_core.models.certificate_with_jwk import CertificateWithJWK
from max_core.models.enums import ClientAssertionMethods
from max_core.models.response_type import ResponseType

from app.cbp.factories import CertificateWithJWKFactory
from app.cbp.models import CbpClient
from app.config.schemas import VadConfig
from app.utils import load_config

CreateCbpClient: TypeAlias = Callable[..., CbpClient]


@pytest.fixture
def config() -> VadConfig:
    return load_config("tests/app.conf.test")


@pytest.fixture(name="faker")
def faker_fixture() -> Faker:
    return Faker()


@pytest.fixture(autouse=True)
def clear_bindings() -> Generator[None, None, None]:
    yield
    inject.clear()


@pytest.fixture
def create_cbp_client(
    faker: Faker,
    certificate_with_jwk: CertificateWithJWK,
) -> CreateCbpClient:
    def __callable(**kwargs: Any) -> CbpClient:
        defaults: dict[str, Any] = {
            "id": faker.unique.uuid4(),
            "name": faker.company(),
            "redirect_uris": [f"https://{faker.unique.domain_name()}/callback"],
            "response_types": [ResponseType.CODE],
            "token_endpoint_auth_method": faker.random_element(
                elements=("client_secret_post", "none")
            ),
            "client_authentication_method": ClientAssertionMethods.NONE,
            "login_methods": ["digid_mock"],
            "exclude_login_methods": [],
            "certificate": certificate_with_jwk,
            "client_secret": None,
            "active": True,
            "created_at": faker.date_time(tzinfo=timezone.utc),
            "updated_at": faker.date_time(tzinfo=timezone.utc),
        }

        properties = {**defaults, **kwargs}
        return CbpClient(**properties)

    return __callable


@pytest.fixture(name="certificate_with_jwk")
def certificate_with_jwk_fixture() -> CertificateWithJWK:
    return CertificateWithJWKFactory.create_dummy()
