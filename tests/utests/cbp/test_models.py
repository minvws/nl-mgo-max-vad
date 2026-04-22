from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from jwcrypto.jwk import JWK

from app.cbp.models import CbpClient
from max_core.models.certificate_with_jwk import CertificateWithJWK

from tests.conftest import CreateCbpClient


class TestCbpClient:
    def test_certificate_serialization_and_restoration(
        self,
        create_cbp_client: CreateCbpClient,
        certificate_with_jwk: CertificateWithJWK,
    ):
        cbp_client = create_cbp_client(certificate=certificate_with_jwk)
        dumped = cbp_client.model_dump(mode="json")

        assert "certificate" not in dumped

        dumped_plus_certificate = dumped | {"certificate": certificate_with_jwk}
        restored = CbpClient.model_validate(dumped_plus_certificate)

        assert isinstance(restored.certificate, CertificateWithJWK)
        assert isinstance(restored.certificate.certificate, x509.Certificate)
        assert isinstance(restored.certificate.jwk, JWK)

    def test_certificate_restored_preserves_content(
        self,
        create_cbp_client: CreateCbpClient,
        certificate_with_jwk: CertificateWithJWK,
    ):
        cbp_client = create_cbp_client(certificate=certificate_with_jwk)
        dumped = cbp_client.model_dump(mode="json")
        restored = CbpClient.model_validate(
            dumped | {"certificate": certificate_with_jwk}
        )

        assert restored.certificate.kid == certificate_with_jwk.kid
        assert restored.certificate.x5t == certificate_with_jwk.x5t
        assert restored.certificate.pem == certificate_with_jwk.pem
        assert restored.certificate.certificate.public_bytes(
            serialization.Encoding.PEM
        ) == certificate_with_jwk.certificate.public_bytes(serialization.Encoding.PEM)
        assert restored.certificate.jwk.export(
            as_dict=True
        ) == certificate_with_jwk.jwk.export(as_dict=True)

    def test_certificate_preserves_object_identity(
        self,
        create_cbp_client: CreateCbpClient,
        certificate_with_jwk: CertificateWithJWK,
    ):
        cbp_client = create_cbp_client(certificate=certificate_with_jwk)
        assert cbp_client.certificate is certificate_with_jwk
