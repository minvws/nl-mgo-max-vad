# MGO VAD

## Table of Contents

- [Definitions](#definitions)
- [Purpose](#purpose)
- [Features](#features)
- [External integrations](#external-integrations)
  - [PRS](#prs)
  - [BRP](#brp)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
    - [Enable SSH agent forwarding](#enable-ssh-agent-forwarding)
  - [Run the application](#run-the-application)
  - [OpenAPI](#openapi)
- [Contributing](#contributing)
  - [Visual Studio Code](#visual-studio-code)
    - [Developing inside a Container](#developing-inside-a-container)
- [Documentation](#documentation)
- [Considerations](#considerations)
- [Disclaimer](#disclaimer)
- [License](#license)
- [Security](#security)

## Definitions

| Abbreviation | Term                             | Description                                                                                                                                         |
| ------------ | -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **VAD**      | Vertrouwde AuthenticatieDienst   | Trusted Authentication Service. Used to describe the interconnected services that facilitate DigiD login, BRP data enrichment and Pseudonymization. |
| **PGO**      | Persoonlijke Gezondheidsomgeving | An online application facilitating communication and exchange of information between Dutch citizens and healthcare providers.                       |
| **OIDC**     | OpenID Connect                   | An interoperable authentication protocol based on the OAuth 2.0 framework of specifications (IETF RFC 6749 and 6750).                               |
| **BSN**      | BurgerServiceNummer              | Dutch equivalent of a Social Security Number, assigned to every Dutch citizen.                                                                      |
| **PII**      | Personally Identifiable Info     | Information that can be used to identify a person.                                                                                                  |
| **PDN**      | Pseudonym                        | A deterministic, organisation-specific pseudonym for PII.                                                                                           |
| **BRP**      | BasisRegistratie Personen        | Dutch Personal Records Database. Contains information about Dutch citizens.                                                                         |
| **PRS**      | Pseudonym Reference Service      | An exchange service facilitating interoperability between clients by providing RIDs and PDNs.                                                       |
| **RID**      | Reference ID                     | A token that can be exchanged once for a PDN at PRS.                                                                                                |

## Purpose

In essence, the VAD (Vertrouwde AuthenticatieDienst) is an authorization server
and OpenID provider that builds on the
[MAX Core](https://github.com/minvws/irealisatie-max-core) framework, which is
based on the OpenID Connect protocol. Extending the ID Token part of the flow,
the VAD provides authenticated clients with end-user information and PRS issued
access tokens, in order for them to be able to request medical resources from
healthcare providers pertaining to that end-user. The VAD, as part of a broader
system for centralized authentication and authorization, aims to improve the
user-friendliness for all clients while maintaining high standards for security
and privacy.

## Features

- It provides a means of authenticating VAD clients using the OIDC protocol
- It provides an authenticated client with end-user information consisting of a
  RID and PII retrieved from the BRP (see
  [Override UserinfoService](./docs/override-userinfoservice.md) for more
  details)
- It provides an authenticated client with a short-lived session, allowing
  clients to skip authentication when a valid session is present

## External integrations

The VAD integrates with several external systems. The list below pertains to the
VAD domain specifically. Please refer to the
[MAX Core](https://github.com/minvws/irealisatie-max-core) documentation for
more information on external integrations as part of the MAX framework.

### PRS

The VAD requests the PRS API for both a VAD-specific PDN as well as a RID, the
latter being part of the userinfo data returned to the VAD client.

Note: this application currently only uses a mock implementation of the PRS API.

### BRP

The other part of the userinfo data is some PII which is retrieved from the BRP.
Since they provide a mock version of their API, the docker setup contains a BRP
mock service to better simulate the system integration.

## Installation

Follow the guide below to run this application on your local machine.

### Prerequisites

Please install the below programs if not present:

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Make](https://www.gnu.org/software/make/)

Again, for further in-depth details on the setup of the MAX Core framework,
please refer to the [MAX Core](https://github.com/minvws/irealisatie-max-core)
documentation.

### Setup

To initialize the application, run:

```bash
make setup-remote
```

#### Enable SSH agent forwarding

At this point, the MAX Core framework a git-type dependency, because is it not
yet available as a Python package. Installing this dependency in the Docker
environment requires a SSH key for authentication. To enable this scenario,
follow the steps below to automatically forward your local SSH agent if one is
running.

```sh
# Example:
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519   # or your key path
ssh-add -l                  # verify key is loaded
```

Note that on macOS, the above `eval` command is not needed. Just make sure to
add the key to your path, every time the host machine is restarted.

Further information can be found in the
[VS Code docs](https://code.visualstudio.com/remote/advancedcontainers/sharing-git-credentials).

### Run the application

To run the application, execute:

```bash
make run-remote
```

The application is now running at http://localhost:8006

### OpenAPI

A browsable and executable version of the VAD API is located at:
http://localhost:8006/docs

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Documentation

More detailed documentation is located in the [docs](./docs/) directory.

## Considerations

N.A.

## Disclaimer

This project and all associated code serve solely as documentation and
demonstration purposes to illustrate potential system communication patterns and
architectures.

This codebase:

- Is NOT intended for production use
- Does NOT represent a final specification
- Should NOT be considered feature-complete or secure
- May contain errors, omissions, or oversimplified implementations
- Has NOT been tested or hardened for real-world scenarios

The code examples are only meant to help understand concepts and demonstrate
possibilities.

By using or referencing this code, you acknowledge that you do so at your own
risk and that the authors assume no liability for any consequences of its use.

## License

This repository follows the
[REUSE Specification v3.2](https://reuse.software/spec-3.2/). The code is
available under the EUPL-1.2 license, but the fonts and images are not. Please
see [LICENSES/](./LICENSES), [REUSE.toml](./REUSE.toml) and the individual
`*.license` files (if any) for copyright and license information.

## Security

Please refer to [SECURITY.md](./SECURITY.md).
