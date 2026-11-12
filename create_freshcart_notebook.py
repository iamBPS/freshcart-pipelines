import nbformat as nbf
from pathlib import Path

notebook = nbf.v4.new_notebook()
cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbf.v4.new_code_cell(text))

md("""# FreshCart ELT Pipeline

## Data Engineering Assignment – Part B

This notebook documents the FreshCart Extract, Load and Transform (ELT) pipeline.

**Implementation disclosure:** This project uses a local DuckDB database. The SQL transformations are adapted for DuckDB and are not presented as Snowflake execution evidence.

### Pipeline architecture

Extract → Landing → Bronze → Silver / Quarantine → Gold

The pipeline processes Web, Mobile, CRM, FX and Pincode source data.
""")

md("## 1. Import Libraries and Connect to the Database")

code("""import pandas as pd
from IPython.display import display
from src.db import get_connection

con = get_connection()
print("Connected to FreshCart DuckDB database successfully.")
""")

md("## 2. Extract Source Data")

code("""from datetime import datetime, timezone
from src.extract import extract_all

run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

print("Extraction run ID:", run_id)
extract_all(run_id)

print("\\nSource extraction completed.")
""")

md("## 3. Load Extracted Data into Bronze")

code("""from src.load import load_all

load_all(run_id)

bronze_summary = con.execute(\"\"\"
SELECT COUNT(*) AS bronze_order_records
FROM bronze.orders_raw
\"\"\").df()

display(bronze_summary)
""")

md("## 4. Execute SQL Transformations")

code("""from src.transform import run_transformations

run_transformations()

print("All SQL transformation stages completed.")
""")

md("## 5. Inspect Silver and Quarantine Layers")

code("""print("Silver cleaned orders")
display(con.execute(
    "SELECT * FROM silver.orders_clean ORDER BY order_id"
).df())

print("Quarantined records")
display(con.execute(
    "SELECT * FROM quarantine.orders_rejected"
).df())
""")

md("## 6. Order Deduplication")

code("""dedup_df = con.execute(\"\"\"
SELECT *
FROM silver.orders_deduplicated
ORDER BY order_id
\"\"\").df()

display(dedup_df)
print("Deduplicated order count:", len(dedup_df))
""")

md("## 7. Customer SCD Type 2 History")

code("""customer_history = con.execute(
    "SELECT * FROM dim.customers ORDER BY customer_id"
).df()

display(customer_history)
""")

md("## 8. FX and Pincode Reference Data")

code("""print("Daily foreign exchange rates")
display(con.execute(
    "SELECT * FROM ref.fx_daily ORDER BY rate_date"
).df())

print("Pincode geographic reference data")
display(con.execute(
    "SELECT * FROM ref.pincode_geo"
).df())
""")

md("## 9. Gold Analytical Layer")

code("""gold_df = con.execute(\"\"\"
SELECT *
FROM gold.orders
ORDER BY order_id
\"\"\").df()

display(gold_df)
""")

md("## 10. Revenue and Loyalty Summary")

code("""gold_summary = con.execute(\"\"\"
SELECT
    COUNT(*) AS total_gold_orders,
    ROUND(SUM(amount_inr), 2) AS total_revenue_inr,
    SUM(loyalty_points) AS total_loyalty_points
FROM gold.orders
\"\"\").df()

display(gold_summary)
""")

md("## 11. Data Quality Checks")

code("""from src.quality_checks import quality_checks

quality_passed = quality_checks()

print("All data quality checks passed:", quality_passed)
""")

md("## 12. Final Pipeline Summary")

code("""summary_queries = {
    "Bronze orders": "SELECT COUNT(*) FROM bronze.orders_raw",
    "Silver cleaned": "SELECT COUNT(*) FROM silver.orders_clean",
    "Quarantine": "SELECT COUNT(*) FROM quarantine.orders_rejected",
    "Deduplicated": "SELECT COUNT(*) FROM silver.orders_deduplicated",
    "Gold orders": "SELECT COUNT(*) FROM gold.orders",
    "Gold revenue (INR)": "SELECT ROUND(SUM(amount_inr), 2) FROM gold.orders",
    "Loyalty points": "SELECT SUM(loyalty_points) FROM gold.orders"
}

summary = []

for metric, query in summary_queries.items():
    value = con.execute(query).fetchone()[0]
    summary.append({"Metric": metric, "Result": value})

summary_df = pd.DataFrame(summary)
display(summary_df)

con.close()
print("FreshCart ELT notebook execution completed.")
""")

notebook["cells"] = cells
notebook["metadata"] = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    },
    "language_info": {
        "name": "python"
    }
}

output = Path("elt/FreshCart_ELT.ipynb")
output.parent.mkdir(parents=True, exist_ok=True)

nbf.write(notebook, output)

print("Notebook created:", output.resolve())
print("Total cells:", len(cells))
