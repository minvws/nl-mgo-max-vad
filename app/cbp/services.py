from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, Dict, Sequence

import requests
from inject import autoparams

from .factories import CbpClientFactory
from .models import CbpClient
from .repositories import CbpClientRepository


class CbpSource(ABC):
    @abstractmethod
    def get_clients(self) -> Sequence[CbpClient]: ...


class CbpHttpClient(CbpSource):
    @autoparams("logger")
    def __init__(self, logger: Logger, base_url: str, timeout_seconds: int = 30):
        self.__logger = logger
        self.__base_url = base_url
        self.__timeout_seconds = timeout_seconds

    def get_clients(self) -> Sequence[CbpClient]:
        json_response = self.__get("/clients")

        if "clients" not in json_response:
            self.__logger.error(
                "Missing 'clients' property in CBP response: %s", json_response
            )
            return []

        try:
            clients = [
                CbpClientFactory.create(**client_data)
                for client_data in json_response["clients"]
            ]
        except ValueError as e:
            self.__logger.exception("Failed to parse CBP client data", exc_info=e)
            return []

        return clients

    def __get(self, endpoint: str) -> Dict[str, Any]:
        try:
            response = requests.get(
                f"{self.__base_url}{endpoint}", timeout=self.__timeout_seconds
            )
            response.raise_for_status()
        except (ConnectionError, requests.RequestException) as e:
            self.__logger.exception("Failed to connect to CBP", exc_info=e)
            return {}

        try:
            json_response = response.json()
        except requests.JSONDecodeError as e:
            self.__logger.exception("Failed to parse CBP response as JSON", exc_info=e)
            return {}

        return json_response


class NoOpCbpSource(CbpSource):
    def get_clients(self) -> Sequence[CbpClient]:
        return []


class CbpClientFetcher:
    @autoparams()
    def __init__(
        self,
        logger: Logger,
        cached_cbp_client_repository: CbpClientRepository,
        cbp_source: CbpSource,
    ):
        super().__init__()

        self.__logger = logger
        self.__cached_client_repository = cached_cbp_client_repository
        self.__cbp_source = cbp_source

    def fetch(self, use_cache: bool) -> None:
        self.__logger.debug("Fetch CBP clients using cache: %s", use_cache)
        clients = self.__cached_client_repository.get_all() if use_cache else []

        if len(clients) == 0:
            self.__logger.debug("No cached clients; fetching clients from source")
            clients = self.__cbp_source.get_clients()

            self.__logger.debug("Caching fetched clients")
            self.__cached_client_repository.update(clients)
