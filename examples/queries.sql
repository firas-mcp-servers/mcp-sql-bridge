-- Example SELECT queries to run via execute_readonly_query (SQLite sample.db).
-- Use these as inspiration; the AI can call the tool with query set to any of these.

-- List all users
SELECT * FROM users ORDER BY id;

-- Count orders per user
SELECT user_id, COUNT(*) AS order_count, SUM(total) AS total_amount
FROM orders
GROUP BY user_id
ORDER BY total_amount DESC;

-- Recent orders with user names (if you have a joinable schema)
-- SELECT u.name, o.id, o.total FROM orders o JOIN users u ON u.id = o.user_id ORDER BY o.id DESC LIMIT 10;
