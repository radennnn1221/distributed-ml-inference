import psycopg2
from psycopg2.extras import RealDictCursor

from backend.config import PRIMARY_CONFIG, REPLICA_CONFIG

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS mahasiswa (
        id SERIAL PRIMARY KEY,
        nama TEXT NOT NULL,
        jurusan TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS inference_results (
        id BIGSERIAL PRIMARY KEY,
        sepal_length DOUBLE PRECISION NOT NULL,
        sepal_width DOUBLE PRECISION NOT NULL,
        petal_length DOUBLE PRECISION NOT NULL,
        petal_width DOUBLE PRECISION NOT NULL,
        prediction TEXT NOT NULL,
        confidence DOUBLE PRECISION NOT NULL,
        subject TEXT,
        model_name TEXT NOT NULL DEFAULT 'Random Forest',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
]


def get_connection(config):
    return psycopg2.connect(**config)


def ensure_schema():
    conn = get_connection(PRIMARY_CONFIG)
    try:
        with conn:
            with conn.cursor() as cursor:
                for statement in SCHEMA_STATEMENTS:
                    cursor.execute(statement)
    finally:
        conn.close()


def write_data(query, params=None):
    conn = get_connection(PRIMARY_CONFIG)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    return cursor.fetchall()
    finally:
        conn.close()


def read_data(query, params=None):
    conn = get_connection(REPLICA_CONFIG)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        conn.close()
