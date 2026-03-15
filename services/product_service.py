from typing import List, Optional
from database.connection import get_connection
from models.product import Product, ProductUnit


def _row_to_unit(row) -> ProductUnit:
    return ProductUnit(
        id=row["id"],
        product_id=row["product_id"],
        unit_name=row["unit_name"],
        conversion_to_base=row["conversion_to_base"],
        is_default_purchase=bool(row["is_default_purchase"]),
        is_default_sale=bool(row["is_default_sale"]),
    )


def _row_to_product(row, units: List[ProductUnit], stock: float = 0.0) -> Product:
    return Product(
        id=row["id"],
        name=row["name"],
        category=row["category"] or "",
        base_unit=row["base_unit"],
        low_stock_threshold=row["low_stock_threshold"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        units=units,
        current_stock_base=stock,
    )


def get_all_products(active_only: bool = True) -> List[Product]:
    conn = get_connection()
    query = "SELECT * FROM products"
    if active_only:
        query += " WHERE is_active=1"
    query += " ORDER BY name"
    rows = conn.execute(query).fetchall()
    products = []
    for row in rows:
        units = get_units_for_product(row["id"])
        stock_row = conn.execute(
            "SELECT quantity_base FROM inventory WHERE product_id=?", (row["id"],)
        ).fetchone()
        stock = stock_row["quantity_base"] if stock_row else 0.0
        products.append(_row_to_product(row, units, stock))
    return products


def get_product_by_id(product_id: int) -> Optional[Product]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if not row:
        return None
    units = get_units_for_product(product_id)
    stock_row = conn.execute(
        "SELECT quantity_base FROM inventory WHERE product_id=?", (product_id,)
    ).fetchone()
    stock = stock_row["quantity_base"] if stock_row else 0.0
    return _row_to_product(row, units, stock)


def get_units_for_product(product_id: int) -> List[ProductUnit]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM product_units WHERE product_id=? ORDER BY id", (product_id,)
    ).fetchall()
    return [_row_to_unit(r) for r in rows]


# Suggested units shown in dropdowns based on the base unit.
# Format: { base_unit: [(unit_name, conversion_to_base), ...] }
SUGGESTED_UNITS = {
    "piece": [
        ("dozen", 12),
        ("half dozen", 6),
        ("pair", 2),
        ("box", 24),
        ("pack", 10),
        ("carton", 48),
    ],
    "unit": [
        ("dozen", 12),
        ("half dozen", 6),
        ("pair", 2),
        ("box", 24),
        ("pack", 10),
    ],
    "kg": [
        ("gram", 0.001),
        ("lb", 0.4536),
        ("oz", 0.02835),
        ("quintal", 100),
        ("ton", 1000),
    ],
    "gram": [
        ("kg", 1000),
        ("oz", 28.35),
        ("lb", 453.6),
    ],
    "litre": [
        ("ml", 0.001),
        ("gallon", 3.785),
        ("half litre", 0.5),
        ("quarter litre", 0.25),
    ],
    "ml": [
        ("litre", 1000),
        ("gallon", 3785),
        ("half litre", 500),
    ],
    "meter": [
        ("cm", 0.01),
        ("foot", 0.3048),
        ("inch", 0.0254),
        ("yard", 0.9144),
    ],
    "foot": [
        ("inch", 1 / 12),
        ("yard", 3),
        ("meter", 3.281),
    ],
}


def create_product(
    name: str,
    category: str,
    base_unit: str,
    low_stock_threshold: float,
) -> int:
    """Create a product with its base unit entry and inventory row."""
    if not name.strip():
        raise ValueError("Product name cannot be empty.")
    if not base_unit.strip():
        raise ValueError("Base unit cannot be empty.")
    if low_stock_threshold < 0:
        raise ValueError("Low stock threshold cannot be negative.")
    conn = get_connection()
    base = base_unit.strip()
    cur = conn.execute(
        "INSERT INTO products (name, category, base_unit, low_stock_threshold) VALUES (?,?,?,?)",
        (name.strip(), category.strip(), base, low_stock_threshold),
    )
    product_id = cur.lastrowid
    # Base unit entry (1:1 conversion)
    conn.execute(
        """INSERT INTO product_units (product_id, unit_name, conversion_to_base,
           is_default_purchase, is_default_sale)
           VALUES (?,?,1,1,1)""",
        (product_id, base),
    )
    # Ensure an inventory row exists
    conn.execute(
        "INSERT OR IGNORE INTO inventory (product_id, quantity_base) VALUES (?,0)",
        (product_id,),
    )
    conn.commit()
    return product_id


def update_product(
    product_id: int,
    name: str,
    category: str,
    base_unit: str,
    low_stock_threshold: float,
) -> None:
    if not name.strip():
        raise ValueError("Product name cannot be empty.")
    if not base_unit.strip():
        raise ValueError("Base unit cannot be empty.")
    if low_stock_threshold < 0:
        raise ValueError("Low stock threshold cannot be negative.")
    conn = get_connection()
    conn.execute(
        """UPDATE products SET name=?, category=?, base_unit=?,
           low_stock_threshold=? WHERE id=?""",
        (name.strip(), category.strip(), base_unit.strip(), low_stock_threshold, product_id),
    )
    conn.commit()


def deactivate_product(product_id: int) -> None:
    conn = get_connection()
    conn.execute("UPDATE products SET is_active=0 WHERE id=?", (product_id,))
    conn.commit()


def reactivate_product(product_id: int) -> None:
    conn = get_connection()
    conn.execute("UPDATE products SET is_active=1 WHERE id=?", (product_id,))
    conn.commit()


def delete_product(product_id: int) -> None:
    """Permanently delete a product and all related records."""
    conn = get_connection()
    conn.execute("DELETE FROM sale_items WHERE product_id=?", (product_id,))
    conn.execute("DELETE FROM purchase_items WHERE product_id=?", (product_id,))
    conn.execute("DELETE FROM product_units WHERE product_id=?", (product_id,))
    conn.execute("DELETE FROM inventory WHERE product_id=?", (product_id,))
    conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()


def add_unit(
    product_id: int,
    unit_name: str,
    conversion_to_base: float,
    is_default_purchase: bool = False,
    is_default_sale: bool = False,
) -> int:
    if not unit_name.strip():
        raise ValueError("Unit name cannot be empty.")
    if conversion_to_base <= 0:
        raise ValueError("Conversion factor must be greater than zero.")
    conn = get_connection()
    if is_default_purchase:
        conn.execute(
            "UPDATE product_units SET is_default_purchase=0 WHERE product_id=?",
            (product_id,),
        )
    if is_default_sale:
        conn.execute(
            "UPDATE product_units SET is_default_sale=0 WHERE product_id=?",
            (product_id,),
        )
    cur = conn.execute(
        """INSERT INTO product_units (product_id, unit_name, conversion_to_base,
           is_default_purchase, is_default_sale)
           VALUES (?,?,?,?,?)""",
        (product_id, unit_name.strip(), conversion_to_base,
         int(is_default_purchase), int(is_default_sale)),
    )
    conn.commit()
    return cur.lastrowid


def update_unit(
    unit_id: int,
    unit_name: str,
    conversion_to_base: float,
    is_default_purchase: bool,
    is_default_sale: bool,
) -> None:
    conn = get_connection()
    # Get product_id first
    row = conn.execute(
        "SELECT product_id FROM product_units WHERE id=?", (unit_id,)
    ).fetchone()
    if not row:
        return
    product_id = row["product_id"]
    if is_default_purchase:
        conn.execute(
            "UPDATE product_units SET is_default_purchase=0 WHERE product_id=?",
            (product_id,),
        )
    if is_default_sale:
        conn.execute(
            "UPDATE product_units SET is_default_sale=0 WHERE product_id=?",
            (product_id,),
        )
    conn.execute(
        """UPDATE product_units SET unit_name=?, conversion_to_base=?,
           is_default_purchase=?, is_default_sale=? WHERE id=?""",
        (unit_name.strip(), conversion_to_base,
         int(is_default_purchase), int(is_default_sale), unit_id),
    )
    conn.commit()


def delete_unit(unit_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM product_units WHERE id=?", (unit_id,))
    conn.commit()
