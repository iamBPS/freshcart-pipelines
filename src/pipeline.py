
from datetime import datetime, timezone

from src.extract import extract_all
from src.load import load_all
from src.transform import run_transformations
from src.db import get_connection


def show_results():
    queries = {
        "Bronze orders": "SELECT COUNT(*) FROM bronze.orders_raw",
        "Silver cleaned": "SELECT COUNT(*) FROM silver.orders_clean",
        "Quarantine": "SELECT COUNT(*) FROM quarantine.orders_rejected",
        "Deduplicated": "SELECT COUNT(*) FROM silver.orders_deduplicated",
        "Gold orders": "SELECT COUNT(*) FROM gold.orders",
        "Gold revenue": "SELECT ROUND(SUM(amount_inr), 2) FROM gold.orders",
        "Loyalty points": "SELECT SUM(loyalty_points) FROM gold.orders",
    }

    with get_connection() as conn:
        print("\n========== FRESHCART PIPELINE RESULTS ==========")
        for label, query in queries.items():
            result = conn.execute(query).fetchone()[0]
            print(f"{label}: {result}")
        print("================================================")


def run_pipeline():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    print(f"Starting FreshCart ELT pipeline: {run_id}")

    extract_all(run_id)
    load_all(run_id)
    run_transformations()
    show_results()

    print("\nFreshCart ELT pipeline completed.")


if __name__ == "__main__":
    run_pipeline()
