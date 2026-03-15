import logging
import os
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from database.connection import get_db_path, close_connection
from database.schema import init_db
from ui.main_window import MainWindow
from services.backup_service import auto_backup

logger = logging.getLogger(__name__)


def _setup_logging():
    """Configure logging to file and console."""
    log_dir = Path(get_db_path()).parent
    log_file = log_dir / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def _safe_backup():
    """Run auto-backup silently — errors must never block shutdown."""
    try:
        auto_backup()
    except Exception:
        logger.exception("Auto-backup failed on shutdown")


def _offer_backup_restore():
    """On fresh install, offer to restore from local or Google Drive backup."""
    import tempfile
    from services.backup_service import list_auto_backups, restore_backup

    # Gather local backups
    local_backups = list_auto_backups()
    latest_local = local_backups[0] if local_backups else None

    # Gather Google Drive backups (if connected)
    latest_drive = None
    try:
        from services.google_drive_service import is_connected, list_drive_backups
        if is_connected():
            drive_backups = list_drive_backups()
            if drive_backups:
                latest_drive = drive_backups[0]
    except Exception:
        logger.warning("Could not check Google Drive backups", exc_info=True)

    if not latest_local and not latest_drive:
        return

    # Pick the best source — prefer Drive if local is missing, otherwise show what we have
    if latest_drive and not latest_local:
        source, label = "drive", "Google Drive"
        info = latest_drive
    elif latest_local and not latest_drive:
        source, label = "local", "local storage"
        info = latest_local
    else:
        # Both exist — prefer whichever is newer by date string
        if latest_drive["date"] > latest_local["date"]:
            source, label = "drive", "Google Drive"
            info = latest_drive
        else:
            source, label = "local", "local storage"
            info = latest_local

    reply = QMessageBox.question(
        None,
        "Backup Found",
        f"A previous backup was found on {label}:\n\n"
        f"  {info['name']}\n"
        f"  Date: {info['date']}\n"
        f"  Size: {info['size_mb']:.1f} MB\n\n"
        "Would you like to restore it?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.Yes,
    )
    if reply != QMessageBox.Yes:
        return

    tmp = None
    try:
        if source == "drive":
            from services.google_drive_service import download_backup
            tmp = tempfile.mktemp(suffix=".zip", prefix="drive_restore_")
            download_backup(info["id"], tmp)
            restore_backup(tmp)
        else:
            restore_backup(info["path"])
    except Exception:
        logger.exception("Backup restore failed during initial setup")
        QMessageBox.warning(
            None,
            "Restore Failed",
            "Could not restore the backup. Starting with a fresh database.",
        )
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Inventory Manager")
    app.setStyle("Fusion")

    _setup_logging()
    logger.info("Application starting")

    # Global exception handler — log and show dialog instead of silent crash
    def _handle_exception(exc_type, exc_value, exc_tb):
        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
        QMessageBox.critical(
            None, "Unexpected Error",
            f"An unexpected error occurred:\n{exc_value}\n\n"
            "Details have been written to app.log.",
        )
    sys.excepthook = _handle_exception

    # Detect fresh install before init_db creates the DB
    is_fresh = not os.path.exists(get_db_path())

    # Initialize database (creates tables if they don't exist)
    init_db()

    # On fresh install, offer to restore from existing backup
    if is_fresh:
        _offer_backup_restore()

    # Auto-backup and clean shutdown
    def _safe_shutdown():
        _safe_backup()
        close_connection()

    app.aboutToQuit.connect(_safe_shutdown)

    window = MainWindow(is_fresh=is_fresh)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
