from typing import List, Dict
from database.connection import get_connection
from models.purchase import Purchase, PurchaseItem
from services.inventory_service import adjust_stock


def record_purchase(date: str, notes: str, items: List[Dict]) -> int:
    """
    Record a purchase and update inventory.

    items: list of dicts with keys:
        product_id, product_name, unit_id, unit_name,
        quantity, price_per_unit, conversion_to_base
    Returns the new purchase id.
    """
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO purchases (date, notes) VALUES (?,?)",
            (date, notes.strip()),
        )
        purchase_id = cur.lastrowid

        for item in items:
            qty_base = item["quantity"] * item["conversion_to_base"]
            conn.execute(
                """INSERT INTO purchase_items
                   (purchase_id, product_id, unit_id, quantity, price_per_unit, quantity_base)
                   VALUES (?,?,?,?,?,?)""",
                (purchase_id, item["product_id"], item["unit_id"],
                 item["quantity"], item["price_per_unit"], qty_base),
            )
            adjust_stock(item["product_id"], qty_base)

        conn.commit()
        return purchase_id
    except Exception:
        conn.rollback()
        raise


def get_purchase_history(limit: int = 100, offset: int = 0) -> List[Purchase]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM purchases ORDER BY date DESC, created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    purchases = []
    for row in rows:
        items = _get_purchase_items(row["id"])
        purchases.append(Purchase(
            id=row["id"],
            date=row["date"],
            notes=row["notes"] or "",
            created_at=row["created_at"],
            items=items,
        ))
    return purchases


def get_purchase_by_id(purchase_id: int) -> Purchase | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM purchases WHERE id=?", (purchase_id,)
    ).fetchone()
    if not row:
        return None
    return Purchase(
        id=row["id"],
        date=row["date"],
        notes=row["notes"] or "",
        created_at=row["created_at"],
        items=_get_purchase_items(purchase_id),
    )


def delete_purchase(purchase_id: int) -> None:
    """Delete a purchase and reverse inventory changes."""
    conn = get_connection()
    try:
        items = _get_purchase_items(purchase_id)
        for item in items:
            adjust_stock(item.product_id, -item.quantity_base)
        conn.execute("DELETE FROM purchases WHERE id=?", (purchase_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _get_purchase_items(purchase_id: int) -> List[PurchaseItem]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT pi.*, p.name as product_name, pu.unit_name
           FROM purchase_items pi
           JOIN products p ON p.id = pi.product_id
           JOIN product_units pu ON pu.id = pi.unit_id
           WHERE pi.purchase_id=?""",
        (purchase_id,),
    ).fetchall()
    return [
        PurchaseItem(
            id=row["id"],
            purchase_id=row["purchase_id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            unit_id=row["unit_id"],
            unit_name=row["unit_name"],
            quantity=row["quantity"],
            price_per_unit=row["price_per_unit"],
            quantity_base=row["quantity_base"],
        )
        for row in rows
    ]
