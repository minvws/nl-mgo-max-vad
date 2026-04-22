from logging import Logger

from app.cbp.models import CbpClient
from app.cbp.repositories import CbpClientRepository
from app.cbp.services import (
    CbpClientFactory,
    CbpClientFetcher,
    CbpHttpClient,
    CbpSource,
)
from faker import Faker
from pytest import fixture
from pytest_mock import MockerFixture
from requests import JSONDecodeError, Response

from tests.conftest import CreateCbpClient


class TestCbpClientFactory:
    def test_create_returns_cbp_client_with_only_cbp_client_args(
        self, faker: Faker
    ) -> None:
        args = {
            "id": faker.uuid4(),
            "redirect_uris": [faker.uri()],
            "client_secret": None,
            "active": faker.boolean(),
            "created_at": str(faker.date_time()),
            "updated_at": str(faker.date_time()),
        }

        result = CbpClientFactory.create(**args)

        assert isinstance(result, CbpClient)


class TestCbpHttpClient:
    @fixture
    def logger(self, mocker: MockerFixture) -> Logger:
        return mocker.Mock(spec=Logger)

    @fixture
    def sut(self, logger: Logger) -> CbpHttpClient:
        return CbpHttpClient(logger=logger, base_url="http://example.com")

    def test_get_clients_returns_cbp_clients(
        self,
        mocker: MockerFixture,
        faker: Faker,
        sut: CbpHttpClient,
    ) -> None:
        response = mocker.Mock(spec=Response)
        clients = [
            {
                "id": faker.uuid4(),
                "redirect_uris": [faker.uri()],
                "client_secret": None,
                "active": faker.boolean(),
                "created_at": str(faker.date_time()),
                "updated_at": str(faker.date_time()),
            }
            for _ in range(3)
        ]
        mocker.patch(
            "app.cbp.services.requests.get",
            return_value=response,
            autospec=True,
        )
        response.json.return_value = {"clients": clients}

        result = sut.get_clients()

        assert len(result) == 3

    def test_get_clients_empty_response_if_connection_fails(
        self,
        mocker: MockerFixture,
        sut: CbpHttpClient,
        logger: Logger,
    ) -> None:
        exception = ConnectionError("Connection refused")
        mocker.patch(
            "app.cbp.services.requests.get",
            side_effect=exception,
            autospec=True,
        )

        result = sut.get_clients()

        assert len(result) == 0
        logger.exception.assert_called_once_with(
            "Failed to connect to CBP", exc_info=exception
        )

    def test_get_clients_empty_response_if_no_json_response(
        self,
        mocker: MockerFixture,
        sut: CbpHttpClient,
        logger: Logger,
    ) -> None:
        response = mocker.Mock(spec=Response)
        exception = JSONDecodeError("Invalid JSON", "", 0)
        mocker.patch(
            "app.cbp.services.requests.get",
            return_value=response,
            autospec=True,
        )
        response.json.side_effect = exception

        result = sut.get_clients()

        assert len(result) == 0
        logger.exception.assert_called_once_with(
            "Failed to parse CBP response as JSON", exc_info=exception
        )
        logger.error.assert_called_once_with(
            "Missing 'clients' property in CBP response: %s", {}
        )

    def test_get_clients_empty_response_if_json_structure_is_invalid(
        self,
        mocker: MockerFixture,
        sut: CbpHttpClient,
        logger: Logger,
    ) -> None:
        response = mocker.Mock(spec=Response)
        json = {"invalid": "structure"}
        mocker.patch(
            "app.cbp.services.requests.get",
            return_value=response,
            autospec=True,
        )
        response.json.return_value = json

        result = sut.get_clients()

        assert len(result) == 0
        logger.error.assert_called_once_with(
            "Missing 'clients' property in CBP response: %s", json
        )

    def test_get_clients_empty_response_if_client_data_is_invalid(
        self,
        mocker: MockerFixture,
        faker: Faker,
        sut: CbpHttpClient,
        logger: Logger,
    ) -> None:
        response = mocker.Mock(spec=Response)
        json = {
            "clients": [
                {
                    "redirect_uris": [faker.uri()],
                    "client_secret": None,
                    "active": faker.boolean(),
                    "created_at": str(faker.date_time()),
                    "updated_at": str(faker.date_time()),
                }
            ]
        }
        mocker.patch(
            "app.cbp.services.requests.get",
            return_value=response,
            autospec=True,
        )
        response.json.return_value = json

        result = sut.get_clients()

        assert len(result) == 0
        logger.exception.assert_called_once()
        msg, kwargs = logger.exception.call_args
        assert msg[0] == "Failed to parse CBP client data"
        assert "exc_info" in kwargs
        assert isinstance(kwargs["exc_info"], ValueError)


class TestCbpClientFetcher:
    @fixture
    def cached_cbp_client_repository(
        self, mocker: MockerFixture
    ) -> CbpClientRepository:
        return mocker.Mock(spec=CbpClientRepository)

    @fixture
    def cbp_source(self, mocker: MockerFixture) -> CbpSource:
        return mocker.Mock(spec=CbpSource)

    @fixture
    def sut(
        self,
        cached_cbp_client_repository: CbpClientRepository,
        cbp_source: CbpSource,
        mocker: MockerFixture,
    ) -> CbpClientFetcher:
        return CbpClientFetcher(
            logger=mocker.Mock(spec=Logger),
            cached_cbp_client_repository=cached_cbp_client_repository,
            cbp_source=cbp_source,
        )

    def test_fetch_fetches_clients_from_cbp_if_cached_clients_is_empty(
        self,
        sut: CbpClientFetcher,
        cached_cbp_client_repository: CbpClientRepository,
        cbp_source: CbpSource,
        create_cbp_client: CreateCbpClient,
    ) -> None:
        clients = [create_cbp_client() for _ in range(2)]
        cbp_source.get_clients.return_value = clients
        cached_cbp_client_repository.get_all.return_value = []

        sut.fetch(use_cache=True)

        cached_cbp_client_repository.get_all.assert_called_once()
        cbp_source.get_clients.assert_called_once()
        cached_cbp_client_repository.update.assert_called_once_with(clients)

    def test_fetch_fetches_clients_from_cbp_if_use_cache_is_false(
        self,
        sut: CbpClientFetcher,
        cached_cbp_client_repository: CbpClientRepository,
        cbp_source: CbpSource,
        create_cbp_client: CreateCbpClient,
    ) -> None:
        clients = [create_cbp_client() for _ in range(2)]
        cbp_source.get_clients.return_value = clients

        sut.fetch(use_cache=False)

        cached_cbp_client_repository.get_all.assert_not_called()
        cbp_source.get_clients.assert_called_once()
        cached_cbp_client_repository.update.assert_called_once_with(clients)

    def test_fetch_is_idle_if_cached_clients_is_not_empty_and_use_cache_is_true(
        self,
        sut: CbpClientFetcher,
        cached_cbp_client_repository: CbpClientRepository,
        cbp_source: CbpSource,
        create_cbp_client: CreateCbpClient,
    ) -> None:
        clients = [create_cbp_client() for _ in range(2)]
        cached_cbp_client_repository.get_all.return_value = clients

        sut.fetch(use_cache=True)

        cached_cbp_client_repository.get_all.assert_called_once()
        cbp_source.get_clients.assert_not_called()
        cached_cbp_client_repository.update.assert_not_called()
