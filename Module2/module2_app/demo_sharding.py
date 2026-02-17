#!/usr/bin/env python3
"""demo_sharding.py – Manual range-based AND hash-based partitioning.

Two independent PostgreSQL instances act as shards:
    Shard 0  →  pg-primary  (port 5432)
    Shard 1  →  pg-shard2   (port 5442)

We demonstrate two partitioning strategies and compare distribution.

Usage:
    python -m module2_app.demo_sharding
"""

from __future__ import annotations

import hashlib
from collections import Counter

from module2_app.db import pg_shard, ensure_schema, insert_user, fetch_all_users


NUM_SHARDS = 2
SEPARATOR = "=" * 60

USERS = [
    ("alice",   "asia"),
    ("bob",     "europe"),
    ("carol",   "africa"),
    ("dave",    "north-america"),
    ("eve",     "europe"),
    ("frank",   "asia"),
    ("grace",   "south-america"),
    ("heidi",   "oceania"),
    ("ivan",    "europe"),
    ("judy",    "africa"),
    ("karl",    "north-america"),
    ("laura",   "asia"),
    ("mallory", "europe"),
    ("niaj",    "north-america"),
    ("olivia",  "oceania"),
    ("pat",     "south-america"),
]


# strategy helpers 

def shard_by_range(region: str) -> int:
    """Range partition: regions starting A-M → shard 0, N-Z → shard 1."""
    return 0 if region[0].upper() <= "M" else 1


def shard_by_hash(name: str) -> int:
    """Hash partition: MD5 of name mod NUM_SHARDS."""
    digest = hashlib.md5(name.encode()).hexdigest()
    return int(digest, 16) % NUM_SHARDS


# demo runners 

def run_strategy(strategy_name: str, key_fn):
    """Insert USERS using *key_fn* to pick a shard, then print distribution."""
    print(f"\n{'─'*60}")
    print(f"Strategy: {strategy_name}")
    print(f"{'─'*60}")

    # ensure schema on both shards & truncate from previous run
    for sid in range(NUM_SHARDS):
        conn = pg_shard(sid)
        ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute("TRUNCATE users RESTART IDENTITY")
        conn.commit()
        conn.close()

    # insert
    distribution: Counter = Counter()
    for name, region in USERS:
        sid = key_fn(name) if "hash" in strategy_name.lower() else key_fn(region)
        conn = pg_shard(sid)
        uid = insert_user(conn, name, region)
        distribution[sid] += 1
        print(f"  {name:10s} region={region:16s} → shard {sid}  (id={uid})")
        conn.close()

    # summary
    print(f"\n  Distribution: {dict(distribution)}")

    # read back
    for sid in range(NUM_SHARDS):
        conn = pg_shard(sid)
        rows = fetch_all_users(conn)
        print(f"\n  Shard {sid} (port {5432 if sid == 0 else 5442}) – {len(rows)} rows:")
        for r in rows:
            print(f"    {r}")
        conn.close()


def main() -> None:
    print(SEPARATOR)
    print("Manual Sharding Demo  –  Range vs Hash Partitioning")
    print(SEPARATOR)

    run_strategy("Range partitioning (by region first letter A-M / N-Z)", shard_by_range)
    run_strategy("Hash partitioning  (MD5 of name mod 2)", shard_by_hash)

    print(f"\n{SEPARATOR}")
    print("Done.")


if __name__ == "__main__":
    main()
