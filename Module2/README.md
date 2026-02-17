# Module 2 — Databases & Storage

> **Goal:** Learn how to scale and structure data — replication, sharding,
> backup/restore, and consistency trade-offs — through working code.

---

## Architecture

```
                          ┌────────────┐
                          │   Client   │  (Python demos)
                          └─────┬──────┘
            ┌───────────────────┼───────────────────┐
            │                   │                   │
     ┌──────▼──────┐    ┌──────▼──────┐    ┌───────▼──────┐
     │ PostgreSQL   │    │  ScyllaDB   │    │   MongoDB    │
     │              │    │ (3-node)    │    │  (RS rs0)    │
     │ primary:5432 │    │  n1 :9042   │    │    :27017    │
     │ replica:5433 │    │  n2 :9142   │    └──────────────┘
     │ shard2 :5442 │    │  n3 :9242   │
     └──────────────┘    └─────────────┘
```

### What each service teaches

| Service | Concept | Demo script |
|---------|---------|-------------|
| pg-primary + pg-replica | Leader-follower replication, WAL streaming | `demo_replication.py` |
| pg-primary + pg-shard2 | Manual range / hash partitioning | `demo_sharding.py` |
| ScyllaDB 3-node cluster | Tunable consistency (ONE / QUORUM / ALL) | `scylla_demo.py` |
| MongoDB replica-set | Strong vs eventual consistency, write concern | `mongo_consistency_demo.py` |

---

## Prerequisites

* **Docker** ≥ 24 and **Docker Compose** v2+
* **Python** ≥ 3.10

---

## Quick start

### 1. Start the infrastructure

```bash
cd Module2
docker compose up -d
```

Wait ~30 s for ScyllaDB healthchecks to pass:

```bash
docker compose ps          # all services should show "healthy"
```

### 2. One-time MongoDB replica-set init

```bash
docker exec mongodb mongosh --eval "rs.initiate()"
```

### 3. Install Python dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # or: pip install -e .
```

### 4. Run the demos

```bash
# Postgres replication (write → primary, read → replica)
python -m module2_app.demo_replication

# Manual sharding (range + hash across two Postgres instances)
python -m module2_app.demo_sharding

# ScyllaDB tunable consistency (ONE / QUORUM / ALL)
python -m module2_app.scylla_demo

# MongoDB strong vs eventual consistency
python -m module2_app.mongo_consistency_demo
```

### 5. Backup & restore

#### PostgreSQL

```bash
chmod +x backup_restore.sh

# Backup primary
./backup_restore.sh backup

# Backup shard-2
./backup_restore.sh backup shard2

# List backups
./backup_restore.sh list

# Restore a dump to primary
./backup_restore.sh restore backups/<dumpfile> primary
```

#### ScyllaDB

```bash
chmod +x scylla_backup.sh

# Snapshot all 3 nodes
./scylla_backup.sh snapshot

# List snapshots on node-1
./scylla_backup.sh list scylla-node1

# Clear old snapshots
./scylla_backup.sh clear
```

---

## Topics covered (theory + code)

### SQL vs NoSQL — Trade-offs

| | PostgreSQL (SQL) | ScyllaDB / MongoDB (NoSQL) |
|---|---|---|
| Schema | Rigid, predefined | Flexible / schema-less |
| Joins | Native SQL joins | De-normalised / app-side |
| Consistency | Strong (ACID) | Tunable / eventual (BASE) |
| Scale pattern | Vertical + read replicas | Horizontal (auto-sharding) |

### Indexing & B+ Trees

PostgreSQL stores every index as a B+ tree by default. Run inside `psql`
on the primary to see:

```sql
-- Create an index and inspect its type
CREATE INDEX idx_users_region ON users (region);
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'users';
```

### Leader-Follower Replication & WAL

* The primary streams WAL (Write-Ahead Log) segments to the replica.
* Config lives in `conf/pg-primary.conf` (`wal_level=replica`).
* `demo_replication.py` writes to primary and reads from replica.

### Sharding & Partitioning

* `demo_sharding.py` manually routes writes across two Postgres
  instances using **range** (region first-letter) and **hash** (MD5 mod N)
  strategies.
* In production, use Postgres native partitioning (`PARTITION BY RANGE/HASH`)
  or a distributed layer (Citus, Vitess).

### Hot / Cold Storage

A common pattern: keep recent (hot) data in Scylla/Postgres and archive
older (cold) data to object storage (S3) or compressed tables.

### Backup & Restore strategies

| Tool | What it does |
|------|-------------|
| `pg_dump / pg_restore` | Logical backup – portable, slower for large DBs |
| `pg_basebackup` | Physical backup – fast, used for replica init |
| `nodetool snapshot` | ScyllaDB SSTable snapshot – fast, node-level |

### ACID vs BASE & Consistency Models

| Property | ACID (Postgres) | BASE (ScyllaDB / Mongo) |
|----------|----------------|------------------------|
| Atomicity | Full transactions | Per-partition atomic |
| Consistency | Immediate | Eventual / tunable |
| Isolation | Serializable / MVCC | Lightweight transactions |
| Durability | WAL + fsync | Commit log + hinted handoff |

The Scylla demo shows: **W + R > RF → strong consistency**.
For RF=3, QUORUM writes + QUORUM reads = 2 + 2 > 3 ✔

---

## File layout

```
Module2/
├── docker-compose.yml          # all services
├── conf/
│   ├── pg-primary.conf         # WAL / replication settings
│   └── pg_hba_replica.conf     # replica auth rules
├── scripts/
│   └── init-replica.sh         # placeholder for replica entrypoint
├── module2_app/
│   ├── __init__.py
│   ├── db.py                   # shared Postgres helpers
│   ├── demo_replication.py     # leader-follower demo
│   ├── demo_sharding.py        # range & hash sharding demo
│   ├── scylla_demo.py          # tunable consistency demo
│   └── mongo_consistency_demo.py # strong vs eventual demo
├── backup_restore.sh           # pg_dump / pg_restore wrapper
├── scylla_backup.sh            # nodetool snapshot wrapper
├── requirements.txt
├── pyproject.toml
└── README.md                   
```

---

## Cleanup

```bash
docker compose down -v          # remove containers + volumes
```
