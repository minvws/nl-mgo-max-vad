from fastapi import FastAPI
import inject
import pytest

from typing import Generator
from fastapi.testclient import TestClient
from app.application import create_app
from app.config.schemas import VadConfig
from app.utils import load_config
from tests.utils import configure_bindings


@pytest.fixture()
def config() -> VadConfig:
    return load_config("tests/app.conf.test")


@pytest.fixture()
def app(config: VadConfig) -> FastAPI:
    return create_app(config)


@pytest.fixture()
def test_client(app: FastAPI) -> TestClient:
    configure_bindings()
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_bindings() -> Generator[None, None, None]:
    yield
    inject.clear()
