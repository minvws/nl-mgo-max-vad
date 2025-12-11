# Hosting changelog

- [NEXT FUTURE RELEASE]

- [0.6.0]

  Changed:

  - Section `[redis]` changed to `[cache]`
  - All existing config keys for redis in this section must be prefixed with `redis_` (their values remain the same):
    - `host` -> `redis_host`
    - `port` -> `redis_port`
    - `enable_debugger` -> `redis_enable_debugger`
    - `ssl` -> `redis_ssl`
    - `key` -> `redis_key`
    - `cert` -> `redis_cert`
    - `cafile` -> `redis_cafile`
    - `default_cache_namespace` -> `redis_default_cache_namespace`
    - `token_namespace` -> `redis_token_namespace`
    - `refresh_token_namespace` -> `redis_refresh_token_namespace`
    - `subject_identifier_namespace` -> `redis_subject_identifier_namespace`
    - `code_namespace` -> `redis_code_namespace`

  Added:
  - The following setting is added to the `[cache]` section (previously `[redis]`):
    - `cache_driver = redis`

  - Section `[cbp]` added
    - key `string` `clients_sync_request_limit` added to limit the rate of requests to the CBP source
    - defaults to `10/second`
  
  - Section `[cbp_source]` added
    - key `type` `string` added to specify the type of source (e.g. `http`, `no-op`)
    - key `base_url` `string` added to specify the base URL for the HTTP source
    - key `timeout` `int` added to specify the timeout for requests (defaults to 30 seconds)

  - Section `[cbp_cache]` added
    - key `filepath` `string` added to specify the file path for caching CBP clients data

- [0.5.0]
  - Refactor: vad depends on package minvws/nl-irealisatie-max-core
  - vad.conf and max.conf are merged to app.conf

- [0.4.0]

  No changes required

- [0.3.0]

  No changes required

- [0.2.0]

  Added:

  - `auth_session`
    - cache_ttl_seconds: 910
      - string
    - cookie_expiry_offset_seconds: 10
      - string

- [0.1.0]

  Added:

  - `auth_session`
    - enabled
      - bool: True
    - secret_key
      - string: 32-byte (256-bit) symmetric key: generate one with: `openssl rand -hex 32`
