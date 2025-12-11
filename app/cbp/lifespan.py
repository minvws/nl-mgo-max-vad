from contextlib import asynccontextmanager

import inject
from fastapi import FastAPI

from app.cbp.services import CbpClientFetcher


@asynccontextmanager
async def prefetch_cbp_clients(_: FastAPI):
    fetcher = inject.instance(CbpClientFetcher)
    fetcher.fetch(use_cache=True)

    yield
