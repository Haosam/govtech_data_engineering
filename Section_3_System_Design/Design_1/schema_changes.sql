ALTER TABLE members
ADD COLUMN IF NOT EXISTS membership_status VARCHAR(20)
NOT NULL DEFAULT 'active';

ALTER TABLE sales_transactions
ADD COLUMN IF NOT EXISTS transaction_status VARCHAR(20)
NOT NULL DEFAULT 'pending';

ALTER TABLE sales_transactions
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;