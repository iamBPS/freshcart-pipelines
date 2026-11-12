
CREATE OR REPLACE TABLE silver.pincode_geo AS
SELECT DISTINCT
    json_extract_string(raw_json, '$.pincode') AS pincode,
    json_extract_string(raw_json, '$.city') AS city,
    json_extract_string(raw_json, '$.state') AS state
FROM bronze.pincode_raw
WHERE json_extract_string(raw_json, '$.pincode') IS NOT NULL;
