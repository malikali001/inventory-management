"""
Simple schema migration runner for SQLite.

Each migration is a function that receives a sqlite3.Connection and applies
incremental schema changes.  Migrations are numbered sequentially starting at 1.
The current version is stored in the ``schema_version`` table (single row).

Usage (called automatically by ``init_db``):
    from database.migrations import run_migrations
    run_migrations(conn)
"""

import logging
import sqlite3

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Migration registry — add new migrations here in order
# ---------------------------------------------------------------------------


def _migration_001_baseline(conn: sqlite3.Connection) -> None:
    """Baseline migration — marks the initial schema as version 1.

    No DDL changes needed because fresh installs already have all tables
    via CREATE TABLE IF NOT EXISTS in schema.py.
    """
    pass


def _migration_002_additional_costs(conn: sqlite3.Connection) -> None:
    """Add final_cost_per_unit to purchase_items and purchase_additional_costs table."""
    conn.execute(
        "ALTER TABLE purchase_items ADD COLUMN final_cost_per_unit REAL DEFAULT NULL"
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS purchase_additional_costs (
               id          INTEGER PRIMARY KEY AUTOINCREMENT,
               purchase_id INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
               cost_name   TEXT    NOT NULL,
               amount      REAL    NOT NULL CHECK (amount >= 0)
           )"""
    )


# Register all migrations in order.  The runner applies any whose version
# number exceeds the current ``schema_version``.
MIGRATIONS: dict[int, callable] = {
    1: _migration_001_baseline,
    2: _migration_002_additional_costs,
}

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

LATEST_VERSION = max(MIGRATIONS)


def _ensure_version_table(conn: sqlite3.Connection) -> None:
    """Create the schema_version table if it doesn't exist."""
    conn.execute(
        """CREATE TABLE IF NOT EXISTS schema_version (
               id      INTEGER PRIMARY KEY CHECK (id = 1),
               version INTEGER NOT NULL DEFAULT 0
           )"""
    )
    # Seed with version 0 so the first migration always runs.
    conn.execute("INSERT OR IGNORE INTO schema_version (id, version) VALUES (1, 0)")


def _get_current_version(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()
    return row[0] if row else 0


def _set_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute("UPDATE schema_version SET version = ? WHERE id = 1", (version,))


def run_migrations(conn: sqlite3.Connection) -> None:
    """Apply all pending migrations and commit."""
    _ensure_version_table(conn)
    current = _get_current_version(conn)

    if current >= LATEST_VERSION:
        return  # nothing to do

    for version in sorted(MIGRATIONS):
        if version > current:
            logger.info("Applying migration %d …", version)
            try:
                MIGRATIONS[version](conn)
                _set_version(conn, version)
            except Exception:
                logger.exception("Migration %d failed", version)
                raise

    conn.commit()
    logger.info("Database schema is now at version %d", LATEST_VERSION)
