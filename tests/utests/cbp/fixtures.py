from app.cbp.models import CbpClient
from jwcrypto.jwk import JWK
from max_core.models.enums import ClientAssertionMethods
from max_core.models.response_type import ResponseType


def create_cbp_client(**overrides) -> CbpClient:
    properties = {
        "id": "test_client_internal_id",
        "name": "Test Client",
        "redirect_uris": ["https://client.local/callback"],
        "response_types": [ResponseType.CODE],
        "token_endpoint_auth_method": "none",
        "client_authentication_method": ClientAssertionMethods.NONE,
        "public_key": JWK.generate(kty="RSA", size=2048),
        "login_methods": ["digid_mock"],
        "exclude_login_methods": [],
        "client_secret": None,
        "active": True,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
    }
    properties.update(overrides)

    return CbpClient(**properties)
