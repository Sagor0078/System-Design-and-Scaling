"""
db_operations.py
────────────────
Interactive CLI to perform INSERT / UPDATE / DELETE on the
PostgreSQL `student` table so you can watch Debezium capture
each change in real-time.

Usage:
    python db_operations.py
"""

import sys

import psycopg2
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "cdc_db",
    "user": "cdc_user",
    "password": "cdc_pass",
}


def get_connection():
    """Return a new auto-commit psycopg2 connection."""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn


def show_students(conn) -> None:
    """Print all rows in the student table."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM student ORDER BY id;")
        rows = cur.fetchall()

    table = Table(title="📚 student table", show_lines=True)
    table.add_column("ID", style="bold cyan", justify="center")
    table.add_column("Name", style="bold white")
    for row in rows:
        table.add_row(str(row[0]), row[1])
    console.print(table)


def insert_student(conn) -> None:
    """Insert a new student."""
    name = console.input("[bold green]Enter student name → [/]").strip()
    if not name:
        console.print("[red]Name cannot be empty.[/]")
        return
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO student (name) VALUES (%s) RETURNING id;", (name,)
        )
        new_id = cur.fetchone()[0]
    console.print(f"Inserted student id={new_id}, name='{name}'[/]")


def update_student(conn) -> None:
    """Update an existing student's name."""
    try:
        sid = int(console.input("[bold yellow]Enter student ID to update → [/]").strip())
    except ValueError:
        console.print("Invalid ID.")
        return
    new_name = console.input("Enter new name ").strip()
    if not new_name:
        console.print("Name cannot be empty.")
        return
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE student SET name = %s WHERE id = %s;", (new_name, sid)
        )
        if cur.rowcount == 0:
            console.print(f"No student found with id={sid}.")
        else:
            console.print(f"Updated student id={sid} → name='{new_name}'")


def delete_student(conn) -> None:
    """Delete a student by ID."""
    try:
        sid = int(console.input("Enter student ID to delete ").strip())
    except ValueError:
        console.print("Invalid ID.")
        return
    with conn.cursor() as cur:
        cur.execute("DELETE FROM student WHERE id = %s;", (sid,))
        if cur.rowcount == 0:
            console.print(f"[red]No student found with id={sid}.[/]")
        else:
            console.print(f"[red]  Deleted student id={sid}[/]")


MENU = """
[bold cyan]╔══════════════════════════════════════╗
║   CDC Demo  –  Database Operations   ║
╠══════════════════════════════════════╣
║  1 │ Show all students               ║
║  2 │ Insert a student                ║
║  3 │ Update a student                ║
║  4 │ Delete a student                ║
║  q │ Quit                            ║
╚══════════════════════════════════════╝[/]
"""


def main() -> None:
    try:
        conn = get_connection()
    except psycopg2.OperationalError as exc:
        console.print(f"[bold red] Cannot connect to PostgreSQL:[/] {exc}")
        sys.exit(1)

    console.print(
        Panel(
            "[bold]Connected to PostgreSQL[/]  •  "
            "Every change you make here will be captured by Debezium → Kafka",
            title="CDC Pipeline",
            border_style="bright_blue",
        )
    )

    while True:
        console.print(MENU)
        choice = console.input("[bold]Select an option → [/]").strip().lower()
        if choice == "1":
            show_students(conn)
        elif choice == "2":
            insert_student(conn)
        elif choice == "3":
            update_student(conn)
        elif choice == "4":
            delete_student(conn)
        elif choice in ("q", "quit", "exit"):
            console.print("[dim]Bye![/]")
            break
        else:
            console.print("[red]Unknown option.[/]")

    conn.close()


if __name__ == "__main__":
    main()
