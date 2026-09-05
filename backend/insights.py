"""Deterministic analytics for the Morning Briefing (no LLM)."""

try:
    from .database_ops import execute_query
except ImportError:
    from database_ops import execute_query

RECENT_DAYS = 14
DAYS_OF_STOCK_THRESHOLD = 7
HIGH_STOCK_THRESHOLD = 30
SPIKE_MULTIPLIER = 4.0
SPIKE_MIN_EXTRA_UNITS = 8
DROP_FRACTION = 0.2
DROP_MIN_AVERAGE = 5.0


def _recent_14_day_cutoff() -> str:
    row = execute_query("SELECT MAX(date) AS max_date FROM Sales;")[0]
    if row["max_date"] is None:
        raise ValueError("Sales table is empty; cannot compute insights.")
    return row["max_date"]


def get_stockout_risks() -> list[dict]:
    """Items with zero stock or dangerously low stock given recent sell-through."""
    cutoff = _recent_14_day_cutoff()
    rows = execute_query(
        f"""
        SELECT
            inv.store_id,
            inv.product_id,
            p.name,
            p.category,
            inv.current_stock,
            inv.reorder_level,
            COALESCE(SUM(s.quantity_sold), 0) AS units_sold_recent
        FROM Inventory AS inv
        JOIN Products AS p ON p.product_id = inv.product_id
        LEFT JOIN Sales AS s
            ON s.store_id = inv.store_id
            AND s.product_id = inv.product_id
            AND s.date >= date('{cutoff}', '-{RECENT_DAYS - 1} days')
        GROUP BY
            inv.store_id, inv.product_id, p.name, p.category,
            inv.current_stock, inv.reorder_level
        """
    )

    severity_map = {"out_of_stock": 3, "below_reorder": 2, "velocity_risk": 1}
    risks = []
    for row in rows:
        avg_daily = row["units_sold_recent"] / RECENT_DAYS
        days_of_stock = (
            round(row["current_stock"] / avg_daily, 1) if avg_daily > 0 else None
        )

        if row["current_stock"] == 0:
            status = "out_of_stock"
        elif row["current_stock"] <= row["reorder_level"]:
            status = "below_reorder"
        elif (days_of_stock is not None
              and days_of_stock < DAYS_OF_STOCK_THRESHOLD):
            status = "velocity_risk"
        else:
            continue

        risks.append({
            "store_id": row["store_id"],
            "product_id": row["product_id"],
            "name": row["name"],
            "category": row["category"],
            "current_stock": row["current_stock"],
            "reorder_level": row["reorder_level"],
            "units_sold_recent": row["units_sold_recent"],
            "avg_daily_velocity": round(avg_daily, 2),
            "estimated_days_of_stock": days_of_stock,
            "status": status,
            "severity": severity_map[status],
        })

    risks.sort(key=lambda r: (-r["severity"], r["current_stock"]))
    return risks


def get_dead_stock() -> list[dict]:
    """Items holding high inventory with zero sales in the last 14 days."""
    cutoff = _recent_14_day_cutoff()
    rows = execute_query(
        f"""
        SELECT
            inv.store_id,
            inv.product_id,
            p.name,
            p.category,
            inv.current_stock,
            inv.reorder_level,
            p.cost_price,
            ROUND(inv.current_stock * p.cost_price, 2) AS dead_stock_value,
            COALESCE(SUM(s.quantity_sold), 0) AS units_sold_recent
        FROM Inventory AS inv
        JOIN Products AS p ON p.product_id = inv.product_id
        LEFT JOIN Sales AS s
            ON s.store_id = inv.store_id
            AND s.product_id = inv.product_id
            AND s.date >= date('{cutoff}', '-{RECENT_DAYS - 1} days')
        GROUP BY
            inv.store_id, inv.product_id, p.name, p.category,
            inv.current_stock, inv.reorder_level, p.cost_price
        HAVING inv.current_stock >= {HIGH_STOCK_THRESHOLD}
            AND COALESCE(SUM(s.quantity_sold), 0) = 0
        ORDER BY dead_stock_value DESC
        """
    )

    return [
        {
            "store_id": row["store_id"],
            "product_id": row["product_id"],
            "name": row["name"],
            "category": row["category"],
            "current_stock": row["current_stock"],
            "reorder_level": row["reorder_level"],
            "dead_stock_value": row["dead_stock_value"],
        }
        for row in rows
    ]


def get_sales_anomalies() -> list[dict]:
    """Products whose daily sales spike or drop massively vs their own average."""
    daily = execute_query(
        """
        SELECT date, product_id, SUM(quantity_sold) AS units
        FROM Sales
        GROUP BY product_id, date
        ORDER BY product_id, date
        """
    )
    if not daily:
        return []

    names = {
        row["product_id"]: row["name"]
        for row in execute_query("SELECT product_id, name FROM Products;")
    }

    by_product: dict[str, list[dict]] = {}
    for row in daily:
        by_product.setdefault(row["product_id"], []).append(row)

    anomalies = []
    for product_id, days in by_product.items():
        average = sum(day["units"] for day in days) / len(days)
        if average <= 0:
            continue
        for day in days:
            units = day["units"]
            if units - average >= SPIKE_MIN_EXTRA_UNITS \
                    and units >= SPIKE_MULTIPLIER * average:
                kind = "spike"
            elif average >= DROP_MIN_AVERAGE and units <= DROP_FRACTION * average:
                kind = "drop"
            else:
                continue
            anomalies.append({
                "date": day["date"],
                "product_id": product_id,
                "name": names.get(product_id, product_id),
                "usual_daily_units": round(average, 2),
                "actual_units": units,
                "change_pct": round((units - average) / average * 100, 1),
                "type": kind,
            })

    anomalies.sort(key=lambda a: -abs(a["change_pct"]))
    return anomalies