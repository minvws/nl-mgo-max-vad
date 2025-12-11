from logging import Logger

from fastapi import APIRouter, BackgroundTasks, Request, Response
from inject import autoparams
from slowapi import Limiter

from .services import CbpClientFetcher


class ClientsSyncRouter(APIRouter):
    @autoparams("fetcher", "limiter", "logger")
    def __init__(
        self,
        fetcher: CbpClientFetcher,
        limiter: Limiter,
        logger: Logger,
        request_limit: int,
    ):
        super().__init__(prefix="/api/v1", tags=["vad"])
        self.__fetcher = fetcher
        self.__limiter = limiter
        self.__logger = logger
        self.__request_limit = request_limit
        self._register_routes()

    def _register_routes(self):
        path = self.__limiter.limit(self.__request_limit)(self.clients_update)
        self.post(
            "/clients-updated",
            responses={
                202: {"description": "Successfully processed clients-updated"},
                429: {"description": "Too many requests"},
            },
        )(path)

    async def clients_update(  # pylint: disable=unused-argument
        self, request: Request, background_tasks: BackgroundTasks
    ) -> Response:
        # NOTE: `request` is required by slowapi for rate limiting, even though it is not used in this handler.
        self.__logger.info(
            "Queueing background task for updating local CBP clients cache."
        )
        background_tasks.add_task(self._fetch_cbp_clients)
        return Response(status_code=202)

    def _fetch_cbp_clients(self) -> None:
        self.__logger.info("Running background task for fetching CBP clients.")
        self.__fetcher.fetch(use_cache=False)
