from fastapi import APIRouter, Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
)
from fastapi.openapi.utils import get_openapi

from app.models.swagger_config import SwaggerConfig


class DocsRouter:
    _swagger_config: SwaggerConfig

    def __init__(self, swagger_config: SwaggerConfig, app: FastAPI):
        self._swagger_config = swagger_config
        self.app: FastAPI = app

    def get_docs_router(self) -> APIRouter:
        docs_router = APIRouter()

        if (
            self._swagger_config.swagger_ui_endpoint
            and self._swagger_config.openapi_endpoint
        ):
            docs_router.add_route(
                path=self._swagger_config.swagger_ui_endpoint,
                endpoint=self.custom_swagger_ui_html,
                include_in_schema=False,
            )

        if (
            self._swagger_config.redoc_endpoint
            and self._swagger_config.openapi_endpoint
        ):
            docs_router.add_route(
                path=self._swagger_config.redoc_endpoint,
                endpoint=self.redoc_html,
                include_in_schema=False,
            )

        @docs_router.get("/openapi-vad.json", include_in_schema=False)
        async def openapi_vad_json(request: Request):
            return JSONResponse(self.generate_openapi(self.app, request))

        return docs_router

    async def custom_swagger_ui_html(
        self,
        _request: Request,
    ):
        return get_swagger_ui_html(
            openapi_url=self._swagger_config.openapi_endpoint or "",
            title="Swagger UI",
            swagger_js_url="static/assets/swagger-ui-bundle.js",
            swagger_css_url="static/assets/swagger-ui.css",
            swagger_favicon_url="static/img/favicon.ico",
        )

    async def redoc_html(
        self,
        _request: Request,
    ):
        return get_redoc_html(
            openapi_url=self._swagger_config.openapi_endpoint or "",
            title="ReDoc",
            redoc_js_url="static/assets/redoc.standalone.js",
            redoc_favicon_url="static/img/favicon.ico",
            with_google_fonts=False,
        )

    def generate_openapi(self, app: FastAPI, request: Request):
        host_url = request.url.scheme + "://" + request.url.netloc
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=(
                "An OpenAPI schema definition for the MGO VAD API.\n\n"
                f"The specification can be requested in JSON format from:\n{host_url}/openapi-vad.json"
            ),
            routes=app.routes,
        )
        # Exclude specific endpoints
        paths_to_exclude = [
            "/",
            "/acs",
            "/metadata/{id_provider}",
            "/continue",
            "/json-schema.json",
            "/digid-mock",
            "/digid-mock-catch",
        ]
        openapi_schema["paths"] = {
            path: path_schema
            for path, path_schema in openapi_schema["paths"].items()
            if path not in paths_to_exclude
        }
        openapi_schema["servers"] = [{"url": host_url}]
        return openapi_schema
