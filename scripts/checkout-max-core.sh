#!/bin/bash
set -euo pipefail

TARGET=local-packages/nl-irealisatie-max-core
REPO="git@github.com:minvws/irealisatie-max-core.git"

# Use first CLI argument as branch, default to main
BRANCH="${1:-main}"

echo "Preparing to clone $REPO into $TARGET (branch: $BRANCH)..."

if [ -d "$TARGET" ]; then
    read -p "Directory $TARGET already exists. Do you want to remove it? [y/N]: " CONFIRM
    case "$CONFIRM" in
        [yY][eE][sS]|[yY])
            echo "Removing existing directory $TARGET..."
            rm -rf "$TARGET"
            ;;
        *)
            echo "Aborting."
            exit 1
            ;;
    esac
fi

git clone --branch "$BRANCH" "$REPO" "$TARGET"
