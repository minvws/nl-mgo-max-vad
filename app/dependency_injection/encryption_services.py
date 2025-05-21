# pylint: disable=c-extension-no-member, too-few-public-methods

from dependency_injector import containers, providers

from app.services.encryption.jwe_service_provider import JweServiceProvider
from app.services.encryption.jwt_service_factory import JWTServiceFactory
from app.services.encryption.sym_encryption_service import SymEncryptionService
from app.services.encryption.url_safe_symmetric_encryptor import (
    UrlSafeSymmetricEncryptor,
)


class EncryptionServices(containers.DeclarativeContainer):
    config = providers.Configuration()

    user_authentication_encryption_service = providers.Singleton(
        SymEncryptionService,
        raw_local_sym_key=config.app.user_authentication_sym_key,
    )

    auth_session_encrypter = providers.Singleton(
        UrlSafeSymmetricEncryptor,
        raw_local_sym_key=config.auth_session.secret_key,
    )

    jwe_service_provider = providers.Singleton(
        JweServiceProvider,
        config=config.jwe,
    )

    jwt_service_factory = providers.Singleton(JWTServiceFactory)
