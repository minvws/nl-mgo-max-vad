# Hosting changelog

- NEXT FUTURE RELEASE

- [0.3.0] 2025-04-25

  No changes required

- [0.2.0] 2025-04-11

  Added:

  - `auth_session`
    - cache_ttl_seconds: 910
      - string
    - cookie_expiry_offset_seconds: 10
      - string

- [0.1.0] 2025-03-21

  Added:

  - `auth_session`
    - enabled
      - bool: True
    - secret_key
      - string: 32-byte (256-bit) symmetric key: generate one with: `openssl rand -hex 32`
