#!/usr/bin/env bash
set -e

# Parent directory of this script
BASE_DIR="$(dirname "$(dirname "${BASH_SOURCE[0]}")")"

CACHE_DIR="${CACHE_DIR:-$BASE_DIR/cache}"
CBP_CACHE_DIR="${CBP_CACHE_DIR:-$CACHE_DIR/cbp}"

mkdir -pv "$CBP_CACHE_DIR"
