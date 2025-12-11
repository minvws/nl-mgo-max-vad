from inject import Binder
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from slowapi import Limiter

from app.application import create_app
from app.cbp.services import CbpClientFetcher
from app.config.schemas import VadConfig
from tests.utils import configure_bindings


def test_rate_limit_exceeded(config: VadConfig, mocker: MockerFixture):
    config.cbp.clients_sync_request_limit = "1/hour"  # very low limit for testing

    cbp_client_fetcher = mocker.Mock(spec=CbpClientFetcher)

    def override_bindings(binder: Binder) -> None:
        binder.bind_to_constructor(
            Limiter,
            lambda: Limiter(key_func=lambda request: "test"),  # simple key for testing
        )
        binder.bind_to_constructor(CbpClientFetcher, lambda: cbp_client_fetcher)

    configure_bindings(config, override_bindings)

    test_client = TestClient(create_app(config))

    # First request should succeed
    response = test_client.post("/api/v1/clients-updated")
    assert response.status_code == 202

    # Second request immediately should hit the rate limit
    response = test_client.post("/api/v1/clients-updated")
    assert response.status_code == 429
    assert "Too many requests" in response.text
