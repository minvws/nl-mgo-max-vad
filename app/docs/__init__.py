from fastapi import FastAPI
from inject import instance

from app.config.schemas import VadConfig

from .router import DocsRouter


def init_docs_module(app: FastAPI, config: VadConfig) -> None:
    if config.swagger.enabled:
        app.include_router(instance(DocsRouter))
