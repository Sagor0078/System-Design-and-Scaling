#!/usr/bin/env python3
"""mongo_consistency_demo.py – Strong vs eventual consistency with MongoDB.

MongoDB replica sets support *read preferences* that control which node
serves reads.  With a single-node RS the behaviour is deterministic, but the
code paths are identical to what you'd run against a real 3-node cluster.

Read preferences used:
  PRIMARY            → always reads from the leader  (strong consistency)
  PRIMARY_PREFERRED  → prefers leader, falls back to secondary
  SECONDARY          → reads from a follower  (eventual consistency – may be stale)

Usage:
    # first init the replica set once:
    #   docker exec mongodb mongosh --eval "rs.initiate()"
    python -m module2_app.mongo_consistency_demo
"""

from __future__ import annotations

import time

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


MONGO_URI = "mongodb://localhost:27017/?replicaSet=rs0"
SEPARATOR = "=" * 60


def main() -> None:
    print(SEPARATOR)
    print("MongoDB – Strong vs Eventual Consistency Demo")
    print(SEPARATOR)

    # ── 1. Connect with PRIMARY preference (strong) ────────────────────
    client_primary = MongoClient(
        MONGO_URI,
        readPreference="primary",
        serverSelectionTimeoutMS=5000,
    )
    db = client_primary.module2
    coll = db.consistency_test

    # Clean slate
    coll.drop()

    # ── 2. Write ────────────────────────────────────────────────────────
    doc = {"sensor": "temp-42", "value": 23.5, "ts": time.time()}
    result = coll.insert_one(doc)
    print(f"\n✏️  Inserted on PRIMARY  _id={result.inserted_id}")

    # ── 3. Immediate read – PRIMARY (strong) ────────────────────────────
    row = coll.find_one({"sensor": "temp-42"})
    print(f"📖 Read from PRIMARY          : {row}")

    # ── 4. Read with SECONDARY_PREFERRED (eventual) ─────────────────────
    client_secondary = MongoClient(
        MONGO_URI,
        readPreference="secondaryPreferred",
        serverSelectionTimeoutMS=5000,
    )
    try:
        row2 = client_secondary.module2.consistency_test.find_one({"sensor": "temp-42"})
        print(f"📖 Read from SECONDARY_PREF   : {row2}")
    except ServerSelectionTimeoutError:
        print("📖 Read from SECONDARY_PREF   : ⚠️  no secondary available (single-node RS)")

    # ── 5. Write-concern demo (w=majority vs w=1) ──────────────────────
    print("\n📝 Write-concern comparison:")
    for w in [1, "majority"]:
        t0 = time.perf_counter()
        db_wc = client_primary.module2.with_options(
            write_concern=__import__("pymongo").WriteConcern(w=w)
        )
        db_wc.consistency_test.insert_one(
            {"sensor": "temp-42", "value": 24.0, "w": str(w), "ts": time.time()}
        )
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  w={str(w):10s}  {elapsed:7.2f} ms")

    # ── 6. Summary ──────────────────────────────────────────────────────
    print(f"""
{SEPARATOR}
Key take-away
{SEPARATOR}
  • readPreference=primary          → strong consistency (ACID-like)
  • readPreference=secondaryPreferred → eventual (BASE-like, may be stale)
  • writeConcern w=majority          → durable after majority ack
  • writeConcern w=1                 → fast, but data on 1 node only

  MongoDB's default (w=1, readPref=primary) gives strong reads
  but weak durability.  Use w=majority + readPref=primary for
  the strongest guarantee short of transactions.
""")

    client_primary.close()
    client_secondary.close()
    print("Done.")


if __name__ == "__main__":
    main()
