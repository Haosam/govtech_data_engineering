# Section 2 - E-Commerce Database

## Entity Relationship Diagram

The database is designed to support membership information, product catalogue data, and e-commerce sales transactions.

```mermaid
erDiagram
    MEMBERS ||--o{ SALES_TRANSACTIONS : makes
    MANUFACTURERS ||--o{ ITEMS : produces
    SALES_TRANSACTIONS ||--|{ TRANSACTION_ITEMS : contains
    ITEMS ||--o{ TRANSACTION_ITEMS : purchased_as

    MEMBERS {
        varchar membership_id PK
        varchar first_name
        varchar last_name
        varchar email
        date date_of_birth
        varchar mobile_no
    }

    MANUFACTURERS {
        bigint manufacturer_id PK
        varchar manufacturer_name
    }

    ITEMS {
        bigint item_id PK
        varchar item_name
        bigint manufacturer_id FK
        numeric cost
        numeric weight_kg
    }

    SALES_TRANSACTIONS {
        bigint transaction_id PK
        varchar membership_id FK
        timestamptz transaction_time
        numeric total_items_price
        numeric total_items_weight
    }

    TRANSACTION_ITEMS {
        bigint transaction_id PK, FK
        bigint item_id PK, FK
        integer quantity
        numeric unit_price
        numeric unit_weight
    }