#!/usr/bin/env bash

set -euo pipefail

SERVICE_NAME="datavis-api"
SERVICE_USER="datavis-api"
: "${SERVICE_CREATOR_DEPLOY_ROOT:?Controller must set SERVICE_CREATOR_DEPLOY_ROOT}"
: "${SERVICE_CREATOR_ENV_FILE:?Controller must set SERVICE_CREATOR_ENV_FILE}"

case "${1:-}" in
  ""|--reinstall) ;;
  *) echo "Usage: $0 [--reinstall]" >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { echo "Usage: $0 [--reinstall]" >&2; exit 2; }

set -a
# shellcheck disable=SC1090
source "$SERVICE_CREATOR_ENV_FILE"
set +a

PREPARED_RELEASE="${SERVICE_CREATOR_PREPARED_RELEASE:?Update adapter must set SERVICE_CREATOR_PREPARED_RELEASE}"
[[ -x "$PREPARED_RELEASE/venv/bin/$SERVICE_NAME" ]] || {
  echo "Error: prepared service runtime is missing: $PREPARED_RELEASE" >&2
  exit 1
}

# Replace the application's `initialize` command when first-time state creation
# requires more than the scaffold placeholder. It must preserve existing state
# unless --reinstall explicitly defines reviewed repository-specific behavior.
sudo --preserve-env -u "$SERVICE_USER" \
  "$PREPARED_RELEASE/venv/bin/$SERVICE_NAME" initialize
