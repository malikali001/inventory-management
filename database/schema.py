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
"""


def init_db() -> None:
    """Create all tables if they don't exist."""
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
