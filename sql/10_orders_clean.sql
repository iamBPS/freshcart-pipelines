
CREATE OR REPLACE TEMP TABLE orders_stage AS
WITH all_source_data AS (
    SELECT
        ingest_seq,
        source,
        run_id,
        raw_json,
        json_extract_string(raw_json, '$.order_id') AS order_id,
        json_extract_string(raw_json, '$.cust_email') AS email_raw,
        json_extract_string(raw_json, '$.cust_name') AS name_raw,
        json_extract_string(raw_json, '$.order_date') AS date_raw,
        json_extract_string(raw_json, '$.amount') AS amount_raw,
        json_extract_string(raw_json, '$.currency') AS currency_raw,
        json_extract_string(raw_json, '$.pincode') AS pincode_raw,
        json_extract_string(raw_json, '$.updated_at') AS updated_raw
    FROM bronze.orders_raw
    WHERE source = 'web'

    UNION ALL

    SELECT
        ingest_seq,
        source,
        run_id,
        raw_json,
        json_extract_string(raw_json, '$.orderId'),
        json_extract_string(raw_json, '$.customer.email'),
        json_extract_string(raw_json, '$.customer.name'),
        json_extract_string(raw_json, '$.orderDate'),
        json_extract_string(raw_json, '$.total.value'),
        json_extract_string(raw_json, '$.total.currency'),
        json_extract_string(raw_json, '$.deliveryPin'),
        json_extract_string(raw_json, '$.updatedAt')
    FROM bronze.orders_raw
    WHERE source = 'mobile'
),
source_data AS (
    SELECT *
    FROM all_source_data
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY source, raw_json
        ORDER BY ingest_seq DESC
    ) = 1
),
parsed AS (
    SELECT
        ingest_seq,
        source,
        run_id,
        trim(order_id) AS order_id,
        lower(trim(email_raw)) AS customer_email,
        trim(name_raw) AS name_raw,
        COALESCE(
            try_strptime(trim(date_raw), '%Y-%m-%d'),
            try_strptime(trim(date_raw), '%d/%m/%Y'),
            try_strptime(trim(date_raw), '%b %d, %Y')
        )::DATE AS order_date,
        try_cast(
            regexp_replace(
                trim(amount_raw),
                '[₹,$ ]',
                '',
                'g'
            ) AS DECIMAL(12,2)
        ) AS amount,
        upper(trim(currency_raw)) AS currency,
        trim(pincode_raw) AS pincode,
        try_cast(trim(updated_raw) AS TIMESTAMP) AS updated_at,
        amount_raw
    FROM source_data
),
validated AS (
    SELECT
        *,
        concat_ws(
            '|',
            CASE
                WHEN order_id IS NULL OR order_id = ''
                THEN 'missing_order_id'
            END,
            CASE
                WHEN customer_email IS NULL OR NOT regexp_full_match(
                    customer_email,
                    '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}'
                )
                THEN 'invalid_email'
            END,
            CASE WHEN order_date IS NULL
                THEN 'invalid_order_date'
            END,
            CASE
                WHEN amount IS NOT NULL AND amount <= 0
                THEN 'non_positive_amount'
            END,
            CASE
                WHEN amount_raw IS NOT NULL AND amount IS NULL
                THEN 'invalid_amount'
            END,
            CASE
                WHEN currency NOT IN ('INR', 'USD')
                THEN 'unsupported_currency'
            END,
            CASE
                WHEN pincode IS NULL OR NOT regexp_full_match(
                    pincode, '[0-9]{6}'
                )
                THEN 'invalid_pincode'
            END,
            CASE
                WHEN updated_at IS NULL
                THEN 'invalid_updated_at'
            END
        ) AS rejection_reasons
    FROM parsed
)
SELECT * FROM validated;

CREATE OR REPLACE TABLE silver.orders_clean AS
SELECT
    ingest_seq,
    source,
    run_id,
    order_id,
    customer_email,
    CASE
        WHEN name_raw IS NULL OR trim(name_raw) = '' THEN NULL
        ELSE upper(substr(
            regexp_replace(trim(name_raw), '\\.$', ''), 1, 1
        )) || lower(substr(
            regexp_replace(trim(name_raw), '\\.$', ''), 2
        ))
    END AS customer_name,
    order_date,
    amount,
    currency,
    pincode,
    updated_at
FROM orders_stage
WHERE rejection_reasons = '';

CREATE OR REPLACE TABLE quarantine.orders_rejected AS
SELECT
    ingest_seq,
    source,
    run_id,
    order_id,
    rejection_reasons,
    'REJECTED' AS record_status
FROM orders_stage
WHERE rejection_reasons <> '';
