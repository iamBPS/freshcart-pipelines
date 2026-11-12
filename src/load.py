
import gzip
import json

from config import LANDING_DIR
from src.db import get_connection


SOURCE_TABLES = {
    "web": "orders_raw",
    "mobile": "orders_raw",
    "crm": "customers_raw",
    "fx": "fx_raw",
    "pincode": "pincode_raw",
}


def create_bronze_tables():
    conn = get_connection()
    try:
        conn.execute("""
            CREATE SCHEMA IF NOT EXISTS bronze;
            CREATE SEQUENCE IF NOT EXISTS bronze.bronze_ingest_seq START 1;

            CREATE TABLE IF NOT EXISTS bronze.orders_raw (
                ingest_seq BIGINT,
                source VARCHAR,
                run_id VARCHAR,
                extracted_at TIMESTAMP,
                raw_json VARCHAR
            );

            CREATE TABLE IF NOT EXISTS bronze.customers_raw (
                ingest_seq BIGINT,
                source VARCHAR,
                run_id VARCHAR,
                extracted_at TIMESTAMP,
                raw_json VARCHAR
            );

            CREATE TABLE IF NOT EXISTS bronze.fx_raw (
                ingest_seq BIGINT,
                source VARCHAR,
                run_id VARCHAR,
                extracted_at TIMESTAMP,
                raw_json VARCHAR
            );

            CREATE TABLE IF NOT EXISTS bronze.pincode_raw (
                ingest_seq BIGINT,
                source VARCHAR,
                run_id VARCHAR,
                extracted_at TIMESTAMP,
                raw_json VARCHAR
            );
        """)
    finally:
        conn.close()


def load_file(file_path):
    loaded = 0
    conn = get_connection()

    try:
        with gzip.open(file_path, "rt", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue

                envelope = json.loads(line)
                source = str(envelope.get("source", "")).lower()
                target_table = SOURCE_TABLES.get(source)

                if target_table is None:
                    raise ValueError(
                        f"Unknown source '{source}' in {file_path.name}"
                    )

                record = envelope.get("data", {})

                # Support both a single object and a list of objects.
                records = record if isinstance(record, list) else [record]

                rows = [
                    (
                        source,
                        envelope.get("run_id", ""),
                        envelope.get("extracted_at"),
                        json.dumps(item, ensure_ascii=False)
                    )
                    for item in records
                ]

                if rows:
                    conn.executemany(
                        f"""
                        INSERT INTO bronze.{target_table}
                            (ingest_seq, source, run_id, extracted_at, raw_json)
                        VALUES (
                            nextval('bronze.bronze_ingest_seq'),
                            ?, ?, CAST(? AS TIMESTAMP), ?
                        )
                        """,
                        rows
                    )
                    loaded += len(rows)

    finally:
        conn.close()

    print(f"{file_path.name}: {loaded} rows loaded")
    return loaded


def load_all(run_id):
    create_bronze_tables()

    files = sorted(LANDING_DIR.rglob(f"*__{run_id}.json.gz"))

    if not files:
        raise FileNotFoundError(
            f"No landing files found for run_id {run_id}"
        )

    total = 0
    for file_path in files:
        total += load_file(file_path)

    print(f"Total Bronze rows loaded: {total}")
    return total
