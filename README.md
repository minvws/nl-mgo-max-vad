# MGO VAD

## Table of Contents

## Disclaimer

This project and all associated code serve solely as documentation
and demonstration purposes to illustrate potential system
communication patterns and architectures.

This codebase:

- Is NOT intended for production use
- Does NOT represent a final specification
- Should NOT be considered feature-complete or secure
- May contain errors, omissions, or oversimplified implementations
- Has NOT been tested or hardened for real-world scenarios

The code examples are only meant to help understand concepts and demonstrate possibilities.

By using or referencing this code, you acknowledge that you do so at your own
risk and that the authors assume no liability for any consequences of its use.

**Flow:**

- [Definitions](#definitions)
- [Purpose](#purpose)
- [Features](#features)
- [External integrations](#external-integrations)
  - [PRS](#prs)
  - [BRP](#brp)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Run the application](#run-the-application)
  - [OpenAPI](#openapi)
- [Contributing](#contributing)
  - [Visual Studio Code](#visual-studio-code)
    - [Developing inside a Container](#developing-inside-a-container)
- [Documentation](#documentation)
- [Disclaimer](#disclaimer)
- [License](#license)
- [Security](#security)

## Definitions

| Abbreviation | Term                           | Description                                                                                                                                        |
| ------------ | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **VAD**      | Vertrouwde AuthenticatieDienst | Trusted Authentication Service. Used to describe the interconnected services that facilitate DigiD login, BRP data enrichment and Pseudonymization |
| **OIDC**     | OpenID Connect                 | An interoperable authentication protocol based on the OAuth 2.0 framework of specifications (IETF RFC 6749 and 6750)                               |
| **BSN**      | BurgerServiceNummer            | Dutch equivalent of a Social Security Number, assigned to every Dutch citizen.                                                                     |
| **PII**      | Personally Identifiable Info   | Information that can be used to identify a person                                                                                                  |
| **PDN**      | Pseudonym                      | A deterministic, organisation-specific pseudonym for PII                                                                                           |
| **BRP**      | BasisRegistratie Personen      | Dutch Personal Records Database. Contains information about Dutch citizens                                                                         |
| **PRS**      | Pseudonym Reference Service    | An exchange service facilitating interoperability between clients by providing RIDs and PDNs                                                       |
| **RID**      | Reference ID                   | A token that can be exchanged once for a PDN at PRS                                                                                                |

## Purpose

This application builds on the [MAX](https://github.com/minvws/nl-rdo-max/)
framework, extending its OpenID Connect authentication/authorization
functionality, mainly adding a userinfo provider that compiles authorization
context and PII to support the VAD authentication flow.

## Features

- It provides a means of authenticating VAD clients using the OIDC protocol
- It provides an authenticated client with userinfo consisting of a RID and PII
  retrieved from the BRP
- It provides an authenticated client with a short-lived session, allowing
  clients to skip authentication when a valid session is present

## External integrations

The MGO VAD integrates with several external systems. Below is a list of systems
specifically part of the VAD extension. Please refer to the
[MAX](https://github.com/minvws/nl-rdo-max/) documentation for more information
on external integrations as part of the MAX framework.

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

Again, for further in-depth details on the setup of the MAX framework, please
refer to the [MAX](https://github.com/minvws/nl-rdo-max/) documentation.

### Setup

To initialize the application, run:

```bash
make setup-remote
```

### Run the application

To run the application, execute:

```bash
make run-remote
```

The application is now running at http://localhost:8006

### OpenAPI

A browsable and executable version of the DVP Proxy API is located at:
http://localhost:8006/docs

## Contributing

### Visual Studio Code

This repository contains shared configuration files, which automates the setup
of your workspace.

The configuration files reside in the `./.vscode` folder.

VS Code will detect this folder automatically and will recommend that you
install several extensions. It is advised to install all of them, as it will be
a good starting point for this project.

#### Developing inside a Container

Once you have installed all the extensions, VS Code may detect a Dev Container
configuration file and, hence, ask you to reopen the folder to develop in a
container.

This feature is enabled by the Dev Container extension. It allows you to use a
container as a full-featured development environment, providing a better
development experience, including auto-completion, code navigation, and
debugging.

## Documentation

More detailed documentation is located in the [docs](./docs/) directory.

## Disclaimer

This project and all associated code serve solely as documentation
and demonstration purposes to illustrate potential system
communication patterns and architectures.

This codebase:

- Is NOT intended for production use
- Does NOT represent a final specification
- Should NOT be considered feature-complete or secure
- May contain errors, omissions, or oversimplified implementations
- Has NOT been tested or hardened for real-world scenarios

The code examples are only meant to help understand concepts and demonstrate possibilities.

By using or referencing this code, you acknowledge that you do so at your own
risk and that the authors assume no liability for any consequences of its use.

Please refer to [MAX](https://github.com/minvws/nl-rdo-max) for the most current version.

## License

This repository follows the
[REUSE Specification v3.2](https://reuse.software/spec-3.2/). The code is
available under the EUPL-1.2 license, but the fonts and images are not. Please
see [LICENSES/](./LICENSES), [REUSE.toml](./REUSE.toml) and the individual
`*.license` files (if any) for copyright and license information.

## Security

Please refer to [SECURITY.md](./SECURITY.md).
