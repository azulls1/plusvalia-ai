#!/bin/bash
# backup.sh — Automated backup for geo-app
# Usage: ./backup.sh [full|db|models|config|verify|cleanup]

set -euo pipefail

BACKUP_DIR="/root/backups/geo-app"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

backup_database() {
    log "Starting database backup..."
    local backup_file="$BACKUP_DIR/db_backup_$DATE.sql.gz"

    # Use Supabase pg_dump via Docker
    docker exec supabase_db pg_dump -U supabase_admin -d postgres \
        --no-owner --no-privileges \
        -t 'iainmobiliaria_*' \
        | gzip > "$backup_file"

    local size=$(du -h "$backup_file" | cut -f1)
    log "Database backup complete: $backup_file ($size)"
}

backup_models() {
    log "Starting model backup..."
    local backup_file="$BACKUP_DIR/models_backup_$DATE.tar.gz"

    # Copy model files from Docker volume
    docker cp backend-api:/app/ml_model/models/ /tmp/model_backup/
    tar -czf "$backup_file" -C /tmp model_backup/
    rm -rf /tmp/model_backup/

    local size=$(du -h "$backup_file" | cut -f1)
    log "Model backup complete: $backup_file ($size)"
}

backup_config() {
    log "Starting config backup..."
    local backup_file="$BACKUP_DIR/config_backup_$DATE.tar.gz"

    tar -czf "$backup_file" \
        /root/docker-compose.production.yml \
        /root/supabase.yaml \
        /root/monitoring/ \
        --exclude='*.log' 2>/dev/null || true

    local size=$(du -h "$backup_file" | cut -f1)
    log "Config backup complete: $backup_file ($size)"
}

cleanup_old() {
    log "Cleaning backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete
    log "Cleanup complete"
}

verify_backup() {
    log "Verifying latest backup..."
    local latest=$(ls -t "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null | head -1)
    if [ -n "$latest" ]; then
        gzip -t "$latest" && log "Backup integrity OK: $latest" || log "ERROR: Backup corrupted: $latest"
    else
        log "WARNING: No database backups found"
    fi
}

case "${1:-full}" in
    full)
        backup_database
        backup_models
        backup_config
        cleanup_old
        verify_backup
        ;;
    db) backup_database ;;
    models) backup_models ;;
    config) backup_config ;;
    verify) verify_backup ;;
    cleanup) cleanup_old ;;
    *)
        echo "Usage: $0 [full|db|models|config|verify|cleanup]"
        exit 1
        ;;
esac

log "Backup process complete"
