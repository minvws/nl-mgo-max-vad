# Auth Session Configuration

Configuration keys under the `[auth_session]` section control the behavior of [auth session feature](../features/auth_session.md).

## Configuration Keys

### `enabled`

- **Type**: Boolean
- **Purpose**: Flags whether the auth session feature is active.
- **Usage**: Set to `True` to enable session management, or `False` to disable it.

### `secret_key`

- **Type**: String (64 characters)
- **Purpose**: Encryption key used for securing the cookie value.
- **Usage**: Must be a 64-character hexadecimal string which can be generated with: `openssl rand -hex 32`.

### `cache_ttl_seconds`

- **Type**: Integer
- **Purpose**: Controls how long session data remains in cache
- **Note**: Should be slightly longer than the actual cookie expiry. The effective session duration is the value minus `cookie_expiry_offset_seconds`.

### `cookie_expiry_offset_seconds`

- **Type**: Integer
- **Default**: `10`
- **Purpose**: Substracts additional seconds from the cache TTL to ensure the cache remains valid longer than the cookie
