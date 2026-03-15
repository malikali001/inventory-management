from typing import List, Dict
from database.connection import get_connection


def get_all_units() -> List[Dict]:
    """Return all saved units sorted by name."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT name, default_count FROM saved_units ORDER BY name"
    ).fetchall()
    return [{"name": r["name"], "default_count": r["default_count"]} for r in rows]


def add_custom_unit(name: str, default_count: float = 1) -> None:
    """Add a new unit (ignores if name already exists)."""
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO saved_units (name, default_count) VALUES (?, ?)",
        (name.strip(), default_count),
    )
    conn.commit()


def update_unit_count(name: str, default_count: float) -> None:
    """Update the default count of an existing unit."""
    conn = get_connection()
    conn.execute(
        "UPDATE saved_units SET default_count=? WHERE name=?",
        (default_count, name.strip()),
    )
    conn.commit()


def get_all_categories() -> List[str]:
    """Return all saved categories sorted by name."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT name FROM saved_categories ORDER BY name"
    ).fetchall()
    return [r["name"] for r in rows]


def add_custom_category(name: str) -> None:
    """Add a new category (ignores if name already exists)."""
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO saved_categories (name) VALUES (?)",
        (name.strip(),),
    )
    conn.commit()
