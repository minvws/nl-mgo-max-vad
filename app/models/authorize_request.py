import json
import logging
from json import JSONDecodeError
from typing import Union, List, Optional

from fastapi import Query

from pydantic import BaseModel, field_validator, Field, ConfigDict

from app import constants
from app.models.response_type import ResponseType

from app.exceptions.max_exceptions import InvalidCodeChallengeMethodException

log = logging.getLogger(__package__)


class AuthorizeRequest(BaseModel):
    client_id: str = Field(..., description="Client identifier")
    redirect_uri: str = Query(
        ...,
        description="Redirect URI",
        examples=["https://client.example.com/callback"],
    )
    response_type: str = Field(..., description="Response type", examples=["code"])
    nonce: str = Field(..., description="Nonce parameter", title="Nonce")
    scope: str = Field(..., description="Scope")
    state: str = Field(..., description="State parameter")
    code_challenge: str
    code_challenge_method: str
    login_hint: Union[str, None] = None
    claims: Union[str, None] = None

    model_config = ConfigDict(
        title="AuthorizeRequest",
        json_schema_extra={
            "examples": [
                {
                    "client_id": "your-client-id",
                    "response_type": "code",
                    "redirect_uri": "https://client.example.com/callback",
                    "scope": "openid profile email",
                    "state": "random-state-string",
                    "nonce": "random-nonce-string",
                }
            ]
        },
    )

    @staticmethod
    def get_allowed_scopes():
        return ["openid", constants.SCOPE_AUTHORIZATION_BY_PROXY]

    @property
    def splitted_scopes(self):
        if isinstance(self.scope, str):
            return self.scope.split()
        raise TypeError(
            f"Expected 'scope' to be a string, got {type(self.scope).__name__}"
        )

    @property
    def login_hints(self):
        if self.login_hint is None:
            return []
        return self.login_hint.split(",")

    @property
    def acme_tokens(self) -> Optional[List[str]]:
        if self.claims is None:
            return None
        try:
            return json.loads(self.claims).get("acme_tokens", None)
        except (TypeError, JSONDecodeError):
            log.debug("Unable to load acme_tokens: %s", self.claims)
            return None

    @field_validator("scope")
    def validate_scopes(cls, scopes):  # pylint: disable=no-self-argument
        splitted_scopes = scopes.split()
        for scope in splitted_scopes:
            if scope not in cls.get_allowed_scopes():
                log.warning(
                    "Scope %s not allowed, only %s are supported",
                    scope,
                    cls.get_allowed_scopes(),
                )

        return scopes

    @field_validator("code_challenge_method")
    def validate_code_challenge_method(
        cls, code_challenge_method: str
    ):  # pylint: disable=no-self-argument
        if code_challenge_method != "S256":
            raise InvalidCodeChallengeMethodException()

        return code_challenge_method

    @property
    def authorization_by_proxy(self):
        return constants.SCOPE_AUTHORIZATION_BY_PROXY in self.splitted_scopes

    @field_validator("response_type")
    def validate_response_type(
        cls, response_type: str
    ):  # pylint: disable=no-self-argument
        response_types = ResponseType.list()
        if response_type not in response_types:
            log.warning(
                "response_code %s is not defined in defined response types %s",
                response_type,
                response_types,
            )
        return response_type
