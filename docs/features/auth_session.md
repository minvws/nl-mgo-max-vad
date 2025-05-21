# Auth Session Feature

## Overview
The Auth Session feature is an optional component in the OpenID Connect (OIDC) authentication flow, designed to maintain a user's session once authenticated. This feature is useful when the OIDC authorization call is made multiple times in a short period, causing the user to re-verify their identity with an external authentication provider like DigiD. With the auth session enabled, an HTTP cookie is used to skip external authentication if the user has already authenticated during the session's lifetime.

## Configuration
See the [Auth Session Configuration page](../config/auth_session.md) for instructions on how to configure the behavior of the auth session feature.

## Flow and Process

1. **Initial OIDC Flow**: 
   - When a user completes the OIDC authentication flow, the application returns a cookie as part of the SAML Assertion Consumer Service (ACS) response.
   - This cookie is crucial for ensuring that subsequent requests by the user are associated with their authenticated session.

2. **Subsequent OIDC Authorize Call**:
   - On the next OIDC authorization request, the application checks for the presence of the cookie.
   - If the cookie is found and its corresponding data is available in the cache, the authorization flow skips the external authentication part at the configured authentication provider.
   - If the cookie is absent or invalid, the authorization flow proceeds as usual; the user will be redirected to the DigiD flow to reauthenticate.

3. **Cache Requirement**:
   - The application relies on an external application using MAX to use the **AuthSessionCache** class to store data related to the authentication session.
   - The cache serves as a crucial layer, holding the necessary data that corresponds to the session cookie.
   - **Encryption**: MAX encrypts any data stored in the cache, ensuring that even if the cache is compromised, the stored information remains secure.
   - If no cache data is available, the application will crash because the auth session cookie cannot be served.

## Authentication Cookie
- The authentication cookie contains a **random UUID**, which is encrypted using a symmetric key algorithm to ensure that there is no direct relationship between the cookie value and the cache key.
- This encryption ensures that even if the cookie is intercepted, no meaningful information can be derived from it.

## Session Renewal
- The application provides an endpoint to **renew the session duration** to prevent premature expiration.
    - This can be useful for unmanageable circumstances that might cause the session to expire, such as a situation where the user needs to manage permissions as part of the authentication flow.
- By calling this endpoint, the lifetime of both the cookie and cache will be extended with the same lifetime as initially used, starting from the moment the endpoint was hit.

## Key Points
- **OIDC Flow**: Ensures users do not need to complete an authentication flow at an external provider multiple times during the session.
- **Session Cookie**: Contains a random UUID, encrypted using a symmetric key, to avoid linking the cookie directly to the cache.
- **Cache Dependency**: The application depends on external applications to cache data related to the session cookie.
- **Cache Encryption**: MAX encrypts the data stored in the cache to protect sensitive session-related information.
- **Session Renewal**: MAX offers an endpoint to renew the session to prevent premature expiration.

## Conclusion
The Auth Session feature helps to provide a smoother and more seamless user experience by minimizing the need for repeated authentication while maintaining the security and integrity of the authentication flow.
