from typing import List, Dict
from database.connection import get_connection
from models.product import Product
from services.product_service import get_all_products


def get_inventory_summary() -> List[Dict]:
    """Return list of dicts with product stock info for the inventory page."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.id, p.name, p.category, p.base_unit, p.low_stock_threshold,
               COALESCE(i.quantity_base, 0) AS quantity_base,
               pu.unit_name AS display_unit,
               pu.conversion_to_base AS display_conversion
        FROM products p
        LEFT JOIN inventory i ON i.product_id = p.id
        LEFT JOIN product_units pu ON pu.product_id = p.id AND pu.conversion_to_base = 1
        WHERE p.is_active = 1
        ORDER BY p.name
    """).fetchall()

    result = []
    for row in rows:
        conv = row["display_conversion"] or 1.0
        display_qty = row["quantity_base"] / conv if conv else row["quantity_base"]
        threshold_in_base = row["low_stock_threshold"]
        result.append({
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "quantity_base": row["quantity_base"],
            "display_qty": round(display_qty, 3),
            "display_unit": row["display_unit"] or row["base_unit"],
            "low_stock_threshold": threshold_in_base,
            "is_low": row["quantity_base"] <= threshold_in_base and threshold_in_base > 0,
        })
    return result


def get_total_inventory_value() -> Dict:
    """Calculate total inventory value using the most recent purchase price per product."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.id, p.name, COALESCE(i.quantity_base, 0) AS quantity_base
        FROM products p
        LEFT JOIN inventory i ON i.product_id = p.id
        WHERE p.is_active = 1 AND COALESCE(i.quantity_base, 0) > 0
    """).fetchall()

    total_value = 0.0
    items = []
    for row in rows:
        last_purchase = conn.execute(
            """SELECT pi.price_per_unit, pu.conversion_to_base
               FROM purchase_items pi
               JOIN purchases pr ON pr.id = pi.purchase_id
               JOIN product_units pu ON pu.id = pi.unit_id
               WHERE pi.product_id = ?
               ORDER BY pr.date DESC, pr.created_at DESC
               LIMIT 1""",
            (row["id"],),
        ).fetchone()

        if last_purchase and last_purchase["conversion_to_base"]:
            cost_per_base = last_purchase["price_per_unit"] / last_purchase["conversion_to_base"]
        else:
            cost_per_base = 0.0

        item_value = row["quantity_base"] * cost_per_base
        total_value += item_value
        items.append({
            "name": row["name"],
            "quantity_base": row["quantity_base"],
            "cost_per_base": cost_per_base,
            "value": item_value,
        })

    items.sort(key=lambda x: x["value"], reverse=True)
    return {"total_value": total_value, "items": items}


def adjust_stock(product_id: int, delta_base: float) -> None:
    """Add or subtract from inventory. Used internally by purchase/sale services."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO inventory (product_id, quantity_base, last_updated)
           VALUES (?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(product_id) DO UPDATE SET
               quantity_base = quantity_base + excluded.quantity_base,
               last_updated = CURRENT_TIMESTAMP""",
        (product_id, delta_base),
    )
    # Note: commit is handled by the calling service inside its transaction
