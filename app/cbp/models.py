from datetime import datetime

from max_core.models.certificate_with_jwk import CertificateWithJWK
from max_core.models.client import Client
from pydantic import Field, field_serializer


class CbpClient(Client):
    client_secret: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
    certificate: CertificateWithJWK = Field(exclude=True)

    @field_serializer("created_at", "updated_at")
    def serialize_dates(self, date: datetime) -> str:
        return date.isoformat() if date else ""
