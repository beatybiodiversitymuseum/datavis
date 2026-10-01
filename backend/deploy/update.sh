#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="datavis-api"
SERVICE_USER="datavis-api"
STATE_DIR="/var/lib/datavis-api"
: "${SERVICE_CREATOR_RELEASE_ID:?Controller must set SERVICE_CREATOR_RELEASE_ID}"
: "${SERVICE_CREATOR_ARTIFACT_SHA256:?Controller must set SERVICE_CREATOR_ARTIFACT_SHA256}"
: "${SERVICE_CREATOR_ARTIFACT_DIR:?Controller must set SERVICE_CREATOR_ARTIFACT_DIR}"
: "${SERVICE_CREATOR_ENV_FILE:?Controller must set SERVICE_CREATOR_ENV_FILE}"
: "${SERVICE_CREATOR_DEPLOY_ROOT:?Controller must set SERVICE_CREATOR_DEPLOY_ROOT}"

DEPLOY_ROOT="$SERVICE_CREATOR_DEPLOY_ROOT"
RELEASE_ID="$SERVICE_CREATOR_RELEASE_ID"
ARTIFACT_DIR="$SERVICE_CREATOR_ARTIFACT_DIR"
ENVIRONMENT_FILE="$SERVICE_CREATOR_ENV_FILE"
RELEASES_DIR="$DEPLOY_ROOT/releases"
RELEASE_PATH="$RELEASES_DIR/$RELEASE_ID"
CURRENT_LINK="$DEPLOY_ROOT/current"
CONFIG_DIR="$(dirname "$ENVIRONMENT_FILE")"

[[ "$RELEASE_ID" =~ ^[A-Za-z0-9._-]+$ ]] || {
  echo "Error: invalid release ID: $RELEASE_ID" >&2
  exit 2
}
[[ -d "$ARTIFACT_DIR/wheelhouse" ]] || {
  echo "Error: controller artifact is missing the backend wheelhouse." >&2
  exit 1
}
[[ -s "$ARTIFACT_DIR/runtime-requirements.lock" ]] || {
  echo "Error: runtime-requirements.lock is missing or empty." >&2
  exit 1
}
if grep -Ev '^[[:space:]]*(#.*|$|[A-Za-z0-9_.-]+==[^[:space:]]+([[:space:]]*;.*)?)$' \
  "$ARTIFACT_DIR/runtime-requirements.lock" >/dev/null; then
  echo "Error: runtime-requirements.lock contains a non-exact requirement." >&2
  exit 1
fi
[[ -f "$ENVIRONMENT_FILE" ]] || {
  echo "Error: controller-managed environment is missing: $ENVIRONMENT_FILE" >&2
  exit 1
}

sudo id "$SERVICE_USER" >/dev/null 2>&1 ||
  sudo useradd --system --home "$STATE_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
install -d -m 0755 "$RELEASES_DIR"
sudo install -d -m 0755 "$CONFIG_DIR"
sudo install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 "$STATE_DIR"

if [[ -e "$RELEASE_PATH" ]]; then
  if [[ ! -f "$RELEASE_PATH/release.env" ]] \
    || ! grep -Fqx "ARTIFACT_SHA256=$SERVICE_CREATOR_ARTIFACT_SHA256" \
      "$RELEASE_PATH/release.env"; then
    echo "Error: immutable release collision: $RELEASE_PATH" >&2
    exit 1
  fi
else
  install -d -m 0755 "$RELEASE_PATH"
  cleanup() { rm -rf -- "$RELEASE_PATH"; }
  trap cleanup EXIT
  install -d -m 0755 "$RELEASE_PATH/app/config" "$RELEASE_PATH/wheelhouse" \
    "$RELEASE_PATH/systemd" "$RELEASE_PATH/.service-creator"
  rsync -a --delete "$ARTIFACT_DIR/config/" "$RELEASE_PATH/app/config/"
  rsync -a --delete "$ARTIFACT_DIR/wheelhouse/" "$RELEASE_PATH/wheelhouse/"
  rsync -a --delete "$ARTIFACT_DIR/systemd/" "$RELEASE_PATH/systemd/"
  install -m 0644 "$ARTIFACT_DIR/runtime-requirements.lock" \
    "$RELEASE_PATH/runtime-requirements.lock"
  install -m 0755 "$SCRIPT_DIR/readiness.sh" "$RELEASE_PATH/.service-creator/readiness"
  python3 -m venv "$RELEASE_PATH/venv"
  "$RELEASE_PATH/venv/bin/python" -m pip install --no-index \
    --find-links "$RELEASE_PATH/wheelhouse" \
    --requirement "$RELEASE_PATH/runtime-requirements.lock"
  "$RELEASE_PATH/venv/bin/python" -m pip install --no-index --no-deps \
    "$RELEASE_PATH"/wheelhouse/datavis_api-*.whl
  printf 'RELEASE_ID=%s\nARTIFACT_SHA256=%s\nREPOSITORY=%s\n' \
    "$RELEASE_ID" "$SERVICE_CREATOR_ARTIFACT_SHA256" \
    "${SERVICE_CREATOR_REPOSITORY:-unknown}" |
    tee "$RELEASE_PATH/release.env" >/dev/null
  chmod 0444 "$RELEASE_PATH/release.env"
  chmod 0755 "$RELEASE_PATH" "$RELEASE_PATH/app" "$RELEASE_PATH/venv" \
    "$RELEASE_PATH/wheelhouse" "$RELEASE_PATH/systemd" \
    "$RELEASE_PATH/.service-creator"
  trap - EXIT
fi

case "${SERVICE_CREATOR_INITIALIZE_MODE:-}" in
  "") ;;
  initialize)
    SERVICE_CREATOR_PREPARED_RELEASE="$RELEASE_PATH" "$SCRIPT_DIR/initialize.sh"
    ;;
  --reinstall)
    SERVICE_CREATOR_PREPARED_RELEASE="$RELEASE_PATH" "$SCRIPT_DIR/initialize.sh" --reinstall
    ;;
  *) echo "Error: invalid initialization mode" >&2; exit 2 ;;
esac

install_supervisor_assets() {
  local release="$1" unit
  local source="$release/systemd"
  for unit in "$source"/*.service "$source"/*.timer; do
    [[ -f "$unit" ]] || continue
    sed "s|/opt/$SERVICE_NAME|$DEPLOY_ROOT|g" "$unit" |
      sudo tee "/etc/systemd/system/$(basename "$unit")" >/dev/null
    sudo chmod 0644 "/etc/systemd/system/$(basename "$unit")"
  done
  sudo systemctl daemon-reload
}

PREVIOUS_TARGET=""
if [[ -L "$CURRENT_LINK" ]]; then
  PREVIOUS_TARGET="$(readlink -f "$CURRENT_LINK")"
  [[ "$PREVIOUS_TARGET" == "$RELEASE_PATH" ]] && PREVIOUS_TARGET=""
fi
ln -sfn "$RELEASE_PATH" "$DEPLOY_ROOT/current.new"
mv -Tf "$DEPLOY_ROOT/current.new" "$CURRENT_LINK"
install_supervisor_assets "$RELEASE_PATH"
activation_status=0
sudo systemctl enable "$SERVICE_NAME.service" || activation_status=$?
((activation_status != 0)) || sudo systemctl restart "$SERVICE_NAME.service" || activation_status=$?
((activation_status != 0)) || sudo systemctl enable --now \
  "$SERVICE_NAME-cache-refresh.timer" || activation_status=$?
((activation_status != 0)) || "$CURRENT_LINK/.service-creator/readiness" || activation_status=$?
if ((activation_status != 0)); then
  if [[ -n "$PREVIOUS_TARGET" && -d "$PREVIOUS_TARGET" ]]; then
    ln -sfn "$PREVIOUS_TARGET" "$DEPLOY_ROOT/current.rollback"
    mv -Tf "$DEPLOY_ROOT/current.rollback" "$CURRENT_LINK"
    install_supervisor_assets "$PREVIOUS_TARGET"
    sudo systemctl restart "$SERVICE_NAME.service" || true
    sudo systemctl enable --now "$SERVICE_NAME-cache-refresh.timer" || true
  else
    rm -f -- "$CURRENT_LINK"
    sudo systemctl disable --now "$SERVICE_NAME.service" || true
    sudo systemctl disable --now "$SERVICE_NAME-cache-refresh.timer" || true
  fi
  exit "$activation_status"
fi
echo "Activated $RELEASE_PATH"
