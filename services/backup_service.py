import logging
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from database.connection import get_db_path, close_connection, get_connection
from database.schema import init_db

logger = logging.getLogger(__name__)


def _backups_dir() -> Path:
    """Return the auto-backups directory, creating it if needed."""
    db_dir = Path(get_db_path()).parent
    backups = db_dir / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    return backups


def create_backup(dest_zip_path: str) -> str:
    """
    Close the DB, copy inventory.db into a .zip at dest_zip_path, reopen the DB.
    Returns the absolute path of the created zip.
    """
    db_path = get_db_path()
    if not os.path.exists(db_path):
        raise FileNotFoundError("Database file not found.")

    # Flush WAL to main DB before copying (best-effort — may fail if DB is busy)
    try:
        get_connection().execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        logger.warning("WAL checkpoint failed (DB may be busy), backing up as-is")
    close_connection()

    try:
        with zipfile.ZipFile(dest_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(db_path, "inventory.db")
        # Verify backup integrity
        with zipfile.ZipFile(dest_zip_path, "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                raise ValueError(f"Backup verification failed: corrupt file {bad}")
    finally:
        get_connection()  # reopen

    return os.path.abspath(dest_zip_path)


def restore_backup(zip_path: str) -> None:
    """
    Close the DB, extract inventory.db from the zip, overwrite the current DB,
    reopen the connection and re-init schema for safety.
    """
    if not os.path.exists(zip_path):
        raise FileNotFoundError("Backup file not found.")

    with zipfile.ZipFile(zip_path, "r") as zf:
        if "inventory.db" not in zf.namelist():
            raise ValueError("Invalid backup: no inventory.db found inside the zip.")

    db_path = get_db_path()
    close_connection()

    try:
        # Safety: keep a copy of the current DB in case restore fails
        temp_copy = db_path + ".pre_restore"
        if os.path.exists(db_path):
            shutil.copy2(db_path, temp_copy)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extract("inventory.db", os.path.dirname(db_path))

        # Remove WAL/SHM leftovers from the old DB
        for suffix in ("-wal", "-shm"):
            leftover = db_path + suffix
            if os.path.exists(leftover):
                os.remove(leftover)

        # Reopen and verify
        conn = get_connection()
        conn.execute("SELECT count(*) FROM products")  # quick integrity check
        init_db()

        # Remove safety copy on success
        if os.path.exists(temp_copy):
            os.remove(temp_copy)

    except Exception:
        # Rollback: restore the old DB
        if os.path.exists(temp_copy):
            close_connection()
            shutil.copy2(temp_copy, db_path)
            os.remove(temp_copy)
            get_connection()
            init_db()
        raise


def auto_backup() -> None:
    """Create a timestamped backup in the backups/ folder. Keep only the last 5."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return  # nothing to back up yet

    backups = _backups_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = str(backups / f"auto_backup_{timestamp}.zip")
    create_backup(dest)

    # Prune old backups — keep newest 5
    existing = sorted(backups.glob("auto_backup_*.zip"), key=os.path.getmtime, reverse=True)
    for old in existing[5:]:
        old.unlink()

    # Upload to Google Drive if connected (failure must never block shutdown)
    try:
        from services.google_drive_service import is_connected, upload_backup
        if is_connected():
            upload_backup(dest)
    except Exception:
        logger.warning("Google Drive upload failed during auto-backup", exc_info=True)


def list_auto_backups() -> list[dict]:
    """Return list of auto-backups with name, size, and date."""
    backups = _backups_dir()
    result = []
    for f in sorted(backups.glob("auto_backup_*.zip"), key=os.path.getmtime, reverse=True):
        stat = f.stat()
        result.append({
            "name": f.name,
            "path": str(f),
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return result


def get_backups_folder() -> str:
    """Return the absolute path of the backups directory."""
    return str(_backups_dir())
