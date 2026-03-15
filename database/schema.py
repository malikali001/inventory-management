from database.connection import get_connection

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    category            TEXT    DEFAULT '',
    base_unit           TEXT    NOT NULL DEFAULT 'piece',
    low_stock_threshold REAL    DEFAULT 0,
    is_active           INTEGER DEFAULT 1,
    created_at          TEXT    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_units (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id          INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    unit_name           TEXT    NOT NULL,
    conversion_to_base  REAL    NOT NULL DEFAULT 1,
    is_default_purchase INTEGER DEFAULT 0,
    is_default_sale     INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS inventory (
    product_id    INTEGER PRIMARY KEY REFERENCES products(id),
    quantity_base REAL    NOT NULL DEFAULT 0,
    last_updated  TEXT    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS purchases (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date       TEXT NOT NULL,
    notes      TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS purchase_items (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id    INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    product_id     INTEGER NOT NULL REFERENCES products(id),
    unit_id        INTEGER NOT NULL REFERENCES product_units(id),
    quantity       REAL    NOT NULL,
    price_per_unit REAL    NOT NULL,
    quantity_base  REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS sales (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date       TEXT NOT NULL,
    notes      TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sale_items (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id        INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id     INTEGER NOT NULL REFERENCES products(id),
    unit_id        INTEGER NOT NULL REFERENCES product_units(id),
    quantity       REAL    NOT NULL,
    price_per_unit REAL    NOT NULL,
    quantity_base  REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS saved_units (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    default_count REAL NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS saved_categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
"""

_DEFAULT_UNITS = [
    ("piece", 1), ("unit", 1), ("pair", 2), ("set", 1),
    ("dozen", 12), ("half dozen", 6), ("bundle", 6),
    ("box", 24), ("carton", 48), ("case", 12),
    ("pack", 10), ("packet", 1), ("bag", 1),
    ("pallet", 1), ("crate", 1),
    ("kg", 1), ("gram", 1), ("lb", 1), ("oz", 1),
    ("litre", 1), ("ml", 1), ("gallon", 1),
    ("meter", 1), ("foot", 1), ("inch", 1), ("yard", 1),
    ("roll", 1), ("sheet", 1), ("bottle", 1), ("can", 1),
]

_DEFAULT_CATEGORIES = [
    "Food", "Beverages", "Household", "Electronics",
    "Clothing", "Health & Beauty", "Stationery",
    "Hardware", "Grocery", "Other",
]


def init_db() -> None:
    """Create all tables if they don't exist and seed defaults."""
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    # Seed default units
    for name, count in _DEFAULT_UNITS:
        conn.execute(
            "INSERT OR IGNORE INTO saved_units (name, default_count) VALUES (?, ?)",
            (name, count),
        )
    # Seed default categories
    for name in _DEFAULT_CATEGORIES:
        conn.execute(
            "INSERT OR IGNORE INTO saved_categories (name) VALUES (?)",
            (name,),
        )
    conn.commit()
