import json
from pathlib import Path

from fastapi.testclient import TestClient
from faker import Faker
from pytest_mock import MockerFixture, MockType
from requests import Response

from app.application import create_app
from app.config.schemas import CbpFileCacheConfig, CbpHttpClientConfig, VadConfig
from tests.utils import configure_bindings


def _set_mock_response(
    response: MockType,
    count: int,
    faker: Faker,
) -> None:
    clients = [
        {
            "id": faker.uuid4(),
            "redirect_uris": [faker.uri()],
            "client_secret": None,
            "active": faker.boolean(),
            "created_at": str(faker.date_time()),
            "updated_at": str(faker.date_time()),
        }
        for _ in range(count)
    ]
    response.json.return_value = {"clients": clients}


def test_clients_update_triggers_async_fetch_from_source(
    mocker: MockerFixture,
    faker: Faker,
    tmp_path: Path,
    config: VadConfig,
) -> None:
    response = mocker.Mock(spec=Response)
    mocker.patch("app.cbp.services.requests.get", return_value=response, autospec=True)
    cbp_clients_cache_filepath = tmp_path.joinpath("cbp_clients.json")

    config.cbp_source = CbpHttpClientConfig(base_url="http://cbp.source")
    config.cbp_cache = CbpFileCacheConfig(filepath=str(cbp_clients_cache_filepath))

    configure_bindings(config=config)

    _set_mock_response(response, 3, faker)

    with TestClient(create_app(config)) as test_client:
        with cbp_clients_cache_filepath.open("r", encoding="utf-8") as cache_file:
            cached_clients = json.load(cache_file)

        # Verify that on application boot 3 clients were fetched from the source and cached
        assert len(cached_clients) == 3

        _set_mock_response(response, 5, faker)
        response = test_client.post("/api/v1/clients-updated")

        assert response.status_code == 202

        with cbp_clients_cache_filepath.open("r", encoding="utf-8") as cache_file:
            cached_clients = json.load(cache_file)

        # Verify that upon invoking the webhook 5 clients were fetched from the source and cached
        assert len(cached_clients) == 5
