#!/usr/bin/env bash
###############################################################################
# backup_restore.sh – PostgreSQL backup & restore via Docker
#
# Usage:
#   ./backup_restore.sh backup                    # dump primary → backups/
#   ./backup_restore.sh backup shard2             # dump shard-2 → backups/
#   ./backup_restore.sh restore <dumpfile>         # restore to primary
#   ./backup_restore.sh restore <dumpfile> shard2  # restore to shard-2
#   ./backup_restore.sh list                       # list backups
###############################################################################
set -euo pipefail

BACKUP_DIR="$(cd "$(dirname "$0")" && pwd)/backups"
mkdir -p "$BACKUP_DIR"

PG_USER=postgres
PG_PASS=example
PG_DB=module2_db

resolve_port() {
  case "${1:-primary}" in
    primary) echo 5432 ;;
    shard2)  echo 5442 ;;
    *)       echo "$1"  ;;          # allow raw port
  esac
}

cmd_backup() {
  local port
  port=$(resolve_port "${1:-primary}")
  local tag="${1:-primary}"
  local ts
  ts=$(date +%Y%m%d_%H%M%S)
  local file="$BACKUP_DIR/${PG_DB}_${tag}_${ts}.dump"

  echo " Backing up ${PG_DB} from port ${port} …"
  PGPASSWORD="$PG_PASS" docker exec pg-"${tag}" \
    pg_dump -U "$PG_USER" -F c -b -v -f "/tmp/backup.dump" "$PG_DB"
  docker cp "pg-${tag}:/tmp/backup.dump" "$file"
  echo " Backup written to $file"
}

cmd_restore() {
  local file="$1"
  local port
  port=$(resolve_port "${2:-primary}")
  local tag="${2:-primary}"

  if [ ! -f "$file" ]; then
    echo " File not found: $file" >&2; exit 1
  fi

  echo " Restoring $file to port ${port} …"
  docker cp "$file" "pg-${tag}:/tmp/restore.dump"
  PGPASSWORD="$PG_PASS" docker exec pg-"${tag}" \
    pg_restore -U "$PG_USER" -d "$PG_DB" -v --clean --if-exists "/tmp/restore.dump" || true
  echo " Restore complete on pg-${tag}"
}

cmd_list() {
  echo " Backups in $BACKUP_DIR:"
  ls -lh "$BACKUP_DIR"/*.dump 2>/dev/null || echo "  (none)"
}

# dispatch 
case "${1:-help}" in
  backup)   cmd_backup "${2:-primary}" ;;
  restore)  cmd_restore "${2:?Usage: $0 restore <file> [target]}" "${3:-primary}" ;;
  list)     cmd_list ;;
  *)
    echo "Usage:"
    echo "  $0 backup  [primary|shard2]"
    echo "  $0 restore <dumpfile> [primary|shard2]"
    echo "  $0 list"
    ;;
esac
