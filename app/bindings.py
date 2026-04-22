from logging import Logger, getLogger
from jwkest.jwk import RSAKey, import_rsa_key
from inject import Binder

from max_core.bindings import MaxCoreBindings
from max_core.providers.oidc_provider import OIDCProvider
from max_core.providers.saml_provider import SAMLProvider
from max_core.misc.utils import (
    as_list,
    file_content_raise_if_none,
    kid_from_certificate,
    read_cert_as_x509_certificate,
)
from max_core.providers.pyop_provider import MaxPyopProvider
from max_core.services.encryption.jwt_service import JWT_ALG

from .providers.oidc_provider import OIDCProvider as OIDCProviderOverride
from .providers.saml_provider import SAMLProvider as SAMLProviderOverride

from .brp.bindings import BrpBindings
from .cbp.bindings import CbpBindings
from .config.schemas import VadConfig
from .docs.bindings import DocsBindings
from .prs.bindings import PrsBindings
from .pyop.models import EmptyUserinfo
from .userinfo.bindings import UserinfoBindings


class ProviderOverrideBindings:
    """
    Temporary override of provider bindings to ensure consistent `sub` claims
    across the OIDC flow.

    This class performs the following temporary overrides:

    1. SAMLProvider:
       - Ensures that a `sub` is generated from a user's BSN.
       - Passes this `sub` to the UserinfoService so that it is returned as part
         of the userinfo response.

    2. OIDCProvider:
       - Retrieves the `user_id` generated in the SAMLProvider from cache.
       - Ensures that the same `sub` can be returned in the userinfo response
         during an active authentication session.

    3. MaxPyopProvider:
       - Injects a custom `EmptyUserinfo` implementation so that PyOP can generate
         and reuse a single `sub` value consistently.

    Note: This is a temporary workaround and should be replaced once we can fetch
    a reasonable user identifier from PRS.
    """

    def __init__(self, config: VadConfig) -> None:
        self.__config = config

    def __call__(self, binder: Binder) -> None:
        binder.bind_to_constructor(
            OIDCProvider,
            lambda: OIDCProviderOverride(  # pylint: disable=no-value-for-parameter
                environment=self.__config.app.environment,
                external_base_url=self.__config.app.external_base_url,
                login_options_sidebar_template=self.__config.templates.login_options_sidebar_template,
                allow_wildcard_redirect_uri=self.__config.oidc.allow_wildcard_redirect_uri,
            ),
        )
        binder.bind_to_constructor(
            SAMLProvider,
            lambda: SAMLProviderOverride(  # pylint: disable=no-value-for-parameter
                environment=self.__config.app.environment.lower(),
            ),
        )

        def __get_pyop_config_info() -> dict:
            issuer = self.__config.oidc.issuer
            authorize_endpoint = self.__config.oidc.authorize_endpoint
            jwks_endpoint = self.__config.oidc.jwks_endpoint
            token_endpoint = self.__config.oidc.accesstoken_endpoint
            userinfo_endpoint = self.__config.oidc.userinfo_endpoint
            scopes_supported = as_list(self.__config.oidc.scopes_supported)

            return {
                "issuer": issuer,
                "authorization_endpoint": issuer + authorize_endpoint,
                "jwks_uri": issuer + jwks_endpoint,
                "token_endpoint": issuer + token_endpoint,
                "scopes_supported": scopes_supported,
                "response_types_supported": ["code"],
                "response_modes_supported": ["query"],
                "grant_types_supported": ["authorization_code"],
                "subject_types_supported": ["pairwise"],
                "token_endpoint_auth_methods_supported": ["none", "private_key_jwt"],
                "claims_parameter_supported": True,
                "userinfo_endpoint": issuer + userinfo_endpoint,
            }

        def __create_pyop_rsa_signing_key() -> RSAKey:
            signing_key = file_content_raise_if_none(self.__config.oidc.rsa_private_key)
            signing_key_crt = read_cert_as_x509_certificate(
                self.__config.oidc.rsa_private_key_crt
            )
            kid = kid_from_certificate(signing_key_crt)
            key = RSAKey(key=import_rsa_key(signing_key), alg=JWT_ALG)
            key.kid = kid
            return key

        config_info_dict = __get_pyop_config_info()
        pyop_rsa_signing_key = __create_pyop_rsa_signing_key()

        binder.bind_to_constructor(
            MaxPyopProvider,
            lambda: MaxPyopProvider(  # pylint: disable=no-value-for-parameter
                userinfo=EmptyUserinfo(),
                id_token_lifetime=self.__config.cache.object_ttl,
                trusted_certificates_directory=self.__config.oidc.certificates_directory,
                configuration_information=config_info_dict,
                signing_key=pyop_rsa_signing_key,
            ),
        )


class AppBindings:
    def __init__(self, config: VadConfig) -> None:
        self.__config = config

    def __call__(self, binder: Binder) -> None:
        binder.install(MaxCoreBindings(self.__config))
        binder.install(ProviderOverrideBindings(self.__config))

        binder.bind(Logger, getLogger(__package__))
        binder.install(DocsBindings(self.__config.swagger))
        binder.install(PrsBindings(self.__config.prs))
        binder.install(BrpBindings(self.__config.brp))
        binder.install(CbpBindings(self.__config))
        binder.install(UserinfoBindings())
