from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
from collections import Counter
import random

import pandas as pd
import psycopg


# ============================================================
# Configuration
# ============================================================

REPO_ROOT = Path(__file__).resolve().parent.parent

SUCCESS_DIR = (
    REPO_ROOT
    / "Section_1_datapipelines"
    / "data"
    / "successful"
)

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "ecommerce",
    "user": "postgres",
    "password": "postgres",  # local Docker only. DO NOT USE IN PRODUCTION
}

# Makes fake data repeatable
random.seed(42)


# ============================================================
# Fake catalogue
# ============================================================

MANUFACTURERS = [
    "Apple",
    "Samsung",
    "Sony",
    "Logitech",
    "Nike",
    "Philips",
]


ITEMS = [
    {
        "name": "Wireless Mouse",
        "manufacturer": "Logitech",
        "cost": Decimal("29.90"),
        "weight": Decimal("0.100"),
        "popularity": 10,
    },
    {
        "name": "Mechanical Keyboard",
        "manufacturer": "Logitech",
        "cost": Decimal("89.90"),
        "weight": Decimal("0.850"),
        "popularity": 9,
    },
    {
        "name": "Wireless Headphones",
        "manufacturer": "Sony",
        "cost": Decimal("129.90"),
        "weight": Decimal("0.250"),
        "popularity": 8,
    },
    {
        "name": "Smartphone",
        "manufacturer": "Samsung",
        "cost": Decimal("899.00"),
        "weight": Decimal("0.180"),
        "popularity": 5,
    },
    {
        "name": "Laptop",
        "manufacturer": "Apple",
        "cost": Decimal("1599.00"),
        "weight": Decimal("1.400"),
        "popularity": 4,
    },
    {
        "name": "Smart Watch",
        "manufacturer": "Apple",
        "cost": Decimal("499.00"),
        "weight": Decimal("0.050"),
        "popularity": 4,
    },
    {
        "name": "Running Shoes",
        "manufacturer": "Nike",
        "cost": Decimal("139.00"),
        "weight": Decimal("0.700"),
        "popularity": 3,
    },
    {
        "name": "Coffee Maker",
        "manufacturer": "Philips",
        "cost": Decimal("79.90"),
        "weight": Decimal("2.100"),
        "popularity": 2,
    },
]


# ============================================================
# Load successful Section 1 members
# ============================================================

def load_member_csvs():
    csv_files = sorted(SUCCESS_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No successful CSV files found in {SUCCESS_DIR}"
        )

    dfs = []

    for csv_file in csv_files:
        print(f"Reading {csv_file.name}")

        df = pd.read_csv(
            csv_file,
            dtype={
                "membership_id": "string",
                "mobile_no": "string",
            },
        )

        dfs.append(df)

    members_df = pd.concat(
        dfs,
        ignore_index=True,
    )

    # Avoid duplicate primary keys / emails
    members_df = (
        members_df
        .drop_duplicates(subset=["membership_id"])
        .drop_duplicates(subset=["email"])
    )

    members_df["date_of_birth"] = pd.to_datetime(
        members_df["date_of_birth"].astype(str),
        format="%Y%m%d",
        errors="coerce",
    ).dt.date

    return members_df


# ============================================================
# Seed database
# ============================================================

def seed_database():

    members_df = load_member_csvs()

    with psycopg.connect(**DB_CONFIG) as conn:

        with conn.cursor() as cur:

            # ------------------------------------------------
            # Reset existing test data
            # ------------------------------------------------

            cur.execute("""
                TRUNCATE TABLE
                    transaction_items,
                    sales_transactions,
                    items,
                    manufacturers,
                    members
                RESTART IDENTITY CASCADE;
            """)

            # ------------------------------------------------
            # Insert members
            # ------------------------------------------------

            member_rows = [
                (
                    row.membership_id,
                    row.first_name,
                    row.last_name,
                    row.email,
                    row.date_of_birth,
                    row.mobile_no,
                )
                for row in members_df.itertuples()
            ]

            cur.executemany(
                """
                INSERT INTO members (
                    membership_id,
                    first_name,
                    last_name,
                    email,
                    date_of_birth,
                    mobile_no
                )
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                member_rows,
            )

            print(f"Inserted {len(member_rows)} members.")

            # ------------------------------------------------
            # Insert manufacturers
            # ------------------------------------------------

            manufacturer_ids = {}

            for manufacturer in MANUFACTURERS:

                cur.execute(
                    """
                    INSERT INTO manufacturers (
                        manufacturer_name
                    )
                    VALUES (%s)
                    RETURNING manufacturer_id;
                    """,
                    (manufacturer,),
                )

                manufacturer_id = cur.fetchone()[0]

                manufacturer_ids[manufacturer] = manufacturer_id

            print(
                f"Inserted {len(manufacturer_ids)} manufacturers."
            )

            # ------------------------------------------------
            # Insert items
            # ------------------------------------------------

            item_records = []

            for item in ITEMS:

                cur.execute(
                    """
                    INSERT INTO items (
                        item_name,
                        manufacturer_id,
                        cost,
                        weight_kg
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING item_id;
                    """,
                    (
                        item["name"],
                        manufacturer_ids[item["manufacturer"]],
                        item["cost"],
                        item["weight"],
                    ),
                )

                item_id = cur.fetchone()[0]

                item_records.append({
                    **item,
                    "item_id": item_id,
                })

            print(f"Inserted {len(item_records)} items.")

            # ------------------------------------------------
            # Generate fake sales transactions
            # ------------------------------------------------

            membership_ids = (
                members_df["membership_id"]
                .tolist()
            )

            item_weights = [
                item["popularity"]
                for item in item_records
            ]

            number_of_transactions = 300

            for _ in range(number_of_transactions):

                membership_id = random.choice(
                    membership_ids
                )

                # Each transaction selects 1 to 5 items
                selection_count = random.randint(
                    1,
                    5,
                )

                selected_items = random.choices(
                    item_records,
                    weights=item_weights,
                    k=selection_count,
                )

                # If the same item is selected multiple
                # times, treat it as quantity > 1
                item_counts = Counter(
                    item["item_id"]
                    for item in selected_items
                )

                total_price = Decimal("0")
                total_weight = Decimal("0")

                transaction_lines = []

                for item_id, quantity in item_counts.items():

                    item = next(
                        item
                        for item in item_records
                        if item["item_id"] == item_id
                    )

                    total_price += (
                        item["cost"] * quantity
                    )

                    total_weight += (
                        item["weight"] * quantity
                    )

                    transaction_lines.append(
                        (
                            item_id,
                            quantity,
                            item["cost"],
                            item["weight"],
                        )
                    )

                transaction_time = (
                    datetime(2026, 1, 1)
                    + timedelta(
                        days=random.randint(0, 220),
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59),
                    )
                )

                # --------------------------------------------
                # Insert transaction header
                # --------------------------------------------

                cur.execute(
                    """
                    INSERT INTO sales_transactions (
                        membership_id,
                        transaction_time,
                        total_items_price,
                        total_items_weight
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING transaction_id;
                    """,
                    (
                        membership_id,
                        transaction_time,
                        total_price,
                        total_weight,
                    ),
                )

                transaction_id = cur.fetchone()[0]

                # --------------------------------------------
                # Insert transaction line items
                # --------------------------------------------

                for (
                    item_id,
                    quantity,
                    unit_price,
                    unit_weight,
                ) in transaction_lines:

                    cur.execute(
                        """
                        INSERT INTO transaction_items (
                            transaction_id,
                            item_id,
                            quantity,
                            unit_price,
                            unit_weight
                        )
                        VALUES (%s, %s, %s, %s, %s);
                        """,
                        (
                            transaction_id,
                            item_id,
                            quantity,
                            unit_price,
                            unit_weight,
                        ),
                    )

            print(
                f"Inserted {number_of_transactions} "
                f"fake sales transactions."
            )

    print("Database seeding complete.")


if __name__ == "__main__":
    seed_database()