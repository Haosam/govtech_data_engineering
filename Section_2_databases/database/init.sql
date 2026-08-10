-- ============================================================
-- Members
-- ============================================================

CREATE TABLE members (
    membership_id VARCHAR(255) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(320) NOT NULL UNIQUE,
    date_of_birth DATE NOT NULL,
    mobile_no VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- Manufacturers
-- ============================================================

CREATE TABLE manufacturers (
    manufacturer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    manufacturer_name VARCHAR(255) NOT NULL UNIQUE
);


-- ============================================================
-- Items
-- ============================================================

CREATE TABLE items (
    item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    manufacturer_id BIGINT NOT NULL,
    cost NUMERIC(12, 2) NOT NULL CHECK (cost >= 0),
    weight_kg NUMERIC(10, 3) NOT NULL CHECK (weight_kg >= 0),

    CONSTRAINT fk_items_manufacturer
        FOREIGN KEY (manufacturer_id)
        REFERENCES manufacturers(manufacturer_id),

    CONSTRAINT uq_item_manufacturer
        UNIQUE (item_name, manufacturer_id)
);


-- ============================================================
-- Sales transactions
-- ============================================================

CREATE TABLE sales_transactions (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    membership_id VARCHAR(255) NOT NULL,
    transaction_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_items_price NUMERIC(14, 2) NOT NULL
        CHECK (total_items_price >= 0),
    total_items_weight NUMERIC(12, 3) NOT NULL
        CHECK (total_items_weight >= 0),

    CONSTRAINT fk_transaction_member
        FOREIGN KEY (membership_id)
        REFERENCES members(membership_id)
);


-- ============================================================
-- Transaction Items
-- ============================================================

CREATE TABLE transaction_items (
    transaction_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),

    -- Snapshot price/weight at time of purchase
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    unit_weight NUMERIC(10, 3) NOT NULL CHECK (unit_weight >= 0),

    PRIMARY KEY (transaction_id, item_id),

    CONSTRAINT fk_transaction_items_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES sales_transactions(transaction_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_transaction_items_item
        FOREIGN KEY (item_id)
        REFERENCES items(item_id)
);


-- ============================================================
-- Useful indexes
-- ============================================================

CREATE INDEX idx_sales_transactions_membership_id
    ON sales_transactions(membership_id);

CREATE INDEX idx_sales_transactions_time
    ON sales_transactions(transaction_time);

CREATE INDEX idx_transaction_items_item_id
    ON transaction_items(item_id);