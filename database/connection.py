import sqlite3
import os
import sys
from pathlib import Path


def get_db_path() -> str:
    """Return path to SQLite database file, stored in the platform's app data folder.

    Windows:  %APPDATA%\\InventoryManager\\
    macOS:    ~/Library/Application Support/InventoryManager/
    Linux:    $XDG_DATA_HOME/InventoryManager/  (defaults to ~/.local/share/)
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", str(Path.home()))
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    db_dir = Path(base) / "InventoryManager"
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
