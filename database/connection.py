import sqlite3
import os
from pathlib import Path


def get_db_path() -> str:
    """Return path to SQLite database file, stored in user's app data folder."""
    app_data = os.environ.get("APPDATA") or str(Path.home())
    db_dir = Path(app_data) / "InventoryManager"
    db_dir.mkdir(parents=True, exist_ok=True)
    return str(db_dir / "inventory.db")


_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    """Return singleton SQLite connection with WAL mode and foreign keys enabled."""
    global _connection
    if _connection is None:
        db_path = get_db_path()
        _connection = sqlite3.connect(db_path, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


def close_connection() -> None:
    global _connection
    if _connection:
        _connection.close()
        _connection = None
