from inject import Binder

from app.config.schemas import SwaggerConfig

from .router import DocsRouter


class DocsBindings:
    def __init__(self, swagger_config: SwaggerConfig) -> None:
        self.__swagger_config = swagger_config

    def __call__(self, binder: Binder) -> None:
        binder.bind_to_constructor(
            DocsRouter, lambda: DocsRouter(self.__swagger_config)
        )
