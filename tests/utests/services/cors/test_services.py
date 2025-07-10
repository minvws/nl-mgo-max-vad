import random
from typing import Mapping
from faker.proxy import Faker
from pytest import fixture, mark
from pytest_mock import AsyncMockType, MockerFixture
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Send

from app.services.cors.services import PathAwareCORSMiddleware


class TestPathAwareCORSMiddleware:
    @fixture
    def mock_app(self, mocker: MockerFixture) -> AsyncMockType:
        return mocker.AsyncMock(spec=ASGIApp)

    @fixture
    def mock_default_middleware(self, mocker: MockerFixture) -> AsyncMockType:
        return mocker.AsyncMock(spec=CORSMiddleware)

    @fixture
    def mock_middleware_by_path(
        self, mocker: MockerFixture, faker: Faker
    ) -> Mapping[str, AsyncMockType]:
        return {
            faker.uri_path(deep=3): mocker.AsyncMock(spec=CORSMiddleware),
            faker.uri_path(deep=3): mocker.AsyncMock(spec=CORSMiddleware),
            faker.uri_path(deep=3): mocker.AsyncMock(spec=CORSMiddleware),
        }

    @fixture
    def path_aware_cors_middleware(
        self,
        mock_app: ASGIApp,
        mock_default_middleware: AsyncMockType,
        mock_middleware_by_path: Mapping[str, AsyncMockType],
    ) -> PathAwareCORSMiddleware:
        def wrap_in_lambda(mock):
            return lambda *_: mock

        return PathAwareCORSMiddleware(
            app=mock_app,
            default_middleware=lambda *_: mock_default_middleware,
            middleware_by_path={
                path: wrap_in_lambda(mock)
                for path, mock in mock_middleware_by_path.items()
            },
        )

    @mark.asyncio
    async def test_it_is_idle_when_scope_is_not_http(
        self,
        mocker: MockerFixture,
        path_aware_cors_middleware: PathAwareCORSMiddleware,
        mock_app: AsyncMockType,
        mock_default_middleware: AsyncMockType,
        mock_middleware_by_path: Mapping[str, AsyncMockType],
    ) -> None:
        scope = {"type": "websocket"}
        receive = mocker.Mock(spec=Receive)
        send = mocker.Mock(spec=Send)

        await path_aware_cors_middleware(scope, receive, send)

        mock_app.assert_called_once_with(scope, receive, send)
        mock_default_middleware.assert_not_called()
        for mock_middleware in mock_middleware_by_path.values():
            mock_middleware.assert_not_called()

    @mark.asyncio
    async def test_it_executes_path_specific_cors_policy_if_requested_path_matches(
        self,
        mocker: MockerFixture,
        path_aware_cors_middleware: PathAwareCORSMiddleware,
        mock_app: AsyncMockType,
        mock_default_middleware: AsyncMockType,
        mock_middleware_by_path: Mapping[str, AsyncMockType],
    ):
        path_specific_middleware = random.choice(list(mock_middleware_by_path.items()))
        scope = {"type": "http", "path": path_specific_middleware[0]}
        receive = mocker.Mock(spec=Receive)
        send = mocker.Mock(spec=Send)

        await path_aware_cors_middleware(scope, receive, send)

        mock_app.assert_not_called()
        mock_default_middleware.assert_not_called()
        for path, mock_middleware in mock_middleware_by_path.items():
            if path_specific_middleware[0] != path:
                mock_middleware.assert_not_called()
            else:
                mock_middleware.assert_called_once()

    @mark.asyncio
    async def test_it_executes_default_cors_policy_if_requested_path_does_not_matches(
        self,
        mocker: MockerFixture,
        path_aware_cors_middleware: PathAwareCORSMiddleware,
        mock_app: AsyncMockType,
        mock_default_middleware: AsyncMockType,
        mock_middleware_by_path: Mapping[str, AsyncMockType],
        faker: Faker,
    ):
        scope = {"type": "http", "path": faker.uri_path(deep=2)}
        receive = mocker.Mock(spec=Receive)
        send = mocker.Mock(spec=Send)

        await path_aware_cors_middleware(scope, receive, send)

        mock_app.assert_not_called()
        mock_default_middleware.assert_called_once()
        for mock_middleware in mock_middleware_by_path.values():
            mock_middleware.assert_not_called()
        mock_default_middleware.assert_called_once_with(scope, receive, send)
