"""
register_connector.py
─────────────────────
Registers (or updates) the Debezium PostgreSQL source connector
via the Kafka Connect REST API.

Usage:
    python register_connector.py          # uses defaults
    python register_connector.py --wait   # waits until Debezium is healthy
"""

import argparse
import json
import sys
import time

import requests
from rich.console import Console
from rich.panel import Panel

console = Console()

DEBEZIUM_URL = "http://localhost:8083"
CONNECTOR_NAME = "cdc-postgres-connector"

CONNECTOR_CONFIG = {
    "name": CONNECTOR_NAME,
    "config": {
        # Connector class
        "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
        "tasks.max": "1",

        # ── Database connection ──────────────────────────────────
        "database.hostname": "postgres",
        "database.port": "5432",
        "database.user": "cdc_user",
        "database.password": "cdc_pass",
        "database.dbname": "cdc_db",

        # Logical name used as Kafka topic prefix
        "topic.prefix": "cdc",

        # ── Tables to capture ───────────────────────────────────
        "table.include.list": "public.student",

        # ── Snapshot & plugin ────────────────────────────────────
        "plugin.name": "pgoutput",
        "slot.name": "debezium_slot",
        "publication.name": "dbz_publication",
        "snapshot.mode": "initial",

        # ── Converters (plain JSON, no Schema Registry needed) ──
        "key.converter": "org.apache.kafka.connect.json.JsonConverter",
        "key.converter.schemas.enable": "false",
        "value.converter": "org.apache.kafka.connect.json.JsonConverter",
        "value.converter.schemas.enable": "false",

        # ── Tombstone / delete handling ──────────────────────────
        "delete.handling.mode": "rewrite",
        "tombstones.on.delete": "false",
    },
}


def wait_for_debezium(timeout: int = 120) -> bool:
    """Block until the Debezium REST API is reachable."""
    console.print("[bold yellow] Waiting for Debezium Connect to be ready…[/]")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{DEBEZIUM_URL}/connectors", timeout=5)
            if r.status_code == 200:
                console.print("Debezium is ready!")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(3)
    console.print("Timed out waiting for Debezium. ")
    return False


def register() -> None:
    """POST the connector configuration to Debezium."""
    url = f"{DEBEZIUM_URL}/connectors"

    # Check if the connector already exists
    try:
        existing = requests.get(f"{url}/{CONNECTOR_NAME}", timeout=10)
        if existing.status_code == 200:
            console.print(
                f"[yellow]Connector '{CONNECTOR_NAME}' already exists – updating config…[/]"
            )
            resp = requests.put(
                f"{url}/{CONNECTOR_NAME}/config",
                headers={"Content-Type": "application/json"},
                data=json.dumps(CONNECTOR_CONFIG["config"]),
                timeout=10,
            )
        else:
            raise requests.HTTPError()
    except (requests.HTTPError, requests.ConnectionError):
        console.print(f"[cyan]Creating connector '{CONNECTOR_NAME}'…[/]")
        resp = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(CONNECTOR_CONFIG),
            timeout=10,
        )

    if resp.status_code in (200, 201):
        console.print(
            Panel(
                json.dumps(resp.json(), indent=2),
                title="Connector Registered",
                border_style="green",
            )
        )
    else:
        console.print(f"Failed ({resp.status_code}):[/] {resp.text}")
        sys.exit(1)


def check_status() -> None:
    """Print the current status of the connector."""
    time.sleep(3)  # give Debezium a moment
    try:
        resp = requests.get(
            f"{DEBEZIUM_URL}/connectors/{CONNECTOR_NAME}/status", timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            state = data.get("connector", {}).get("state", "UNKNOWN")
            tasks = data.get("tasks", [])
            color = "green" if state == "RUNNING" else "red"
            console.print(f"\n[bold]Connector state:[/] [{color}]{state}[/{color}]")
            for t in tasks:
                t_state = t.get("state", "UNKNOWN")
                t_color = "green" if t_state == "RUNNING" else "red"
                console.print(
                    f"  Task {t.get('id')}: [{t_color}]{t_state}[/{t_color}]"
                )
    except Exception as exc:
        console.print(f"[dim]Could not fetch status: {exc}[/]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Register Debezium CDC connector")
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for Debezium to become healthy before registering",
    )
    args = parser.parse_args()

    if args.wait:
        if not wait_for_debezium():
            sys.exit(1)

    register()
    check_status()


if __name__ == "__main__":
    main()
