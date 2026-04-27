-- Run after Revitalash full sync completes.
-- Identifies Revitalash rows that landed in BRONZE_SHOPIFY_ISCLINICAL
-- and removes them, leaving only genuine isClinical data.

-- Step 1: Audit — how many order IDs overlap?
SELECT
    'overlapping_order_ids' AS check_name,
    COUNT(*) AS cnt
FROM HGI.BRONZE_SHOPIFY_ISCLINICAL.ORDERS isc
JOIN HGI.BRONZE_SHOPIFY_REVITALASH.ORDERS rev
    ON isc.id = rev.id

UNION ALL

-- Step 2: Date range sanity check per schema
SELECT 'isclinical_earliest', MIN(created_at::date)::varchar FROM HGI.BRONZE_SHOPIFY_ISCLINICAL.ORDERS
UNION ALL
SELECT 'isclinical_latest',   MAX(created_at::date)::varchar FROM HGI.BRONZE_SHOPIFY_ISCLINICAL.ORDERS
UNION ALL
SELECT 'isclinical_count',    COUNT(*)::varchar               FROM HGI.BRONZE_SHOPIFY_ISCLINICAL.ORDERS
UNION ALL
SELECT 'revitalash_earliest', MIN(created_at::date)::varchar FROM HGI.BRONZE_SHOPIFY_REVITALASH.ORDERS
UNION ALL
SELECT 'revitalash_latest',   MAX(created_at::date)::varchar FROM HGI.BRONZE_SHOPIFY_REVITALASH.ORDERS
UNION ALL
SELECT 'revitalash_count',    COUNT(*)::varchar               FROM HGI.BRONZE_SHOPIFY_REVITALASH.ORDERS;

-- Step 3: If overlapping_order_ids > 0, delete contamination from ISCLINICAL
-- (uncomment and run after reviewing Step 1 output)

/*
DELETE FROM HGI.BRONZE_SHOPIFY_ISCLINICAL.ORDERS
WHERE id IN (
    SELECT id FROM HGI.BRONZE_SHOPIFY_REVITALASH.ORDERS
);

DELETE FROM HGI.BRONZE_SHOPIFY_ISCLINICAL.CUSTOMERS
WHERE id IN (
    SELECT id FROM HGI.BRONZE_SHOPIFY_REVITALASH.CUSTOMERS
);

DELETE FROM HGI.BRONZE_SHOPIFY_ISCLINICAL.ORDER_LINE_ITEMS
WHERE order_id IN (
    SELECT id FROM HGI.BRONZE_SHOPIFY_REVITALASH.ORDERS
);

DELETE FROM HGI.BRONZE_SHOPIFY_ISCLINICAL.PRODUCTS
WHERE id IN (
    SELECT id FROM HGI.BRONZE_SHOPIFY_REVITALASH.PRODUCTS
);

DELETE FROM HGI.BRONZE_SHOPIFY_ISCLINICAL.PRODUCT_VARIANTS
WHERE id IN (
    SELECT id FROM HGI.BRONZE_SHOPIFY_REVITALASH.PRODUCT_VARIANTS
);
*/
