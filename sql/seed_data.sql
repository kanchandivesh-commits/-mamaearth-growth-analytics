-- Clear existing data so the seed can be re-run safely
DELETE FROM orders;
DELETE FROM products;
DELETE FROM customers;

-- Import the raw CSV files
.mode csv

.import --skip 1 data/customers.csv customers
.import --skip 1 data/products.csv products
.import --skip 1 data/orders.csv orders

-- Convert intentionally blank CSV cells into SQL NULLs
UPDATE orders
SET discount_pct = NULL
WHERE discount_pct = '';

UPDATE orders
SET rating = NULL
WHERE rating = '';
