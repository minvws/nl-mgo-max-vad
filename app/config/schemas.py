from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

from max_core.config.schemas import CoreConfig
from max_core.config.schemas import AppConfig as CoreAppConfig


class AppConfig(CoreAppConfig):
    version_file_path: str = Field(default="static/version.json")


class PrsRepositoryType(str, Enum):
    MOCK = "mock"
    API = "api"


class CbpSourceType(str, Enum):
    HTTP = "http"
    NOOP = "no-op"


class UvicornConfig(BaseModel):
    host: str
    port: int
    reload: bool = Field(default=False)
    workers: int = Field(default=1)
    use_ssl: bool = Field(default=False)
    base_dir: str | None = Field(default=None)
    cert_file: str | None = Field(default=None)
    key_file: str | None = Field(default=None)
    reload_includes: str | None = Field(default=None)


class PrsConfig(BaseModel):
    prs_repository: PrsRepositoryType
    repo_base_url: str | None = Field(default=None)
    organisation_id: str

    @model_validator(mode="after")
    def validate_repo_base_url_required(self) -> "PrsConfig":
        if self.prs_repository is PrsRepositoryType.API and not self.repo_base_url:
            raise ValueError("repo_base_url is required when prs_repository is 'api'")
        return self


class BrpConfig(BaseModel):
    mock_brp: bool = Field(default=False)
    base_url: str | None = Field(default=None)
    api_key: str | None = Field(default=None)


class CbpConfig(BaseModel):
    clients_sync_request_limit: str = Field(default="10/second")


class CbpHttpClientConfig(BaseModel):
    type: Literal[CbpSourceType.HTTP] = Field(default=CbpSourceType.HTTP)
    base_url: str
    timeout: int = Field(default=30)


class NoOpCbpSourceConfig(BaseModel):
    type: Literal[CbpSourceType.NOOP] = Field(default=CbpSourceType.NOOP)


class CbpFileCacheConfig(BaseModel):
    filepath: str

    @model_validator(mode="after")
    def validate_filepath(self) -> "CbpFileCacheConfig":
        if self.filepath == "":
            raise ValueError("'filepath' cannot be empty")

        return self


class SwaggerConfig(BaseModel):
    enabled: bool = Field(default=False)
    swagger_ui_endpoint: str | None = Field(default="/ui")
    redoc_endpoint: str | None = Field(default="/docs")
    openapi_endpoint: str | None = Field(default="/openapi.json")


class LoggingConfig(BaseModel):
    loglevel_default: str
    loglevel_app: str

    @field_validator("loglevel_default", "loglevel_app", mode="before")
    @classmethod
    def convert_loglevel_to_uppercase(cls, v: str) -> str:
        return v.upper()


class VadConfig(CoreConfig):
    app: AppConfig
    logging: LoggingConfig
    uvicorn: UvicornConfig
    prs: PrsConfig
    brp: BrpConfig
    cbp: CbpConfig = Field(default_factory=CbpConfig)
    cbp_source: CbpHttpClientConfig | NoOpCbpSourceConfig = Field(discriminator="type")
    cbp_cache: CbpFileCacheConfig
    swagger: SwaggerConfig = Field(default_factory=SwaggerConfig)
