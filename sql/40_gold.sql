
CREATE OR REPLACE TABLE gold.orders AS
WITH enriched AS (
    SELECT
        o.order_id,
        o.customer_email,
        o.customer_name,
        o.order_date,
        o.amount,
        o.currency,
        o.pincode,
        o.updated_at,
        COALESCE(c.tier, 'Silver') AS customer_tier,
        f.rate_to_inr,
        g.city,
        g.state,
        o.amount * f.rate_to_inr AS amount_inr
    FROM silver.orders_deduplicated o
    LEFT JOIN silver.customer_tier_history c
      ON c.email = o.customer_email
     AND o.order_date >= c.valid_from
     AND (c.valid_to IS NULL OR o.order_date <= c.valid_to)
    LEFT JOIN silver.fx_rates f
      ON f.rate_date = o.order_date
     AND f.currency = o.currency
    LEFT JOIN silver.pincode_geo g
      ON g.pincode = o.pincode
)
SELECT
    *,
    CAST(
        FLOOR(amount_inr / 100) *
        CASE customer_tier
            WHEN 'Silver' THEN 1
            WHEN 'Gold' THEN 2
            WHEN 'Platinum' THEN 3
            ELSE 1
        END AS INTEGER
    ) AS loyalty_points
FROM enriched;

CREATE OR REPLACE TABLE gold.daily_revenue AS
SELECT
    order_date,
    ROUND(SUM(amount_inr), 2) AS total_revenue_inr,
    COUNT(*) AS total_orders
FROM gold.orders
GROUP BY order_date
ORDER BY order_date;
