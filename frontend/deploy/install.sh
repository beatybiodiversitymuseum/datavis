#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SERVICE_CREATOR_DEPLOY_ROOT:?Controller must set SERVICE_CREATOR_DEPLOY_ROOT}"

reinstall=0
case "${1:-}" in
  "") ;;
  --reinstall) reinstall=1 ;;
  *) echo "Usage: $0 [--reinstall]" >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { echo "Usage: $0 [--reinstall]" >&2; exit 2; }

LIFECYCLE_DIR="${SERVICE_CREATOR_DEPLOY_ROOT%/}/.service-creator"
INITIALIZED_MARKER="$LIFECYCLE_DIR/initialized"
if [[ -f "$INITIALIZED_MARKER" && "$reinstall" == 0 ]]; then
  exec "$SCRIPT_DIR/update.sh"
fi

install -d -m 0755 "$LIFECYCLE_DIR"
if [[ "$reinstall" == 1 ]]; then
  SERVICE_CREATOR_INITIALIZE_MODE=--reinstall "$SCRIPT_DIR/update.sh"
else
  SERVICE_CREATOR_INITIALIZE_MODE=initialize "$SCRIPT_DIR/update.sh"
fi
marker_temp="$(mktemp "$LIFECYCLE_DIR/.initialized.XXXXXX")"
trap 'rm -f -- "$marker_temp"' EXIT
printf 'initialized\n' >"$marker_temp"
chmod 0644 "$marker_temp"
mv -f -- "$marker_temp" "$INITIALIZED_MARKER"
trap - EXIT
echo "Initialization complete."
