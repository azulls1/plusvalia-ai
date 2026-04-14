#!/usr/bin/env bash
# ================================================================
# ROLLBACK SCRIPT — geo-app backend
# ================================================================
# Rolls back the backend-api service to a previous Docker image.
#
# Usage:
#   ./scripts/rollback.sh <image_tag>
#   ./scripts/rollback.sh backend-inmobiliario:v1.2.3
#   ./scripts/rollback.sh registry.example.com/backend-inmobiliario:20260320
#
# Requirements:
#   - Docker installed and running
#   - Access to the Docker registry (if using remote images)
#   - Sufficient permissions to manage containers/services
# ================================================================

set -euo pipefail

# ================================================================
# CONFIGURATION
# ================================================================
readonly SCRIPT_NAME="$(basename "$0")"
readonly SERVICE_NAME="${SERVICE_NAME:-backend-api}"
readonly COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
readonly HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
readonly HEALTH_RETRIES=12
readonly HEALTH_INTERVAL=10
readonly SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"

# ================================================================
# LOGGING HELPERS
# ================================================================
log()   { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]  $*"; }
warn()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN]  $*" >&2; }
error() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*" >&2; }

# ================================================================
# NOTIFICATION (Slack / stdout)
# ================================================================
notify() {
  local message="$1"
  log "$message"

  if [[ -n "$SLACK_WEBHOOK" ]]; then
    curl -s -X POST -H 'Content-type: application/json' \
      --data "{\"text\":\"[geo-app rollback] ${message}\"}" \
      "$SLACK_WEBHOOK" > /dev/null 2>&1 || warn "Failed to send Slack notification"
  fi
}

# ================================================================
# USAGE
# ================================================================
usage() {
  cat <<EOF
Usage: $SCRIPT_NAME <image_tag>

Arguments:
  image_tag   The Docker image tag to roll back to.
              Examples:
                backend-inmobiliario:v1.2.3
                registry.example.com/backend-inmobiliario:20260320-abc1234

Environment variables (optional):
  SERVICE_NAME       Docker service/container name (default: backend-api)
  COMPOSE_FILE       Docker Compose file path (default: docker-compose.production.yml)
  HEALTH_URL         Health check URL (default: http://localhost:8000/health)
  SLACK_WEBHOOK_URL  Slack webhook for notifications
EOF
  exit 1
}

# ================================================================
# HEALTH CHECK
# ================================================================
health_check() {
  log "Running health check against $HEALTH_URL ..."
  for i in $(seq 1 "$HEALTH_RETRIES"); do
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")

    if [[ "$status" == "200" ]]; then
      log "Health check PASSED (attempt $i/$HEALTH_RETRIES)"
      return 0
    fi

    warn "Health check attempt $i/$HEALTH_RETRIES: HTTP $status — retrying in ${HEALTH_INTERVAL}s..."
    sleep "$HEALTH_INTERVAL"
  done

  error "Health check FAILED after $HEALTH_RETRIES attempts"
  return 1
}

# ================================================================
# ROLLBACK — Docker Swarm mode
# ================================================================
rollback_swarm() {
  local image_tag="$1"
  log "Rolling back Docker Swarm service '$SERVICE_NAME' to image: $image_tag"
  docker service update --image "$image_tag" "$SERVICE_NAME"
}

# ================================================================
# ROLLBACK — Docker Compose mode
# ================================================================
rollback_compose() {
  local image_tag="$1"
  log "Rolling back via Docker Compose (file: $COMPOSE_FILE)"

  # Stop the current container
  log "Stopping current $SERVICE_NAME container..."
  docker compose -f "$COMPOSE_FILE" stop "$SERVICE_NAME"

  # Pull the target image
  log "Pulling image: $image_tag"
  docker pull "$image_tag"

  # Start with the rollback image
  log "Starting $SERVICE_NAME with image $image_tag"
  IMAGE_TAG="$image_tag" docker compose -f "$COMPOSE_FILE" up -d "$SERVICE_NAME"
}

# ================================================================
# MAIN
# ================================================================
main() {
  # -- Validate arguments --
  if [[ $# -lt 1 ]]; then
    error "Missing required argument: image_tag"
    usage
  fi

  local target_image="$1"
  notify "ROLLBACK STARTED — target image: $target_image"

  # -- Detect deployment mode --
  local mode="compose"
  if docker service ls > /dev/null 2>&1 && docker service inspect "$SERVICE_NAME" > /dev/null 2>&1; then
    mode="swarm"
  fi
  log "Detected deployment mode: $mode"

  # -- Pull the target image first --
  log "Pulling target image: $target_image"
  if ! docker pull "$target_image"; then
    notify "ROLLBACK FAILED — could not pull image: $target_image"
    exit 1
  fi
  log "Image pulled successfully"

  # -- Execute rollback --
  if [[ "$mode" == "swarm" ]]; then
    rollback_swarm "$target_image"
  else
    rollback_compose "$target_image"
  fi

  # -- Verify health --
  if health_check; then
    notify "ROLLBACK SUCCEEDED — now running: $target_image"
    exit 0
  else
    notify "ROLLBACK FAILED — health check did not pass after rolling back to $target_image"
    exit 1
  fi
}

main "$@"
