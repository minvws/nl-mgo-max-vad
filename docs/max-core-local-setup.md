# MAX Core local setup

This guide explains how to use a local
[MAX Core](https://github.com/minvws/irealisatie-max-core) copy within this
repository. Linking the package locally ensures that any change you make in MAX
Core is applied immediately in this project, without commiting to version
control.

In this guide, you will:

1. Clone the `irealisatie-max-core` repository into the root of this project on
   your host machine
2. Configure Poetry inside Docker to use the local checkout in editable mode

## 1. Clone max-core into the project root (host)

Run this from the root of this repository on your host machine:

```bash
scripts/checkout-max-core.sh
```

Notes:

- By default, this will clone into `./local-packages/nl-irealisatie-max-core`
  and check out the `main` branch.
- To use a different branch, pass it as the first argument, e.g.:

```bash
scripts/checkout-max-core.sh my-feature-branch
```

After running, you should have this structure:

```text
nl-mgo-max-vad-private/
  ...
  local-packages/nl-irealisatie-max-core/
```

## 2. Configure Poetry to use the local max-core (inside Docker)

Make sure the application is running by following the steps described in the
Installation chapter of the [README.md](../README.md#installation).

Run the following commands to configure the max-core package in editable mode:

```bash
docker compose exec app bash "scripts/setup-local-max-core.sh"
docker compose restart app
```

The restart is required to make Poetry's editable dependency take effect inside
the running container.
