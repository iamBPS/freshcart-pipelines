
from src.db import get_connection


def get_value(conn, query):
    return conn.execute(query).fetchone()[0]



def test_pipeline_expected_counts():
    with get_connection() as conn:
        unique_bronze_orders = get_value(
            conn,
            """
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT source, raw_json
                FROM bronze.orders_raw
            )
            """
        )

        assert unique_bronze_orders == 8

        assert get_value(
            conn, "SELECT COUNT(*) FROM silver.orders_clean"
        ) == 6

        assert get_value(
            conn, "SELECT COUNT(*) FROM quarantine.orders_rejected"
        ) == 2

        assert get_value(
            conn, "SELECT COUNT(*) FROM silver.orders_deduplicated"
        ) == 4

        assert get_value(
            conn, "SELECT COUNT(*) FROM gold.orders"
        ) == 4


def test_gold_revenue():
    with get_connection() as conn:
        revenue = get_value(
            conn, "SELECT ROUND(SUM(amount_inr), 2) FROM gold.orders"
        )
        assert float(revenue) == 7785.00


def test_loyalty_points():
    with get_connection() as conn:
        points = get_value(
            conn, "SELECT SUM(loyalty_points) FROM gold.orders"
        )
        assert points == 161


def test_no_duplicate_gold_orders():
    with get_connection() as conn:
        total = get_value(
            conn, "SELECT COUNT(*) FROM gold.orders"
        )
        unique = get_value(
            conn, "SELECT COUNT(DISTINCT order_id) FROM gold.orders"
        )
        assert total == unique
