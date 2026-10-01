#!/usr/bin/env bash
set -euo pipefail
SERVICE_NAME="datavis-api"
: "${SERVICE_CREATOR_ENV_FILE:?Controller must set SERVICE_CREATOR_ENV_FILE}"
: "${SERVICE_CREATOR_HEALTH_PATH:?Controller must set SERVICE_CREATOR_HEALTH_PATH}"
[[ -f "$SERVICE_CREATOR_ENV_FILE" ]] || { echo "Missing controller environment" >&2; exit 1; }
set -a
# shellcheck disable=SC1090
source "$SERVICE_CREATOR_ENV_FILE"
set +a
READINESS_HOST="${DATAVIS_API_HOST:?Controller environment must define DATAVIS_API_HOST}"
READINESS_PORT="${DATAVIS_API_PORT:?Controller environment must define DATAVIS_API_PORT}"
case "$READINESS_HOST" in
  0.0.0.0) READINESS_HOST=127.0.0.1 ;;
  ::) READINESS_HOST='[::1]' ;;
  *:*) READINESS_HOST="[$READINESS_HOST]" ;;
esac
systemctl is-active --quiet "$SERVICE_NAME.service"
curl --fail --silent --show-error \
  --retry 15 \
  --retry-delay 1 \
  --retry-connrefused \
  "http://$READINESS_HOST:$READINESS_PORT$SERVICE_CREATOR_HEALTH_PATH" >/dev/null
