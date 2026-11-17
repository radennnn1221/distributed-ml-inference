#!/bin/bash
set -e

: "${PRIMARY_HOST:=postgres-primary}"
: "${PRIMARY_PORT:=5432}"
: "${REPLICATION_USER:=replicator}"
: "${PGDATA:=/var/lib/postgresql/data}"

until pg_isready -h "$PRIMARY_HOST" -p "$PRIMARY_PORT" -U "${POSTGRES_USER:-admin}"; do
  echo "Menunggu PostgreSQL Primary siap..."
  sleep 2
done

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  echo "Data replica kosong, menjalankan pg_basebackup dari $PRIMARY_HOST..."
  find "$PGDATA" -mindepth 1 -delete 2>/dev/null || true
  chown -R postgres:postgres "$PGDATA"
  gosu postgres pg_basebackup \
    -h "$PRIMARY_HOST" \
    -p "$PRIMARY_PORT" \
    -D "$PGDATA" \
    -U "$REPLICATION_USER" \
    -Fp -Xs -P -R -w
fi

chown -R postgres:postgres "$PGDATA"
exec gosu postgres postgres
