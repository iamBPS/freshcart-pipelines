
CREATE OR REPLACE TABLE silver.orders_deduplicated AS
SELECT *
FROM silver.orders_clean
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY order_id
    ORDER BY updated_at DESC, ingest_seq DESC
) = 1;
