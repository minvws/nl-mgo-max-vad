#!/bin/bash
set -euo pipefail

MAX_CORE_PACKAGE="nl-irealisatie-max-core"
MAX_CORE_TARGET_PATH="/src/local-packages/nl-irealisatie-max-core"

# Show usage/help if requested
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    echo "Usage: $0"
    echo
    echo "This script configures '$MAX_CORE_PACKAGE' as a local editable dependency."
    echo "It expects the local repository to be mounted at '$MAX_CORE_TARGET_PATH'."
    exit 0
fi

if [ ! -d "$MAX_CORE_TARGET_PATH" ]; then
    echo "Path '$MAX_CORE_TARGET_PATH' does not exist. Please mount it correctly."
    exit 1
fi

echo "Configuring $MAX_CORE_PACKAGE from $MAX_CORE_TARGET_PATH"

poetry add --editable "$MAX_CORE_TARGET_PATH"

echo "$MAX_CORE_PACKAGE is now linked as a local editable dependency"
