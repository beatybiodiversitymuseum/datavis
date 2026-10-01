#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPONENT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ARTIFACT="$COMPONENT_ROOT/.deploy-artifact"
TEMP_ARTIFACT="$(mktemp -d "$COMPONENT_ROOT/.deploy-artifact.new.XXXXXX")"
cleanup() { rm -rf -- "$TEMP_ARTIFACT"; }
trap cleanup EXIT

install -d "$TEMP_ARTIFACT/wheelhouse" "$TEMP_ARTIFACT/systemd" \
  "$TEMP_ARTIFACT/config"
python3 -m pip wheel --no-deps --wheel-dir "$TEMP_ARTIFACT/wheelhouse" \
  "$COMPONENT_ROOT"
python3 -m pip wheel --no-deps --wheel-dir "$TEMP_ARTIFACT/wheelhouse" \
  'specify-client @ git+https://github.com/beatybiodiversitymuseum/specify-client.git@v0.6.0'

grep -Ev '^specify-client==' "$COMPONENT_ROOT/runtime-requirements.lock" \
  >"$TEMP_ARTIFACT/public-requirements.lock"
for python_version in 311 312 313; do
  python3 -m pip download --only-binary=:all: \
    --dest "$TEMP_ARTIFACT/wheelhouse" \
    --platform manylinux2014_x86_64 --implementation cp \
    --python-version "$python_version" --abi "cp$python_version" \
    --requirement "$TEMP_ARTIFACT/public-requirements.lock"
done

install -m 0644 "$COMPONENT_ROOT/runtime-requirements.lock" \
  "$TEMP_ARTIFACT/runtime-requirements.lock"
install -m 0644 "$COMPONENT_ROOT/deploy/"*.service \
  "$COMPONENT_ROOT/deploy/"*.timer "$TEMP_ARTIFACT/systemd/"
install -m 0644 "$COMPONENT_ROOT/config/datasets.yaml" \
  "$COMPONENT_ROOT/config/specify.yaml" "$TEMP_ARTIFACT/config/"
rm -f "$TEMP_ARTIFACT/public-requirements.lock"

rm -rf -- "$ARTIFACT"
mv "$TEMP_ARTIFACT" "$ARTIFACT"
trap - EXIT
