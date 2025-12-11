from datetime import datetime
from typing import Any, Dict

from jwcrypto.jwk import JWK
from max_core.models.client import Client
from pydantic import field_serializer


class CbpClient(Client):
    client_secret: str | None
    active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("public_key")
    def serialize_pubkey(self, key: object) -> Dict[str, Any]:
        if not isinstance(key, JWK):
            return {}
        return key.export(as_dict=True, private_key=False)

    @field_serializer("created_at", "updated_at")
    def serialize_dates(self, date: datetime) -> str:
        return date.isoformat() if date else ""
