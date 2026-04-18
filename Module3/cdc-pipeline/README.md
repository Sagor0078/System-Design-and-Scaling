# CDC Pipeline — Change Data Capture with PostgreSQL, Debezium & Kafka

A complete, containerised **Change Data Capture** demo.  
Every `INSERT`, `UPDATE`, or `DELETE` on the PostgreSQL `student` table is automatically streamed to an Apache Kafka topic via **Debezium**, and a Python consumer prints each event in real-time.

---

## Architecture

```
┌─────────────┐      WAL (logical)      ┌───────────┐      Kafka topic       ┌──────────────┐
│  PostgreSQL  │  ───────────────────▶   │  Debezium  │  ──────────────────▶  │ Kafka Broker │
│  (student)   │                        │  Connect   │   cdc.public.student  │              │
└─────────────┘                         └───────────┘                        └──────┬───────┘
       ▲                                                                           │
       │  SQL (Insert/Update/Delete)                                               │  consume
       │                                                                           ▼
┌──────┴───────┐                                                          ┌────────────────┐
│  db_operations│                                                          │ kafka_consumer  │
│  (Python CLI) │                                                          │ (Python)        │
└──────────────┘                                                          └────────────────┘
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Docker & Docker Compose | ≥ 24.x / Compose V2 |
| Python | ≥ 3.10 |

---

## Quick Start

### 1. Start the infrastructure

```bash
cd Module3/cdc-pipeline
docker compose up -d
```

Wait ~30 seconds for all services to become healthy:

```bash
docker compose ps
```

You should see **postgres**, **zookeeper**, **kafka**, **schema-registry**, **debezium**, and **kafka-ui** all running.

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Register the Debezium connector

```bash
python connector/register_connector.py --wait
```

This waits for Debezium to be ready, then registers a connector that watches the `public.student` table.

### 4. Start the Kafka consumer

Open a **new terminal**:

```bash
python consumer/kafka_consumer.py
```

You should immediately see snapshot events for the two seeded rows (`Alice`, `Bob`).

### 5. Make database changes

Open **another terminal**:

```bash
python producer/db_operations.py
```

Use the interactive menu to INSERT, UPDATE, or DELETE students.  
Switch back to the consumer terminal — every change will appear in real-time with a **before / after** diff table.

---

## Kafka UI

A web dashboard is included at **http://localhost:8080**.  
Browse topics, inspect messages, and check the Debezium connector status visually.

---

## Project Structure

```
cdc-pipeline/
├── docker-compose.yml          # All infrastructure services
├── requirements.txt            # Python dependencies
├── init-db/
│   └── init.sql                # Creates student table + seeds data
├── connector/
│   └── register_connector.py   # Registers Debezium connector via REST API
├── producer/
│   └── db_operations.py        # Interactive CLI for DB changes
├── consumer/
│   └── kafka_consumer.py       # Real-time CDC event consumer
└── README.md
```

---

## How It Works

1. **PostgreSQL** is configured with `wal_level=logical` so it emits logical replication events.
2. **Debezium** connects to PostgreSQL using the `pgoutput` plugin, reads the WAL, and publishes change events to the Kafka topic `cdc.public.student`.
3. Each event is a JSON document containing:
   - `op` — operation type (`c` = create, `u` = update, `d` = delete, `r` = snapshot read)
   - `before` — the row state *before* the change (null for inserts)
   - `after` — the row state *after* the change (null for deletes)
   - `source` — metadata (LSN, timestamp, table name, etc.)
4. The **Python consumer** deserialises these events and renders them as rich tables in the terminal.

---

## Useful Commands

```bash
# Check connector status
curl -s http://localhost:8083/connectors/cdc-postgres-connector/status | python -m json.tool

# List Kafka topics
docker exec cdc_kafka kafka-topics --bootstrap-server kafka:9092 --list

# Read raw topic messages
docker exec cdc_kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic cdc.public.student \
  --from-beginning

# Tear everything down (including volumes)
docker compose down -v
```

---

## Extending This Demo

| Use Case | How |
|----------|-----|
| **Add more tables** | Update `table.include.list` in `register_connector.py` to `"public.student,public.course"` |
| **Elasticsearch sync** | Add a consumer that indexes every CDC event into Elasticsearch |
| **Cache invalidation** | Add a consumer that deletes/updates Redis keys on changes |
| **Notifications** | Add a consumer that sends webhooks or emails on certain events |
| **Schema Registry (Avro)** | Switch the converter to `io.confluent.connect.avro.AvroConverter` in the connector config |

---

