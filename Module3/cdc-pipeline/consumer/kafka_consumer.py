"""
kafka_consumer.py
─────────────────
Real-time Kafka consumer that listens to the Debezium CDC topic
for the `student` table and pretty-prints every change event.

Usage:
    python kafka_consumer.py                     # default topic
    python kafka_consumer.py --topic cdc.public.student
"""

import argparse
import json
import signal
import sys

from confluent_kafka import Consumer, KafkaError, KafkaException
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()

KAFKA_BROKER = "localhost:29092"
DEFAULT_TOPIC = "cdc.public.student"
GROUP_ID = "cdc-python-consumer"

# ── graceful shutdown ────────────────────────────────────────────
_running = True


def _shutdown(sig, frame):
    global _running
    console.print("\n[yellow]⏹  Shutting down consumer…[/]")
    _running = False


signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)


# ── event formatting ────────────────────────────────────────────

OP_LABELS = {
    "c": ("INSERT", "bold green"),
    "u": ("UPDATE", "bold yellow"),
    "d": ("DELETE", "bold red"),
    "r": ("SNAPSHOT", "bold cyan"),
}


def format_event(raw_value: dict) -> None:
    """Pretty-print a single Debezium change event."""
    payload = raw_value.get("payload", raw_value)

    op_code = payload.get("op", "?")
    label, color = OP_LABELS.get(op_code, (op_code.upper(), "bold white"))

    before = payload.get("before")
    after = payload.get("after")
    ts_ms = payload.get("ts_ms", "")
    source = payload.get("source", {})
    table = source.get("table", "unknown")

    # header
    console.rule(f"[{color}]  {label}  on  {table}  [{color}]")

    # before / after comparison
    tbl = Table(show_header=True, header_style="bold magenta", show_lines=True)
    tbl.add_column("Field", style="cyan", min_width=10)
    tbl.add_column("Before", style="red", min_width=20)
    tbl.add_column("After", style="green", min_width=20)

    all_keys = set()
    if before:
        all_keys.update(before.keys())
    if after:
        all_keys.update(after.keys())

    for key in sorted(all_keys):
        b_val = str(before.get(key, "—")) if before else "—"
        a_val = str(after.get(key, "—")) if after else "—"
        style = "" if b_val == a_val else "bold"
        tbl.add_row(f"[{style}]{key}", f"[{style}]{b_val}", f"[{style}]{a_val}")

    console.print(tbl)
    console.print(f"[dim]ts_ms={ts_ms}  source.lsn={source.get('lsn', '')}[/]\n")


def format_raw(raw_value: dict) -> None:
    """Fallback: dump the full JSON payload."""
    console.print(
        Syntax(json.dumps(raw_value, indent=2), "json", theme="monokai", line_numbers=True)
    )


# ── main consumer loop ──────────────────────────────────────────

def consume(topic: str) -> None:
    conf = {
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    }

    consumer = Consumer(conf)
    consumer.subscribe([topic])

    console.print(
        Panel(
            f"[bold]Listening on topic:[/] [cyan]{topic}[/]\n"
            f"[bold]Broker:[/] {KAFKA_BROKER}\n"
            f"[bold]Group:[/] {GROUP_ID}\n\n"
            "[dim]Press Ctrl+C to stop.[/]",
            title=" CDC Kafka Consumer",
            border_style="bright_blue",
        )
    )

    try:
        while _running:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            try:
                value = json.loads(msg.value().decode("utf-8"))
                # Debezium wraps events in {"schema":…,"payload":…} when
                # schemas.enable=true, or sends payload directly otherwise.
                if "payload" in value or "op" in value:
                    format_event(value)
                else:
                    format_raw(value)
            except (json.JSONDecodeError, UnicodeDecodeError):
                console.print(f"[dim]Non-JSON message: {msg.value()}[/]")

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        console.print("[green]Consumer closed.[/]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Debezium CDC Kafka consumer")
    parser.add_argument(
        "--topic",
        default=DEFAULT_TOPIC,
        help=f"Kafka topic to consume (default: {DEFAULT_TOPIC})",
    )
    args = parser.parse_args()
    consume(args.topic)


if __name__ == "__main__":
    main()
