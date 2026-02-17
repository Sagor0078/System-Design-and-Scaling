#!/usr/bin/env python3

from __future__ import annotations

import time

from cassandra.cluster import Cluster
from cassandra import ConsistencyLevel
from cassandra.query import SimpleStatement

CONTACT_POINTS = ["127.0.0.1"]
KEYSPACE = "module2ks"
SEPARATOR = "=" * 60


#schema 

def setup_schema(session) -> None:
    session.execute(
        "CREATE KEYSPACE IF NOT EXISTS %s "
        "WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3}" % KEYSPACE
    )
    session.set_keyspace(KEYSPACE)
    session.execute(
        "CREATE TABLE IF NOT EXISTS sensor_data ("
        "  sensor_id text,"
        "  ts        timeuuid,"
        "  value     double,"
        "  PRIMARY KEY (sensor_id, ts)"
        ") WITH CLUSTERING ORDER BY (ts DESC)"
    )


# ── helpers ─────────────────────────────────────────────────────────────────

def timed_exec(session, stmt, params=None, label=""):
    """Execute *stmt* and print elapsed time."""
    t0 = time.perf_counter()
    result = session.execute(stmt, params)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    print(f"  {label:40s}  {elapsed_ms:7.2f} ms")
    return result


# demo 

def main() -> None:
    print(SEPARATOR)
    print("ScyllaDB – Tunable Consistency Demo  (3-node cluster)")
    print(SEPARATOR)

    cluster = Cluster(CONTACT_POINTS)
    session = cluster.connect()
    setup_schema(session)

    sensor = "temp-sensor-42"

    # Writes at different consistency levels
    print("\n WRITES")
    for cl_name, cl in [("ONE", ConsistencyLevel.ONE),
                         ("QUORUM", ConsistencyLevel.QUORUM),
                         ("ALL", ConsistencyLevel.ALL)]:
        stmt = SimpleStatement(
            "INSERT INTO sensor_data (sensor_id, ts, value) VALUES (%s, now(), %s)",
            consistency_level=cl,
        )
        timed_exec(session, stmt, (sensor, 23.5), label=f"INSERT  CL={cl_name}")

    # Reads at different consistency levels 
    print("\n📖 READS  (latest 5 rows)")
    for cl_name, cl in [("ONE", ConsistencyLevel.ONE),
                         ("QUORUM", ConsistencyLevel.QUORUM),
                         ("ALL", ConsistencyLevel.ALL)]:
        stmt = SimpleStatement(
            "SELECT sensor_id, ts, value FROM sensor_data "
            "WHERE sensor_id = %s LIMIT 5",
            consistency_level=cl,
        )
        result = timed_exec(session, stmt, (sensor,), label=f"SELECT  CL={cl_name}")
        for row in result:
            print(f"    → {row.sensor_id}  ts={row.ts}  value={row.value}")

    # Explain the trade-of
    print(f"""
{SEPARATOR}
Key take-away (ACID vs BASE)
{SEPARATOR}
  • CL=ONE   → BASE-like:  low latency, may read stale data
  • CL=QUORUM→ Tunable:    2-of-3 replicas agree – good balance
  • CL=ALL   → Strong:     all replicas must respond – highest latency

  If W + R > RF  you get strong consistency.
  Example: W=QUORUM(2) + R=QUORUM(2) > RF(3)  ✔  linearisable reads.
""")

    cluster.shutdown()
    print("Done.")


if __name__ == "__main__":
    main()
