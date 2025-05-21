import logging
from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from starlette.responses import JSONResponse

from app.constants import AUTH_SESSION_COOKIE
from app.dependency_injection.config import RouterConfig
from app.exceptions.max_exceptions import InvalidRequestException
from app.exceptions.oidc_exceptions import INVALID_REQUEST
from app.middlewares import active_auth_session
from app.models.auth_session import AuthSession
from app.models.authorize_request import AuthorizeRequest
from app.models.token_request import TokenRequest
from app.providers.oidc_provider import OIDCProvider
from app.vad.schemas import UserInfoDTO

oidc_router = APIRouter()

logger = logging.getLogger(__name__)


@oidc_router.get(
    "/.well-known/openid-configuration",
    summary="OpenID Connect Discovery endpoint",
    response_description="OpenID Discovery Configuration",
    tags=["OIDC"],
)
@inject
def well_known(
    oidc_provider: OIDCProvider = Depends(Provide["services.oidc_provider"]),
):
    """
    This endpoint follows the specification defined at http://openid.net/specs/openid-connect-discovery-1_0.html#ProviderMetadata.
    """
    return oidc_provider.well_known()


@oidc_router.get(
    RouterConfig.authorize_endpoint,
    summary="OIDC Authorization Endpoint",
    response_description="OIDC Authorization Response",
    tags=["OIDC"],
    responses={
        302: {"description": "A successful request will result in redirect response."},
        400: {
            "description": "A failed request will result in a 400 response.",
            "content": {
                "application/json": {
                    "example": {
                        "error": "invalid_request",
                        "error_description": "Invalid request",
                    }
                }
            },
        },
    },
)
@inject
def authorize(
    request: Request,
    authorize_request: AuthorizeRequest = Depends(),
    oidc_provider: OIDCProvider = Depends(Provide["services.oidc_provider"]),
    auth_session: Optional[AuthSession] = Depends(active_auth_session),
):
    """
    OIDC Authorization endpoint.

    Example:
    ```
    GET https://vad.test.mgo.irealisatie.nl/authorize?response_type=code\
&redirect_uri=<redirect_uri>\
&client_id=<your-client-id>\
&nonce=b22a20cc4b05d9c5cb4c2b688cdd20df&state=23d30cd64d9a43cb2cfd0675fbec4410\
&scope=openid&code_challenge=4A4C_IRNoTjNtHdb_-4COMSAaQwb2KwmhcK76r3Ecs4\
&code_challenge_method=S256
    ```

    See also:
      - [OAuth 2.0 Authorization Endpoint](http://tools.ietf.org/html/rfc6749#section-3.1)
      - [OIDC Authentication request](http://openid.net/specs/openid-connect-core-1_0.html#AuthRequest)
      - [OIDC Successful Authentication response](https://openid.net/specs/openid-connect-core-1_0.html#AuthResponse)
      - [OIDC Error Authentication response](http://openid.net/specs/openid-connect-core-1_0.html#AuthError)

    """
    response = oidc_provider.present_login_options_or_authorize(
        request=request,
        authorize_request=authorize_request,
        auth_session=auth_session,
    )

    if request.cookies.get(AUTH_SESSION_COOKIE) and not auth_session:
        response.delete_cookie(AUTH_SESSION_COOKIE)

    return response


@oidc_router.post(
    RouterConfig.accesstoken_endpoint,
    summary="OIDC Access Token Endpoint",
    tags=["OIDC"],
    openapi_extra={
        "requestBody": {
            "content": {
                "text/plain": {
                    "example": "grant_type=authorization_code&code=authorization-code&redirect_uri=https://your-redirect-uri.com/callback&client_id=your-client-id&client_secret=your-client-secret"
                }
            },
            "required": True,
        },
    },
    response_description="A success response that includes the issued token, expire and other details from the OAuth Server",
    responses={
        200: {
            "content": {
                "description": "A success response that includes the issued token, expire and other details from the OAuth Server",
                "application/json": {
                    "schema": {
                        "properties": {
                            "access_token": {
                                "type": "string",
                                "description": "The Access Token for the given token request",
                            },
                            "token_type": {
                                "type": "string",
                                "description": "The Token Type issued",
                                "examples": {"Bearer"},
                            },
                            "expires_in": {
                                "type": "string",
                                "description": "The expiry time, in seconds",
                                "examples": {"3600"},
                            },
                            "refresh_token": {
                                "type": "string",
                                "description": "The refresh token, if applicable",
                            },
                            "id_token": {
                                "type": "string",
                            },
                        },
                    }
                },
            }
        },
        400: {
            "description": "A failed request will result in a 400 response.",
            "content": {
                "application/json": {
                    "example": {
                        "error": "invalid_request",
                        "error_description": "Invalid request",
                    }
                }
            },
        },
    },
)
@inject
async def accesstoken(
    request: Request,
    oidc_provider: OIDCProvider = Depends(Provide["services.oidc_provider"]),
):
    """
    Exchange en authorization code for an Access Token.

    See also:
      - [OIDC Token Endpoint](https://openid.net/specs/openid-connect-core-1_0.html#TokenRequest)
      - [OIDC Successful Token response](http://openid.net/specs/openid-connect-core-1_0.html#TokenResponse)
      - [OIDC Token Error response](https://openid.net/specs/openid-connect-core-1_0.html#TokenErrorResponse)
    """
    try:
        return oidc_provider.token(
            TokenRequest.from_body_query_string((await request.body()).decode("utf-8")),
            request.headers,
        )

    except ValueError as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception


@oidc_router.get("/continue")
@inject
async def _continue(
    state: str,
    exchange_token: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    error_details: Optional[str] = None,
    oidc_provider: OIDCProvider = Depends(Provide["services.oidc_provider"]),
):
    if not error:
        if not exchange_token:
            raise InvalidRequestException(
                error=INVALID_REQUEST,
                error_description=INVALID_REQUEST,
                log_message=error_details,
            )
        return oidc_provider.authenticate_with_exchange_token(state, exchange_token)
    raise InvalidRequestException(
        error=error,
        error_description=error_description if error_description is not None else error,
        log_message=error_details,
    )


@oidc_router.get(
    RouterConfig.jwks_endpoint,
    summary="OIDC JWKS Endpoint",
    response_description="OIDC JWKS Response",
    tags=["OIDC"],
    responses={
        "200": {
            "description": "JWK set containing public keys that enable clients to validate a JSON Web Token (JWT) issued by this OIDC Provider",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "keys": {
                                "type": "array",
                                "items": {"type": "string"},
                                "examples": [
                                    {
                                        "kty": "RSA",
                                        "kid": "default_ssl_key",
                                        "use": "sig",
                                        "n": "58BezRBeYOM3rOo1vcllcLc8QAwz....h8Bkx-sVE2hu5S5x4_lADsPojLwWTT7or_sw9Q",
                                        "e": "AQAB",
                                    }
                                ],
                                "description": "JWK set in JSON array format",
                            }
                        },
                    }
                }
            },
        }
    },
)
@inject
async def jwks(
    oidc_provider: OIDCProvider = Depends(Provide["services.oidc_provider"]),
):
    """
    Get the JSON Web Key Set (JWKS).

    See also:
    http://openid.net/specs/openid-connect-discovery-1_0.html#ProviderMetadata
    """
    return oidc_provider.jwks()


@oidc_router.post(
    RouterConfig.userinfo_endpoint,
    summary="OIDC UserInfo Endpoint",
    response_description="OIDC UserInfo Response",
    response_model=UserInfoDTO,
    tags=["OIDC"],
)
@oidc_router.get(
    RouterConfig.userinfo_endpoint,
    summary="OIDC UserInfo Endpoint",
    response_description="OIDC UserInfo Response",
    response_model=UserInfoDTO,
    tags=["OIDC"],
)
@inject
def userinfo(
    request: Request,
    authorization_header: str = Header(  # pylint: disable=unused-argument
        description="An access_token of type Bearer.", alias="Authorization"
    ),
    oidc_provider: OIDCProvider = Depends(Provide["services.oidc_provider"]),
):
    """
    This endpoint returns user details and a reference pseudonyms.

    See also:
    http://openid.net/specs/openid-connect-core-1_0.html#UserInfo
    """
    return oidc_provider.userinfo(request)


@oidc_router.get("/json-schema.json")
@inject
def json_schema(
    schema_content: str = Depends(Provide["services.json_schema"]),
):
    return JSONResponse(content=schema_content)
