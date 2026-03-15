from typing import List, Dict
from database.connection import get_connection


def get_daily_summary(date_from: str, date_to: str) -> Dict:
    """Return revenue, cost (based on last purchase price), and profit for a date range."""
    conn = get_connection()

    revenue_row = conn.execute(
        """SELECT COALESCE(SUM(si.quantity * si.price_per_unit), 0) AS total
           FROM sale_items si
           JOIN sales s ON s.id = si.sale_id
           WHERE s.date BETWEEN ? AND ?""",
        (date_from, date_to),
    ).fetchone()

    cost_row = conn.execute(
        """SELECT COALESCE(SUM(pi.quantity * pi.price_per_unit), 0) AS total
           FROM purchase_items pi
           JOIN purchases p ON p.id = pi.purchase_id
           WHERE p.date BETWEEN ? AND ?""",
        (date_from, date_to),
    ).fetchone()

    sales_count = conn.execute(
        "SELECT COUNT(*) AS cnt FROM sales WHERE date BETWEEN ? AND ?",
        (date_from, date_to),
    ).fetchone()["cnt"]

    revenue = revenue_row["total"]
    cost = cost_row["total"]
    return {
        "date_from": date_from,
        "date_to": date_to,
        "revenue": revenue,
        "cost": cost,
        "profit": revenue - cost,
        "sales_count": sales_count,
    }


def get_profit_per_product(date_from: str, date_to: str) -> List[Dict]:
    """Return revenue, cost, and profit broken down by product for a date range."""
    conn = get_connection()

    # Revenue per product in range
    revenue_rows = conn.execute(
        """SELECT si.product_id, p.name,
                  SUM(si.quantity * si.price_per_unit) AS revenue,
                  SUM(si.quantity_base) AS qty_base_sold
           FROM sale_items si
           JOIN sales s ON s.id = si.sale_id
           JOIN products p ON p.id = si.product_id
           WHERE s.date BETWEEN ? AND ?
           GROUP BY si.product_id""",
        (date_from, date_to),
    ).fetchall()

    result = []
    for row in revenue_rows:
        # Use the most recent purchase price for this product as cost basis
        last_purchase = conn.execute(
            """SELECT pi.price_per_unit, pu.conversion_to_base
               FROM purchase_items pi
               JOIN purchases p ON p.id = pi.purchase_id
               JOIN product_units pu ON pu.id = pi.unit_id
               WHERE pi.product_id = ?
               ORDER BY p.date DESC, p.created_at DESC
               LIMIT 1""",
            (row["product_id"],),
        ).fetchone()

        if last_purchase:
            cost_per_base = last_purchase["price_per_unit"] / last_purchase["conversion_to_base"]
            estimated_cost = cost_per_base * row["qty_base_sold"]
        else:
            estimated_cost = 0.0

        revenue = row["revenue"] or 0.0
        result.append({
            "product_id": row["product_id"],
            "product_name": row["name"],
            "revenue": revenue,
            "estimated_cost": estimated_cost,
            "profit": revenue - estimated_cost,
        })

    result.sort(key=lambda x: x["profit"], reverse=True)
    return result


def get_low_stock_items() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.id, p.name, p.category, p.low_stock_threshold,
                  COALESCE(i.quantity_base, 0) AS quantity_base,
                  pu.unit_name AS display_unit,
                  pu.conversion_to_base AS display_conversion
           FROM products p
           LEFT JOIN inventory i ON i.product_id = p.id
           LEFT JOIN product_units pu ON pu.product_id = p.id AND pu.conversion_to_base = 1
           WHERE p.is_active = 1
             AND p.low_stock_threshold > 0
             AND COALESCE(i.quantity_base, 0) <= p.low_stock_threshold
           ORDER BY (COALESCE(i.quantity_base, 0) - p.low_stock_threshold) ASC""",
    ).fetchall()

    result = []
    for row in rows:
        conv = row["display_conversion"] or 1.0
        result.append({
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "quantity_base": row["quantity_base"],
            "display_qty": round(row["quantity_base"] / conv, 3),
            "display_unit": row["display_unit"] or "unit",
            "low_stock_threshold": row["low_stock_threshold"],
        })
    return result


def get_purchase_history_summary(limit: int = 50) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.id, p.date, p.notes,
                  COUNT(pi.id) AS item_count,
                  COALESCE(SUM(pi.quantity * pi.price_per_unit), 0) AS total
           FROM purchases p
           LEFT JOIN purchase_items pi ON pi.purchase_id = p.id
           GROUP BY p.id
           ORDER BY p.date DESC, p.created_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()

    result = []
    for row in rows:
        # Fetch item details for this purchase
        items = conn.execute(
            """SELECT pr.name, pi.quantity, pu.unit_name
               FROM purchase_items pi
               JOIN products pr ON pr.id = pi.product_id
               JOIN product_units pu ON pu.id = pi.unit_id
               WHERE pi.purchase_id = ?""",
            (row["id"],),
        ).fetchall()
        items_text = ", ".join(
            f"{it['name']} ({it['quantity']:g} {it['unit_name']})" for it in items
        )
        result.append({
            "id": row["id"],
            "date": row["date"],
            "notes": row["notes"] or "",
            "item_count": row["item_count"],
            "items_text": items_text,
            "total": row["total"],
        })
    return result


def get_sales_by_date(date_from: str, date_to: str) -> List[Dict]:
    """Day-by-day revenue breakdown."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.date,
                  COALESCE(SUM(si.quantity * si.price_per_unit), 0) AS revenue,
                  COUNT(DISTINCT s.id) AS batches
           FROM sales s
           LEFT JOIN sale_items si ON si.sale_id = s.id
           WHERE s.date BETWEEN ? AND ?
           GROUP BY s.date
           ORDER BY s.date DESC""",
        (date_from, date_to),
    ).fetchall()
    return [
        {"date": r["date"], "revenue": r["revenue"], "batches": r["batches"]}
        for r in rows
    ]
