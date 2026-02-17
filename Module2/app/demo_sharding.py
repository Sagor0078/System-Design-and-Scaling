"""Simple manual sharding demo: range-based across two Postgres instances (ports 5432 and 5442).
This script chooses a shard by user id modulo or by region range.
"""
from app.db_utils import get_postgres_conn, init_schema, insert_user, get_user_by_id

SHARDS = [
    {"host": "localhost", "port": 5432},
    {"host": "localhost", "port": 5442},
]

def choose_shard_by_hash(name):
    return hash(name) % len(SHARDS)

def choose_shard_by_region(region):
    # simple range mapping: regions starting A-M -> shard0, N-Z -> shard1
    first = region[0].upper()
    if 'A' <= first <= 'M':
        return 0
    return 1

def main():
    # insert a few users
    for name, region in [("alice","asia"),("bob","europe"),("zoe","north")]:
        shard = choose_shard_by_region(region)
        cfg = SHARDS[shard]
        conn = get_postgres_conn(host=cfg['host'], port=cfg['port'])
        init_schema(conn)
        uid = insert_user(conn, name, region)
        print(f"Inserted {name} into shard {shard} id={uid}")

    # read back
    for shard_index, cfg in enumerate(SHARDS):
        conn = get_postgres_conn(host=cfg['host'], port=cfg['port'])
        print(f"Users on shard {shard_index} (port {cfg['port']}):")
        with conn.cursor() as cur:
            cur.execute("SELECT id,name,region FROM users;")
            for row in cur.fetchall():
                print(row)

if __name__ == '__main__':
    main()
