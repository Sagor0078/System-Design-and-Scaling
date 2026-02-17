import psycopg
from psycopg.rows import dict_row
import os

def get_postgres_conn(host="localhost", port=5432, dbname="module2_db", user="postgres", password="example"):
    conn = psycopg.connect(host=host, port=port, dbname=dbname, user=user, password=password)
    return conn

def init_schema(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name TEXT, region TEXT);")
        conn.commit()

def insert_user(conn, name, region):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO users (name, region) VALUES (%s, %s) RETURNING id;", (name, region))
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id

def get_user_by_id(conn, user_id):
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
        return cur.fetchone()
