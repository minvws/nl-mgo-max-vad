from inject import Binder
from slowapi import Limiter
from slowapi.util import get_remote_address

from max_core.services.client_repository import ClientRepository

from app.config.schemas import CbpSourceType, VadConfig

from .repositories import (
    CbpClientRepository,
    FilesystemCbpClientRepository,
)
from .router import ClientsSyncRouter
from .services import CbpHttpClient, CbpSource, NoOpCbpSource


class CbpBindings:
    def __init__(self, config: VadConfig) -> None:
        self.__config = config

    def __call__(self, binder: Binder) -> None:
        self.__bindings_for_webhook(binder)
        self.__bindings_for_clients(binder)

    def __bindings_for_webhook(self, binder: Binder) -> None:
        binder.bind_to_constructor(
            Limiter,
            lambda: Limiter(key_func=get_remote_address),
        )
        binder.bind_to_constructor(
            ClientsSyncRouter,
            lambda: ClientsSyncRouter(  # pylint: disable=no-value-for-parameter
                request_limit=self.__config.cbp.clients_sync_request_limit,
            ),
        )

    def __bindings_for_clients(self, binder: Binder) -> None:
        binder.bind_to_constructor(
            CbpSource,
            lambda: (
                CbpHttpClient(  # pylint: disable=no-value-for-parameter
                    base_url=self.__config.cbp_source.base_url,
                    timeout_seconds=self.__config.cbp_source.timeout,
                )
                if self.__config.cbp_source.type == CbpSourceType.HTTP
                else NoOpCbpSource()
            ),
        )

        client_repository = None

        def get_client_repository():
            nonlocal client_repository

            if client_repository is None:
                client_repository = FilesystemCbpClientRepository(
                    filepath=self.__config.cbp_cache.filepath
                )

            return client_repository

        binder.bind_to_constructor(ClientRepository, get_client_repository)
        binder.bind_to_constructor(CbpClientRepository, get_client_repository)
