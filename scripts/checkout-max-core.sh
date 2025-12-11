#!/bin/bash
set -euo pipefail

TARGET=local-packages/nl-irealisatie-max-core
REPO="git@github.com:minvws/irealisatie-max-core.git"

# Use first CLI argument as branch, default to main
BRANCH="${1:-main}"

if [ ! -d "$TARGET/.git" ]; then
    echo "Cloning $REPO into $TARGET (branch: $BRANCH)..."
    git clone --branch "$BRANCH" "$REPO" "$TARGET"
else
    echo "Repository already exists."
fi
