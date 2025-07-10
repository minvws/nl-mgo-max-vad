from typing import Awaitable, Callable, Mapping, TypeAlias
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

CallableMiddleware: TypeAlias = Callable[[Scope, Receive, Send], Awaitable[None]]
CallableMiddlewareFactory: TypeAlias = Callable[[ASGIApp], CallableMiddleware]


class PathAwareCORSMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        default_middleware: CallableMiddlewareFactory,
        middleware_by_path: Mapping[str, CallableMiddlewareFactory],
    ) -> None:
        self.__app = app
        self.__default_middleware = default_middleware
        self.__middleware_by_path = middleware_by_path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.__app(scope, receive, send)
            return

        middleware = self.__middleware_by_path.get(
            scope["path"], self.__default_middleware
        )

        await middleware(self.__app)(scope, receive, send)
