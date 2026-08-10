-- ============================================================
-- Roles
-- ============================================================

CREATE ROLE logistics_role NOLOGIN;
CREATE ROLE analytics_role NOLOGIN;
CREATE ROLE sales_role NOLOGIN;


-- ============================================================
-- Schema access
-- ============================================================

GRANT USAGE ON SCHEMA public
TO logistics_role, analytics_role, sales_role;


-- ============================================================
-- Logistics
-- ============================================================

GRANT SELECT
ON sales_transactions,
   transaction_items,
   items
TO logistics_role;

GRANT UPDATE (
    transaction_status,
    completed_at
)
ON sales_transactions
TO logistics_role;


-- ============================================================
-- Analytics
-- ============================================================

GRANT SELECT
ON members,
   manufacturers,
   items,
   sales_transactions,
   transaction_items
TO analytics_role;


-- ============================================================
-- Sales
-- ============================================================

GRANT SELECT, INSERT, UPDATE, DELETE
ON items
TO sales_role;

GRANT SELECT
ON manufacturers
TO sales_role;