#!/usr/bin/env bash
###############################################################################
# scylla_backup.sh – ScyllaDB snapshot & restore helpers
#
# Usage:
#   ./scylla_backup.sh snapshot              # create snapshot on all nodes
#   ./scylla_backup.sh snapshot scylla-node1 # single node
#   ./scylla_backup.sh list     scylla-node1 # list snapshots
#   ./scylla_backup.sh clear    scylla-node1 # remove old snapshots
###############################################################################
set -euo pipefail

KEYSPACE="${KEYSPACE:-module2ks}"
SNAPSHOT_TAG="mod2_$(date +%Y%m%d_%H%M%S)"

NODES=("scylla-node1" "scylla-node2" "scylla-node3")

cmd_snapshot() {
  local targets=("${@:-${NODES[@]}}")
  for node in "${targets[@]}"; do
    echo "📸 Creating snapshot on $node  (tag=$SNAPSHOT_TAG, ks=$KEYSPACE) …"
    docker exec "$node" nodetool snapshot -t "$SNAPSHOT_TAG" "$KEYSPACE"
    echo "   ✅ snapshot $SNAPSHOT_TAG created on $node"
  done
}

cmd_list() {
  local node="${1:-scylla-node1}"
  echo "📋 Snapshots on $node:"
  docker exec "$node" nodetool listsnapshots
}

cmd_clear() {
  local targets=("${@:-${NODES[@]}}")
  for node in "${targets[@]}"; do
    echo "🗑️  Clearing ALL snapshots on $node …"
    docker exec "$node" nodetool clearsnapshot -- "$KEYSPACE"
    echo "   done."
  done
}

# ── dispatch ────────────────────────────────────────────────────────────────
case "${1:-help}" in
  snapshot) shift; cmd_snapshot "$@" ;;
  list)     cmd_list "${2:-scylla-node1}" ;;
  clear)    shift; cmd_clear "$@" ;;
  *)
    echo "Usage:"
    echo "  $0 snapshot [node …]   – take named snapshot"
    echo "  $0 list     [node]     – list snapshots"
    echo "  $0 clear    [node …]   – remove all snapshots"
    ;;
esac
