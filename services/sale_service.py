from typing import List, Dict
from database.connection import get_connection
from models.sale import Sale, SaleItem
from services.inventory_service import adjust_stock


def record_sale(date: str, notes: str, items: List[Dict]) -> int:
    """
    Record a daily sales batch and decrease inventory.

    items: list of dicts with keys:
        product_id, product_name, unit_id, unit_name,
        quantity, price_per_unit, conversion_to_base
    Returns the new sale id.
    """
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO sales (date, notes) VALUES (?,?)",
            (date, notes.strip()),
        )
        sale_id = cur.lastrowid

        for item in items:
            qty_base = item["quantity"] * item["conversion_to_base"]
            conn.execute(
                """INSERT INTO sale_items
                   (sale_id, product_id, unit_id, quantity, price_per_unit, quantity_base)
                   VALUES (?,?,?,?,?,?)""",
                (sale_id, item["product_id"], item["unit_id"],
                 item["quantity"], item["price_per_unit"], qty_base),
            )
            adjust_stock(item["product_id"], -qty_base)

        conn.commit()
        return sale_id
    except Exception:
        conn.rollback()
        raise


def get_sale_history(limit: int = 100, offset: int = 0) -> List[Sale]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM sales ORDER BY date DESC, created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    sales = []
    for row in rows:
        items = _get_sale_items(row["id"])
        sales.append(Sale(
            id=row["id"],
            date=row["date"],
            notes=row["notes"] or "",
            created_at=row["created_at"],
            items=items,
        ))
    return sales


def get_sale_by_id(sale_id: int) -> Sale | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
    if not row:
        return None
    return Sale(
        id=row["id"],
        date=row["date"],
        notes=row["notes"] or "",
        created_at=row["created_at"],
        items=_get_sale_items(sale_id),
    )


def delete_sale(sale_id: int) -> None:
    """Delete a sale record and restore inventory."""
    conn = get_connection()
    try:
        items = _get_sale_items(sale_id)
        for item in items:
            adjust_stock(item.product_id, item.quantity_base)
        conn.execute("DELETE FROM sales WHERE id=?", (sale_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _get_sale_items(sale_id: int) -> List[SaleItem]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT si.*, p.name as product_name, pu.unit_name
           FROM sale_items si
           JOIN products p ON p.id = si.product_id
           JOIN product_units pu ON pu.id = si.unit_id
           WHERE si.sale_id=?""",
        (sale_id,),
    ).fetchall()
    return [
        SaleItem(
            id=row["id"],
            sale_id=row["sale_id"],
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
