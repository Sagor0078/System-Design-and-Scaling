#!/usr/bin/env python3
"""demo_replication.py – Write to PRIMARY, read back from REPLICA.

This demonstrates PostgreSQL streaming replication (leader → follower).
The replica is a hot-standby that accepts read-only queries.

Usage:
    python -m module2_app.demo_replication
"""

from __future__ import annotations

import time

from module2_app.db import pg_primary, pg_replica, ensure_schema, insert_user, fetch_all_users


SEPARATOR = "=" * 60


def main() -> None:
    print(SEPARATOR)
    print("PostgreSQL Leader-Follower Replication Demo")
    print(SEPARATOR)

    primary = pg_primary()
    ensure_schema(primary)

    uid = insert_user(primary, "alice", "us-east")
    print(f"\n Wrote user alice  →  PRIMARY (port 5432)  id={uid}")

    uid2 = insert_user(primary, "bob", "eu-west")
    print(f" Wrote user bob    →  PRIMARY (port 5432)  id={uid2}")

    # Show rows on primary
    print("\n Rows on PRIMARY:")
    for row in fetch_all_users(primary):
        print(f"   {row}")

    # Give replication a moment to catch up (usually < 100 ms in this setup)
    print("\n Waiting 1 s for WAL replay on replica …")
    time.sleep(1)

    replica = pg_replica()
    print("\n Rows on REPLICA (port 5433, read-only):")
    for row in fetch_all_users(replica):
        print(f"   {row}")

    # Prove replica is read-only 
    print("\n Attempting INSERT on replica (should fail) …")
    try:
        insert_user(replica, "should-fail", "nowhere")
    except Exception as exc:
        print(f"Expected error: {exc}")

    # Check replication lag 
    with primary.cursor() as cur:
        cur.execute(
            "SELECT client_addr, state, sent_lsn, replay_lsn "
            "FROM pg_stat_replication"
        )
        rows = cur.fetchall()
    print("\n pg_stat_replication on primary:")
    for r in rows:
        print(f"   {r}")

    primary.close()
    replica.close()
    print(f"\n{SEPARATOR}")
    print("Done.")


if __name__ == "__main__":
    main()
