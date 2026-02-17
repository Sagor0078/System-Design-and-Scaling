"""Demo: write to primary and read from replica (reads on port 5433).
Note: the docker-compose replica uses base backup; additional replication user setup may be required.
"""
from app.db_utils import get_postgres_conn, init_schema, insert_user

def main():
    primary = get_postgres_conn(port=5432)
    init_schema(primary)
    uid = insert_user(primary, 'replica_user', 'eu')
    print('Inserted on primary id=', uid)

    # read from replica
    replica = get_postgres_conn(port=5433)
    with replica.cursor() as cur:
        cur.execute('SELECT id,name,region FROM users WHERE id = %s;', (uid,))
        row = cur.fetchone()
        print('Read from replica:', row)

if __name__ == '__main__':
    main()
