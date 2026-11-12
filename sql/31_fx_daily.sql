
CREATE OR REPLACE TABLE silver.fx_rates AS

WITH extracted_rates AS (
    SELECT
        try_cast(j.key AS DATE) AS rate_date,
        'USD' AS currency,
        try_cast(
            json_extract_string(j.value, '$.INR')
            AS DECIMAL(12,4)
        ) AS rate,
        f.ingest_seq
    FROM bronze.fx_raw f,
         json_each(json_extract(f.raw_json, '$.rates')) AS j

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY j.key
        ORDER BY f.ingest_seq DESC
    ) = 1
),

date_bounds AS (
    SELECT
        min(order_date) AS min_date,
        max(order_date) AS max_date
    FROM silver.orders_deduplicated
),

calendar AS (
    SELECT
        unnest(
            generate_series(min_date, max_date, INTERVAL 1 DAY)
        )::DATE AS rate_date
    FROM date_bounds
),

currencies AS (
    SELECT DISTINCT currency
    FROM silver.orders_deduplicated
),

grid AS (
    SELECT
        d.rate_date,
        c.currency
    FROM calendar d
    CROSS JOIN currencies c
),

joined AS (
    SELECT
        g.rate_date,
        g.currency,
        r.rate
    FROM grid g
    LEFT JOIN extracted_rates r
        ON r.rate_date = g.rate_date
       AND r.currency = g.currency
)

SELECT
    rate_date,
    currency,
    CASE
        WHEN currency = 'INR' THEN 1.0000
        ELSE last_value(rate IGNORE NULLS) OVER (
            PARTITION BY currency
            ORDER BY rate_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )
    END AS rate_to_inr
FROM joined;
