import json
import secrets
from pathlib import Path

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from requests import Response

from max_core.exceptions.max_exceptions import InvalidClientException

from app.application import create_app
from app.config.schemas import CbpFileCacheConfig, CbpHttpClientConfig, VadConfig
from tests.conftest import CreateCbpClient
from tests.utils import configure_bindings


@pytest.fixture
def clients_cache_file(tmp_path: Path) -> Path:
    return tmp_path.joinpath("clients.json")


def test_authorize_with_unknown_client_fails(config: VadConfig, faker: Faker) -> None:
    unknown_client_id = "unknown"
    client = TestClient(create_app(config))

    with pytest.raises(InvalidClientException):
        client.get(
            config.oidc.authorize_endpoint,
            params={
                "client_id": unknown_client_id,
                "response_type": "code",
                "redirect_uri": "https://example.com",
                "scope": "openid",
                "state": secrets.token_urlsafe(32),
                "nonce": secrets.token_urlsafe(32),
                "code_challenge": faker.password(),
                "code_challenge_method": "S256",
            },
        )


def test_authorize_with_client_in_cache_succeeds(
    config: VadConfig,
    faker: Faker,
    clients_cache_file: Path,
    create_cbp_client: CreateCbpClient,
) -> None:
    cached_cbp_client = create_cbp_client()
    clients_cache_file.write_text(json.dumps([cached_cbp_client.model_dump()]))

    config.cbp_cache = CbpFileCacheConfig(filepath=str(clients_cache_file))
    configure_bindings(config)

    test_client = TestClient(create_app(config))
    response = test_client.get(
        config.oidc.authorize_endpoint,
        params={
            "client_id": cached_cbp_client.id,
            "response_type": cached_cbp_client.response_types[0],
            "redirect_uri": cached_cbp_client.redirect_uris[0],
            "scope": "openid",
            "state": secrets.token_urlsafe(32),
            "nonce": secrets.token_urlsafe(32),
            "code_challenge": faker.password(),
            "code_challenge_method": "S256",
        },
    )
    assert response.status_code == 200


def test_authorize_with_client_added_after_update_succeeds(
    config: VadConfig,
    faker: Faker,
    clients_cache_file: Path,
    mocker: MockerFixture,
    create_cbp_client: CreateCbpClient,
) -> None:
    new_client = create_cbp_client()
    cached_client = create_cbp_client()
    clients_cache_file.write_text(json.dumps([cached_client.model_dump()]))

    config.cbp_source = CbpHttpClientConfig(base_url="http://cbp.source")
    config.cbp_cache = CbpFileCacheConfig(filepath=str(clients_cache_file))

    cbp_clients_response_mock = mocker.Mock(spec=Response)
    mocker.patch(
        "app.cbp.services.requests.get",
        return_value=cbp_clients_response_mock,
        autospec=True,
    )
    cbp_clients_response_mock.json.return_value = {
        "clients": [
            {
                "id": cached_client.id,
                "redirect_uris": cached_client.redirect_uris,
                "client_secret": None,
                "active": faker.boolean(),
                "created_at": str(faker.date_time()),
                "updated_at": str(faker.date_time()),
            },
            {
                "id": new_client.id,
                "redirect_uris": new_client.redirect_uris,
                "client_secret": None,
                "active": faker.boolean(),
                "created_at": str(faker.date_time()),
                "updated_at": str(faker.date_time()),
            },
        ]
    }

    configure_bindings(config)
    test_client = TestClient(create_app(config))

    clients_updated_response = test_client.post("/api/v1/clients-updated")
    assert clients_updated_response.status_code == 202

    for client in [cached_client, new_client]:
        authorize_response = test_client.get(
            config.oidc.authorize_endpoint,
            params={
                "client_id": client.id,
                "response_type": client.response_types[0],
                "redirect_uri": client.redirect_uris[0],
                "scope": "openid",
                "state": secrets.token_urlsafe(32),
                "nonce": secrets.token_urlsafe(32),
                "code_challenge": faker.password(),
                "code_challenge_method": "S256",
            },
        )

        assert authorize_response.status_code == 200


def test_authorize_with_client_deleted_after_update_fails(
    config: VadConfig,
    faker: Faker,
    clients_cache_file: Path,
    mocker: MockerFixture,
    create_cbp_client: CreateCbpClient,
) -> None:
    client = create_cbp_client()
    deleted_client = create_cbp_client()
    clients_cache_file.write_text(json.dumps([deleted_client.model_dump()]))

    config.cbp_source = CbpHttpClientConfig(base_url="http://cbp.source")
    config.cbp_cache = CbpFileCacheConfig(filepath=str(clients_cache_file))

    cbp_clients_response_mock = mocker.Mock(spec=Response)
    mocker.patch(
        "app.cbp.services.requests.get",
        return_value=cbp_clients_response_mock,
        autospec=True,
    )
    cbp_clients_response_mock.json.return_value = {
        "clients": [
            {
                "id": client.id,
                "redirect_uris": client.redirect_uris,
                "client_secret": None,
                "active": faker.boolean(),
                "created_at": str(faker.date_time()),
                "updated_at": str(faker.date_time()),
            },
        ]
    }

    configure_bindings(config)
    test_client = TestClient(create_app(config))

    clients_updated_response = test_client.post("/api/v1/clients-updated")
    assert clients_updated_response.status_code == 202

    with pytest.raises(InvalidClientException):
        test_client.get(
            config.oidc.authorize_endpoint,
            params={
                "client_id": deleted_client.id,
                "response_type": deleted_client.response_types[0],
                "redirect_uri": deleted_client.redirect_uris[0],
                "scope": "openid",
                "state": secrets.token_urlsafe(32),
                "nonce": secrets.token_urlsafe(32),
                "code_challenge": faker.password(),
                "code_challenge_method": "S256",
            },
        )
