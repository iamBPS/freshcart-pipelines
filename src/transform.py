
from config import SQL_DIR
from src.db import get_connection


SQL_FILES = [
    "00_setup.sql",
    "10_orders_clean.sql",
    "20_orders_dedup.sql",
    "30_customers_scd2.sql",
    "31_fx_daily.sql",
    "32_pincode_geo.sql",
    "40_gold.sql",
]


def run_transformations():
    with get_connection() as conn:
        for filename in SQL_FILES:
            sql_path = SQL_DIR / filename
            print(f"Running {filename}...")
            conn.execute(sql_path.read_text(encoding="utf-8"))

    print("All transformation stages completed.")
