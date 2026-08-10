# Design 1 - PostgreSQL Access Control

## Overview

This design implements role-based access control (RBAC) for the PostgreSQL e-commerce database created in Section 2.

The database is shared by several internal teams with different operational requirements. Access is therefore granted according to the principle of least privilege, ensuring that each team can only access or modify the data required for its responsibilities.

The three teams covered are:

* Logistics
* Analytics
* Sales

---

## Project Structure

```text
Design_1/
├── schema_changes.sql
├── access_control.sql
└── README.md
```

### `schema_changes.sql`

Contains changes required to support the new operational requirements without recreating the existing production tables.

### `access_control.sql`

Creates PostgreSQL roles and grants the permissions required by each team.

---

## Schema Changes

The Section 2 database is treated as an existing database.

Instead of dropping and recreating tables, the required columns are added using `ALTER TABLE`.

The following fields are introduced:

### Members

```text
membership_status
```

Used to represent the current membership status for analytical purposes.

Default value:

```text
active
```

### Sales Transactions

```text
transaction_status
completed_at
```

`transaction_status` allows the logistics team to mark the state of an order.

Default value:

```text
pending
```

`completed_at` records when a transaction is completed.

---

## Access Control Strategy

PostgreSQL roles are used to represent each team:

```text
logistics_role
analytics_role
sales_role
```

The roles are created using `NOLOGIN`.

This allows the roles to act as permission groups that can later be assigned to individual application or employee database accounts.

---

## Access Matrix

| Resource           | Logistics             | Analytics | Sales                           |
| ------------------ | --------------------- | --------- | ------------------------------- |
| Members            | No Access             | Read      | No Access                       |
| Manufacturers      | No Access             | Read      | Read                            |
| Items              | Read                  | Read      | Read / Insert / Update / Delete |
| Sales Transactions | Read + Limited Update | Read      | No Access                       |
| Transaction Items  | Read                  | Read      | No Access                       |

---

## Logistics Access

The logistics team requires access to sales information in order to fulfil orders.

The team can:

* View sales transaction information
* View item information
* View transaction line items
* View total item weight
* Update transaction completion status
* Record the completion timestamp

The team cannot modify financial transaction information such as:

```text
total_items_price
total_items_weight
membership_id
transaction_time
```

Update permissions are restricted specifically to:

```text
transaction_status
completed_at
```

This prevents logistics users from modifying unrelated transaction data.

---

## Analytics Access

The analytics team requires access to sales, membership and product information for analysis.

The team has read-only access to:

```text
members
manufacturers
items
sales_transactions
transaction_items
```

No `INSERT`, `UPDATE` or `DELETE` permissions are granted.

This allows analysts to perform queries and aggregations without being able to modify operational data.

---

## Sales Access

The sales team manages the product catalogue.

The team can:

* View items
* Add new items
* Update existing items
* Remove old items
* View manufacturer information

The sales team does not have access to modify:

```text
members
sales_transactions
transaction_items
```

This prevents catalogue administration from affecting customer or transaction records.

---

## Least Privilege

Permissions are intentionally granted at the smallest practical scope.

For example, logistics does not receive full `UPDATE` permission on the `sales_transactions` table.

Instead:

```sql
GRANT UPDATE (
    transaction_status,
    completed_at
)
ON sales_transactions
TO logistics_role;
```

This allows Logistics to perform its required work while preventing modification of transaction prices or customer references.

---

## Testing

The scripts were tested against the PostgreSQL Docker database created in Section 2.

### Apply Schema Changes

From PowerShell:

```powershell
Get-Content .\schema_changes.sql | docker exec -i ecommerce-db psql -U postgres -d ecommerce
```

The resulting schema can be inspected using:

```sql
\d members
\d sales_transactions
```

---

### Apply Access Control

```powershell
Get-Content .\access_control.sql | docker exec -i ecommerce-db psql -U postgres -d ecommerce
```

Roles can be inspected using:

```sql
\du
```

Permissions can be inspected using:

```sql
\dp
```

---

## Permission Testing

PostgreSQL `SET ROLE` was used to verify the permissions of each team.

Example:

```sql
SET ROLE logistics_role;
```

A permitted logistics query:

```sql
SELECT
    transaction_id,
    total_items_weight,
    transaction_status
FROM sales_transactions
LIMIT 5;
```

A permitted update:

```sql
UPDATE sales_transactions
SET
    transaction_status = 'completed',
    completed_at = CURRENT_TIMESTAMP
WHERE transaction_id = 1;
```

An attempt by Logistics to modify fields outside its responsibilities, such as:

```sql
UPDATE sales_transactions
SET total_items_price = 999999
WHERE transaction_id = 1;
```

is rejected by PostgreSQL due to insufficient permissions.

Similar tests were performed for the Analytics and Sales roles.

---

## Design Considerations

### Existing Production Database

The design assumes that the Section 2 database already exists and may contain production data.

Schema changes are therefore implemented using migrations through `ALTER TABLE` instead of dropping and recreating existing tables.

### Role-Based Access Control

Permissions are assigned to team roles rather than directly to individual users.

In a production environment, individual database accounts can be granted membership in the appropriate role.

For example:

```sql
GRANT logistics_role TO logistics_user;
```

### Separation of Responsibilities

Each team is restricted to the functions required for its role:

```text
Logistics
    → fulfil transactions

Analytics
    → analyse data

Sales
    → manage catalogue
```

This reduces the risk of accidental or unauthorized modification of data.

---

## Security Principles

The design follows the following principles:

* Least privilege
* Role-based access control
* Separation of duties
* Read-only analytical access
* Column-level update restrictions
* Controlled schema evolution
