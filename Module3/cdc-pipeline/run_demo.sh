#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# run_demo.sh — one-shot script to bring up the full CDC demo
# ──────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "══════════════════════════════════════════════"
echo "  CDC Pipeline — Full Demo Launcher"
echo "══════════════════════════════════════════════"
echo ""

# ── 1. Start Docker Compose ─────────────────────────────────
echo "▶ Starting Docker containers…"
docker compose up -d
echo ""

# ── 2. Wait for Debezium to be healthy ──────────────────────
echo "▶ Waiting for Debezium Connect REST API…"
until curl -sf http://localhost:8083/connectors > /dev/null 2>&1; do
    printf "."
    sleep 3
done
echo ""
echo "✅ Debezium is ready."
echo ""

# ── 3. Install Python dependencies ──────────────────────────
echo "▶ Installing Python dependencies…"
pip install -q -r requirements.txt
echo ""

# ── 4. Register the connector ───────────────────────────────
echo "▶ Registering Debezium connector…"
python connector/register_connector.py
echo ""

# ── 5. Instructions ─────────────────────────────────────────
echo "══════════════════════════════════════════════"
echo "  🎉  All set!"
echo ""
echo "  Terminal 1 — Start the consumer:"
echo "    python consumer/kafka_consumer.py"
echo ""
echo "  Terminal 2 — Perform DB operations:"
echo "    python producer/db_operations.py"
echo ""
echo "  Kafka UI: http://localhost:8080"
echo "══════════════════════════════════════════════"
