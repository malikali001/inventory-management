import os
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from database.connection import get_db_path
from database.schema import init_db
from ui.main_window import MainWindow
from services.backup_service import auto_backup


def _safe_backup():
    """Run auto-backup silently — errors must never block shutdown."""
    try:
        auto_backup()
    except Exception:
        pass


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
        pass

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

    try:
        if source == "drive":
            from services.google_drive_service import download_backup
            tmp = tempfile.mktemp(suffix=".zip", prefix="drive_restore_")
            download_backup(info["id"], tmp)
            restore_backup(tmp)
            os.remove(tmp)
        else:
            restore_backup(info["path"])
    except Exception:
        QMessageBox.warning(
            None,
            "Restore Failed",
            "Could not restore the backup. Starting with a fresh database.",
        )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Inventory Manager")
    app.setStyle("Fusion")

    # Detect fresh install before init_db creates the DB
    is_fresh = not os.path.exists(get_db_path())

    # Initialize database (creates tables if they don't exist)
    init_db()

    # On fresh install, offer to restore from existing backup
    if is_fresh:
        _offer_backup_restore()

    # Auto-backup on app close so the latest data is always captured
    app.aboutToQuit.connect(_safe_backup)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
