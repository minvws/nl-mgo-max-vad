from fastapi import FastAPI
from inject import instance

from .router import DocsRouter


def init_docs_module(app: FastAPI) -> None:
    app.include_router(instance(DocsRouter))
