-- ============================================================
-- Mamaearth Growth Analytics — SQL Reports
-- ============================================================


-- ------------------------------------------------------------
-- a) Order totals
-- Expected: 180 orders, ₹99,860.20 revenue, ₹554.78 AOV
-- ------------------------------------------------------------
SELECT
    COUNT(*) AS total_orders,
    ROUND(
        SUM(
            quantity * price *
            (1 - COALESCE(discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_revenue,
    ROUND(
        AVG(
            quantity * price *
            (1 - COALESCE(discount_pct, 0) / 100.0)
        ),
        2
    ) AS avg_order_value
FROM orders
JOIN products
    ON orders.product_id = products.product_id;


-- ------------------------------------------------------------
-- b) Rating completeness
-- Expected: total_orders = 180, rated_orders = 165,
-- missing_ratings = 15
-- ------------------------------------------------------------
SELECT
    COUNT(*) AS total_orders,
    COUNT(rating) AS rated_orders,
    COUNT(*) - COUNT(rating) AS missing_ratings
FROM orders;


-- ------------------------------------------------------------
-- c) Customers with no orders
-- Expected: C045 — Vihaan
-- ------------------------------------------------------------
SELECT
    c.customer_id,
    c.name
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY
    c.customer_id,
    c.name
HAVING COUNT(o.order_id) = 0;


-- Independent NOT IN check
SELECT
    customer_id,
    name
FROM customers
WHERE customer_id NOT IN (
    SELECT customer_id
    FROM orders
);


-- ------------------------------------------------------------
-- d) Cities with return rate above 20%
-- Expected:
-- Jaipur     19 orders, 8 returned, 42.1%
-- Lucknow    49 orders, 15 returned, 30.6%
-- Bangalore  33 orders, 8 returned, 24.2%
-- ------------------------------------------------------------
SELECT
    c.city,
    COUNT(o.order_id) AS total_orders,
    SUM(o.returned) AS returned_orders,
    ROUND(
        100.0 * SUM(o.returned) / COUNT(o.order_id),
        1
    ) AS return_rate_pct
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.city
HAVING
    100.0 * SUM(o.returned) / COUNT(o.order_id) > 20
ORDER BY return_rate_pct DESC;


-- ------------------------------------------------------------
-- e) Top customers by total spend
-- Tie-break: customer_id ascending makes rankings deterministic.
-- ------------------------------------------------------------
SELECT
    c.customer_id,
    c.name,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_spend
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN products p
    ON o.product_id = p.product_id
GROUP BY
    c.customer_id,
    c.name
ORDER BY
    total_spend DESC,
    c.customer_id ASC
LIMIT 5;


-- Ranks 3–5
SELECT
    c.customer_id,
    c.name,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_spend
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN products p
    ON o.product_id = p.product_id
GROUP BY
    c.customer_id,
    c.name
ORDER BY
    total_spend DESC,
    c.customer_id ASC
LIMIT 3 OFFSET 2;


-- ------------------------------------------------------------
-- f) Revenue and orders by product category
-- ------------------------------------------------------------
SELECT
    p.category,
    COUNT(o.order_id) AS total_orders,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_revenue
FROM products p
JOIN orders o
    ON p.product_id = o.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;


-- ------------------------------------------------------------
-- g) Customers whose name starts with A
-- Expected: exactly 10 customers
-- ------------------------------------------------------------
SELECT
    customer_id,
    name,
    city
FROM customers
WHERE name LIKE 'A%'
ORDER BY name;


-- ------------------------------------------------------------
-- h) Distinct acquisition sources
-- Expected: Ad, Organic, Referral, Social
-- ------------------------------------------------------------
SELECT DISTINCT
    acquisition_source
FROM customers
ORDER BY acquisition_source;


-- ------------------------------------------------------------
-- i) Add loyalty tier
-- Tier 1 = Gold
-- Other tiers = Silver
-- ------------------------------------------------------------
ALTER TABLE customers
ADD COLUMN loyalty_tier VARCHAR(10);

UPDATE customers
SET loyalty_tier =
    CASE
        WHEN city_tier = 1 THEN 'Gold'
        ELSE 'Silver'
    END;


-- Check loyalty tier counts
SELECT
    loyalty_tier,
    COUNT(*) AS customer_count
FROM customers
GROUP BY loyalty_tier
ORDER BY loyalty_tier;
