from tests.utils import configure_bindings
from app.application import create_app
from app.application import kwargs_from_config, run, uvicorn_app_factory
from fastapi import FastAPI
from pytest_mock import MockerFixture

from app.config.schemas import UvicornConfig, VadConfig


def test_create_app_with_mocked_config_and_version(
    mocker: MockerFixture, config: VadConfig
) -> None:
    config.swagger.enabled = True

    mocker.patch("app.application._load_config_once", return_value=config)
    mocker.patch("app.application._load_version", return_value="1.2.3")

    app = create_app(config)
    assert isinstance(app, FastAPI)
    assert app.title == "max-vad"
    assert app.version == "1.2.3"
    assert app.openapi_url == "/openapi.json"


def test_create_app_with_swagger_disabled(
    mocker: MockerFixture, config: VadConfig
) -> None:
    config.swagger.enabled = False

    configure_bindings(config=config)

    mocker.patch("app.application._load_config_once", return_value=config)
    mocker.patch("app.application._load_version", return_value="9.9.9")

    app = create_app(config)
    assert app.version == "9.9.9"
    assert app.openapi_url is None


def test_kwargs_from_config_ssl():
    config = UvicornConfig(
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1,
        use_ssl=True,
        base_dir="/ssl",
        key_file="key.pem",
        cert_file="cert.pem",
        reload_includes="*.py *.conf",
    )
    kwargs = kwargs_from_config(config)
    assert kwargs["ssl_keyfile"] == "/ssl/key.pem"
    assert kwargs["ssl_certfile"] == "/ssl/cert.pem"
    assert kwargs["reload_includes"] == ["*.py", "*.conf"]


def test_kwargs_from_config_no_ssl():
    config = UvicornConfig(
        host="127.0.0.1",
        port=8080,
        reload=False,
        workers=2,
        use_ssl=False,
        base_dir=None,
        key_file=None,
        cert_file=None,
        reload_includes=None,
    )
    kwargs = kwargs_from_config(config)
    assert "ssl_keyfile" not in kwargs
    assert "ssl_certfile" not in kwargs
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 8080


def test_run_invokes_uvicorn(mocker, config: VadConfig) -> None:

    mocker.patch("app.application._load_config_once", return_value=config)
    uvicorn_run = mocker.patch("uvicorn.run")
    run()
    uvicorn_run.assert_called_once()


def test_uvicorn_app_factory_returns_app(mocker, config: VadConfig) -> None:

    mocker.patch("app.application._load_config_once", return_value=config)
    app = uvicorn_app_factory()
    assert isinstance(app, FastAPI)
