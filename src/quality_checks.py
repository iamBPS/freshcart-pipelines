from src.db import get_connection


def quality_checks():
    c = get_connection()

    checks = [
        (
            "Gold order IDs must be unique",
            """
            SELECT COUNT(*) FROM (
                SELECT order_id
                FROM gold.orders
                GROUP BY order_id
                HAVING COUNT(*) > 1
            )
            """
        ),
        (
            "Gold order IDs must not be NULL",
            """
            SELECT COUNT(*)
            FROM gold.orders
            WHERE order_id IS NULL
            """
        ),
        (
            "Gold amounts must be positive",
            """
            SELECT COUNT(*)
            FROM gold.orders
            WHERE amount <= 0
            """
        ),
        (
            "Gold customer tiers must not be NULL",
            """
            SELECT COUNT(*)
            FROM gold.orders
            WHERE customer_tier IS NULL
            """
        ),
        (
            "Gold loyalty points must not be negative",
            """
            SELECT COUNT(*)
            FROM gold.orders
            WHERE loyalty_points < 0
            """
        ),
        (
            "Gold INR amount must exist when source amount exists",
            """
            SELECT COUNT(*)
            FROM gold.orders
            WHERE amount IS NOT NULL
              AND amount_inr IS NULL
            """
        )
    ]

    try:
        print("\\n=== FRESHCART DATA QUALITY CHECKS ===")

        all_passed = True

        for index, (name, query) in enumerate(checks, start=1):
            failed_rows = c.execute(query).fetchone()[0]
            status = "PASS" if failed_rows == 0 else "PROBLEM"

            if failed_rows != 0:
                all_passed = False

            print(
                f"Check {index}: {name} | "
                f"Failed rows: {failed_rows} | {status}"
            )

        print("\\nOverall:", "ALL CHECKS PASSED" if all_passed else "QUALITY ISSUES FOUND")

        return all_passed

    finally:
        c.close()


if __name__ == "__main__":
    quality_checks()
