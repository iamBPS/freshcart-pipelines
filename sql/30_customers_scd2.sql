
CREATE OR REPLACE TABLE silver.customer_tier_history AS
WITH raw_events AS (
    SELECT
        ingest_seq,
        json_extract_string(raw_json, '$.cust_id') AS customer_id,
        lower(trim(json_extract_string(raw_json, '$.email'))) AS email,

        upper(substr(
            trim(json_extract_string(raw_json, '$.tier')), 1, 1
        )) ||
        lower(substr(
            trim(json_extract_string(raw_json, '$.tier')), 2
        )) AS tier,

        try_cast(
            json_extract_string(raw_json, '$.effective_from') AS DATE
        ) AS valid_from

    FROM bronze.customers_raw
),
events AS (
    SELECT *
    FROM raw_events
    WHERE email IS NOT NULL
      AND valid_from IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY customer_id, email, tier, valid_from
        ORDER BY ingest_seq DESC
    ) = 1
),
ordered AS (
    SELECT
        customer_id,
        email,
        tier,
        valid_from,
        LEAD(valid_from) OVER (
            PARTITION BY email
            ORDER BY valid_from
        ) AS next_valid_from
    FROM events
)
SELECT
    customer_id,
    email,
    tier,
    valid_from,
    (next_valid_from - INTERVAL 1 DAY)::DATE AS valid_to,
    next_valid_from IS NULL AS is_current
FROM ordered;
