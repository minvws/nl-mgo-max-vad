#!/usr/bin/env bash

set -e

mkdir -p saml/tvs/metadata

if [[ ! -f "tests/resources/idp_metadata.xml" ]]; then
  echo "Fetching saml tvs idp metadata for tests"
  curl "https://pp2.toegang.overheid.nl/kvs/rd/metadata" --output tests/resources/idp_metadata.xml
fi
