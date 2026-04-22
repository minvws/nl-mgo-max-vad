from fastapi.testclient import TestClient

from app.application import create_app
from app.config.schemas import VadConfig
from tests.utils import configure_bindings


class TestDocsRouter:
    def test_openapi_endpoint_available(self, config: VadConfig):
        config.app.version_file_path = "static/version.json.example"
        config.swagger.enabled = True
        config.swagger.openapi_endpoint = "/openapi.json"

        configure_bindings(config=config)

        test_client = TestClient(create_app(config))
        response = test_client.get("/openapi.json")

        assert response.status_code == 200
        assert response.json()["info"]["version"] == "v0.0.0"

    def test_openapi_endpoint_with_version(self, config: VadConfig):
        config.app.version_file_path = "tests/resources/version.json.example"
        config.swagger.enabled = True
        config.swagger.openapi_endpoint = "/openapi.json"

        configure_bindings(config=config)

        test_client = TestClient(create_app(config))
        response = test_client.get("/openapi.json")

        assert response.status_code == 200
        assert response.json()["info"]["version"] == "v1.2.3"

    def test_swagger_disabled(self, config: VadConfig):
        config.swagger.enabled = False
        config.swagger.redoc_endpoint = "/docs"
        config.swagger.openapi_endpoint = "/openapi.json"
        config.swagger.swagger_ui_endpoint = "/ui"

        configure_bindings(config=config)

        test_client = TestClient(create_app(config))
        response = test_client.get("/docs")
        assert response.status_code == 404

        response = test_client.get("/openapi.json")
        assert response.status_code == 404

        response = test_client.get("/ui")
        assert response.status_code == 404

    def test_openapi_endpoint_not_available_with_empty_endpoint(
        self, config: VadConfig
    ):
        config.swagger.enabled = True
        config.swagger.openapi_endpoint = ""

        configure_bindings(config=config)

        test_client = TestClient(create_app(config))
        response = test_client.get("/openapi.json")

        assert response.status_code == 404

    def test_swagger_ui_available(self, config: VadConfig):
        config.swagger.enabled = True
        config.swagger.swagger_ui_endpoint = "/ui"
        config.swagger.openapi_endpoint = "/openapi.json"

        configure_bindings(config=config)

        test_client = TestClient(create_app(config))
        response = test_client.get("/ui")

        assert response.status_code == 200

    def test_swagger_ui_not_available_with_empty_openapi_endpoint(
        self, config: VadConfig
    ):
        config.swagger.enabled = True
        config.swagger.swagger_ui_endpoint = "/ui"
        config.swagger.openapi_endpoint = ""

        configure_bindings(config=config)

        test_client = TestClient(create_app(config))
        response = test_client.get("/ui")

        assert response.status_code == 404

    def test_swagger_ui_not_available_with_empty_endpoint(self, config: VadConfig):
        config.swagger.enabled = True
        config.swagger.swagger_ui_endpoint = ""
        config.swagger.openapi_endpoint = "/openapi.json"

        configure_bindings(config=config)

        test_client = TestClient(create_app(config))
        response = test_client.get("/ui")

        assert response.status_code == 404

    def test_redoc_available(self, config: VadConfig):
        config.swagger.enabled = True
        config.swagger.redoc_endpoint = "/docs"
        config.swagger.openapi_endpoint = "/openapi.json"

        configure_bindings(config=config)

        test_client = TestClient(create_app(config))
        response = test_client.get("/docs")

        assert response.status_code == 200

    def test_redoc_not_available_with_empty_endpoint(self, config: VadConfig):
        config.swagger.enabled = True
        config.swagger.redoc_endpoint = ""
        config.swagger.openapi_endpoint = "/openapi.json"

        configure_bindings(config=config)

        test_client = TestClient(create_app(config))
        response = test_client.get("/docs")

        assert response.status_code == 404

    def test_redoc_not_available_with_empty_openapi_endpoint(self, config: VadConfig):
        config.swagger.enabled = True
        config.swagger.redoc_endpoint = "/docs"
        config.swagger.openapi_endpoint = ""

        configure_bindings(config=config)

        test_client = TestClient(create_app(config))
        response = test_client.get("/docs")

        assert response.status_code == 404
