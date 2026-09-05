"""Generate the local Retail Copilot SQLite database (database/retail.db).

Produces three tables:
  Products   - ~30 realistic retail products
  Inventory  - current stock + reorder level per store/product
  Sales      - 30 days of synthetic daily sales

Intentionally engineered edge cases:
  - Some Inventory rows have current_stock = 0 (stockouts)
  - Some Inventory rows sit below their reorder_level
  - One product has a single-day sales spike
  - One product has zero sales across all 30 days
"""

import sqlite3
from pathlib import Path
from random import Random

import pandas as pd

DB_PATH = Path(__file__).resolve().parent / "retail.db"

STORE_IDS = ["S001", "S002", "S003"]
N_DAYS = 30
SPIKE_PRODUCT = "P005"
SPIKE_DAY = 15  # 0-indexed, day 16 of the 30-day window
ZERO_SALES_PRODUCT = "P011"
RNG = Random(42)  # deterministic output


def build_products() -> pd.DataFrame:
    products = [
        ("P001", "Wireless Mouse", "Electronics", 8.50, 19.99),
        ("P002", "Mechanical Keyboard", "Electronics", 45.00, 89.99),
        ("P003", "27-inch Monitor", "Electronics", 150.00, 259.99),
        ("P004", "USB-C Cable (1m)", "Electronics", 2.00, 7.99),
        ("P005", "Bluetooth Speaker", "Electronics", 22.00, 49.99),
        ("P006", "Noise-Cancelling Headphones", "Electronics", 80.00, 169.99),
        ("P007", "4K Webcam", "Electronics", 35.00, 79.99),
        ("P008", "Espresso Machine", "Home & Kitchen", 180.00, 349.99),
        ("P009", "Air Fryer", "Home & Kitchen", 60.00, 119.99),
        ("P010", "Stand Mixer", "Home & Kitchen", 140.00, 279.99),
        ("P011", "Cast Iron Skillet", "Home & Kitchen", 18.00, 44.99),
        ("P012", "Nonstick Frying Pan", "Home & Kitchen", 12.00, 29.99),
        ("P013", "Stainless Steel Water Bottle", "Home & Kitchen", 5.00, 16.99),
        ("P014", "Chef's Knife", "Home & Kitchen", 15.00, 39.99),
        ("P015", "Scented Candle Set", "Home & Kitchen", 7.00, 21.99),
        ("P016", "Running Shoes", "Sports & Outdoors", 38.00, 89.99),
        ("P017", "Yoga Mat", "Sports & Outdoors", 10.00, 24.99),
        ("P018", "Resistance Bands Set", "Sports & Outdoors", 9.00, 19.99),
        ("P019", "Camping Tent", "Sports & Outdoors", 95.00, 189.99),
        ("P020", "Hiking Backpack", "Sports & Outdoors", 40.00, 79.99),
        ("P021", "Dumbbell Set (20lb)", "Sports & Outdoors", 55.00, 109.99),
        ("P022", "Insulated Cooler", "Sports & Outdoors", 30.00, 64.99),
        ("P023", "Cotton T-Shirt", "Clothing", 4.00, 14.99),
        ("P024", "Denim Jeans", "Clothing", 16.00, 44.99),
        ("P025", "Down Jacket", "Clothing", 60.00, 129.99),
        ("P026", "Baseball Cap", "Clothing", 3.50, 12.99),
        ("P027", "Winter Scarf", "Clothing", 5.00, 15.99),
        ("P028", "Wireless Router", "Electronics", 45.00, 99.99),
        ("P029", "External SSD 1TB", "Electronics", 65.00, 119.99),
        ("P030", "Ergonomic Desk Chair", "Office", 130.00, 249.99),
    ]
    df = pd.DataFrame(
        products,
        columns=["product_id", "name", "category", "cost_price", "selling_price"],
    )
    return df.set_index("product_id")


def build_inventory(products: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for store in STORE_IDS:
        for product_id in products.index:
            # Known scope products get deterministic stock problems.
            if product_id == "P008":  # stocked out everywhere
                current_stock = 0
                reorder_level = 8
            elif product_id == "P019":  # below reorder level everywhere
                current_stock = 2
                reorder_level = 5
            elif product_id == "P021":  # halfway out of stock
                current_stock = RNG.choice([0, 3])
                reorder_level = 6
            elif product_id == "P011":  # high stock, never sells: dead stock
                current_stock = 150
                reorder_level = 20
            else:
                current_stock = RNG.randint(15, 120)
                reorder_level = RNG.randint(5, 25)
                if (product_id, store) in {("P003", "S001"), ("P014", "S003")}:
                    current_stock = 1  # bespoke low-stock spots
            rows.append((store, product_id, current_stock, reorder_level))

    df = pd.DataFrame(
        rows, columns=["store_id", "product_id", "current_stock", "reorder_level"]
    )
    return df.set_index(["store_id", "product_id"])


def build_sales(products: pd.DataFrame) -> pd.DataFrame:
    selling_price = products["selling_price"].to_dict()
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=N_DAYS, freq="D")

    rows = []
    tx_id = 1
    for day_idx, day in enumerate(dates):
        date_str = day.strftime("%Y-%m-%d")
        for store in STORE_IDS:
            for product_id in products.index:
                if product_id == ZERO_SALES_PRODUCT:
                    continue  # intentionally never sells

                if product_id == SPIKE_PRODUCT and day_idx == SPIKE_DAY:
                    quantity = RNG.randint(180, 220)  # promotion-day spike
                elif product_id == SPIKE_PRODUCT:
                    quantity = RNG.randint(1, 9)
                else:
                    quantity = RNG.randint(0, 6)

                if quantity == 0:
                    continue

                rows.append(
                    {
                        "transaction_id": f"TX{tx_id:06d}",
                        "store_id": store,
                        "product_id": product_id,
                        "date": date_str,
                        "quantity_sold": quantity,
                        "total_revenue": round(quantity * selling_price[product_id], 2),
                    }
                )
                tx_id += 1

    df = pd.DataFrame(rows, columns=[
        "transaction_id", "store_id", "product_id", "date",
        "quantity_sold", "total_revenue",
    ])
    return df.set_index("transaction_id")


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    products = build_products()
    inventory = build_inventory(products)
    sales = build_sales(products)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        products.to_sql("Products", conn, if_exists="replace")
        inventory.to_sql("Inventory", conn, if_exists="replace")
        sales.to_sql("Sales", conn, if_exists="replace")

    with sqlite3.connect(DB_PATH) as conn:
        print(f"Database written to: {DB_PATH}")
        for table in ("Products", "Inventory", "Sales"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table}: {count} rows")

    print(f"  Spike product {SPIKE_PRODUCT} 30-day revenue: "
          f"${sales[sales['product_id'] == SPIKE_PRODUCT]['total_revenue'].sum():,.2f}")
    print(f"  Zero-sales product {ZERO_SALES_PRODUCT} sales rows: "
          f"{(sales['product_id'] == ZERO_SALES_PRODUCT).sum()}")
    stockouts = int((inventory["current_stock"] == 0).sum())
    below_reorder = int((inventory["current_stock"] < inventory["reorder_level"]).sum())
    print(f"  Stockout rows: {stockouts}  |  Rows below reorder level: {below_reorder}")


if __name__ == "__main__":
    main()