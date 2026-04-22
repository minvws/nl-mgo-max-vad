from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import NameOID
from jwcrypto.jwk import JWK
from max_core.misc.utils import kid_from_certificate, load_certificate_with_jwk
from max_core.models.certificate_with_jwk import CertificateWithJWK
from max_core.models.enums import ClientAssertionMethods
from max_core.models.response_type import ResponseType

from .models import CbpClient


class CbpClientFactory:
    @staticmethod
    def create(**kwargs) -> CbpClient:
        token_endpoint_auth_method: str

        if "token_endpoint_auth_method" in kwargs:
            token_endpoint_auth_method = str(kwargs.get("token_endpoint_auth_method"))
        else:
            token_endpoint_auth_method = (
                "none"  # nosec B105 as this is NOT a password nor secret
            )

        kwargs.pop("token_endpoint_auth_method", None)

        return CbpClient(  # nosec
            name="Acme",
            response_types=[ResponseType.CODE],
            token_endpoint_auth_method=token_endpoint_auth_method,
            client_authentication_method=ClientAssertionMethods.NONE,
            certificate=CertificateWithJWKFactory.create_dummy(),
            login_methods=["digid_mock"],
            exclude_login_methods=[],
            **kwargs,
        )


class CertificateWithJWKFactory:
    @staticmethod
    def create_dummy() -> CertificateWithJWK:
        key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "NL"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Test State"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Test City"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Org"),
                x509.NameAttribute(NameOID.COMMON_NAME, "max.example.com"),
            ]
        )
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=10))
            .sign(key, algorithm=hashes.SHA256(), backend=default_backend())
        )

        private_jwk = JWK.from_pyca(key)
        private_jwk.update({"kid": kid_from_certificate(cert)})

        return load_certificate_with_jwk(cert)
