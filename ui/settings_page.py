import os
import sys
import subprocess
import tempfile

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ui.styles import COLORS, get_current_theme, set_theme
from services.backup_service import (
    create_backup, restore_backup, list_auto_backups, get_backups_folder,
)
from services import google_drive_service as gdrive


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_window = parent

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        outer = QVBoxLayout(container)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(20)

        # Title
        title = QLabel("Settings")
        title.setObjectName("page_title")
        outer.addWidget(title)

        # ── Theme toggle card ───────────────────────────────────────────
        theme_card = self._make_card()
        tl = QVBoxLayout(theme_card)
        tl.setContentsMargins(20, 18, 20, 18)
        tl.setSpacing(12)

        tl.addWidget(self._section_title("Appearance"))
        tl.addWidget(self._hint_label("Switch between dark and light theme."))

        theme_row = QHBoxLayout()
        self.btn_dark = QPushButton("Dark")
        self.btn_dark.setFixedHeight(38)
        self.btn_dark.setFixedWidth(100)
        self.btn_dark.clicked.connect(lambda: self._on_switch_theme("dark"))

        self.btn_light = QPushButton("Light")
        self.btn_light.setFixedHeight(38)
        self.btn_light.setFixedWidth(100)
        self.btn_light.clicked.connect(lambda: self._on_switch_theme("light"))

        theme_row.addWidget(self.btn_dark)
        theme_row.addWidget(self.btn_light)
        theme_row.addStretch()
        tl.addLayout(theme_row)
        outer.addWidget(theme_card)

        self._update_theme_buttons()

        # ── Backup card ──────────────────────────────────────────────────
        backup_card = self._make_card()
        bl = QVBoxLayout(backup_card)
        bl.setContentsMargins(20, 18, 20, 18)
        bl.setSpacing(12)

        bl.addWidget(self._section_title("Create Backup"))
        bl.addWidget(self._hint_label(
            "Export your entire database to a .zip file. You can save it to USB, "
            "cloud drive, or anywhere safe."
        ))

        btn_row = QHBoxLayout()
        self.btn_backup = QPushButton("Create Backup")
        self.btn_backup.setObjectName("btn_success")
        self.btn_backup.setFixedHeight(40)
        self.btn_backup.setFixedWidth(200)
        self.btn_backup.clicked.connect(self._on_create_backup)
        btn_row.addWidget(self.btn_backup)

        self.backup_status = QLabel("")
        btn_row.addWidget(self.backup_status)
        btn_row.addStretch()
        bl.addLayout(btn_row)
        outer.addWidget(backup_card)

        # ── Restore card ─────────────────────────────────────────────────
        restore_card = self._make_card()
        rl = QVBoxLayout(restore_card)
        rl.setContentsMargins(20, 18, 20, 18)
        rl.setSpacing(12)

        rl.addWidget(self._section_title("Restore from Backup"))

        warning = QLabel(
            "⚠  This will REPLACE all current data with the backup. "
            "The current database will be overwritten."
        )
        warning.setWordWrap(True)
        warning.setObjectName("warning_label")
        rl.addWidget(warning)

        rbtn_row = QHBoxLayout()
        self.btn_restore = QPushButton("Restore from Backup")
        self.btn_restore.setObjectName("btn_danger")
        self.btn_restore.setFixedHeight(40)
        self.btn_restore.setFixedWidth(200)
        self.btn_restore.clicked.connect(self._on_restore_backup)
        rbtn_row.addWidget(self.btn_restore)

        self.restore_status = QLabel("")
        rbtn_row.addWidget(self.restore_status)
        rbtn_row.addStretch()
        rl.addLayout(rbtn_row)
        outer.addWidget(restore_card)

        # ── Auto-backups card ────────────────────────────────────────────
        auto_card = self._make_card()
        al = QVBoxLayout(auto_card)
        al.setContentsMargins(20, 18, 20, 18)
        al.setSpacing(12)

        al.addWidget(self._section_title("Auto-Backups"))
        al.addWidget(self._hint_label(
            "The app automatically creates a backup every time it starts. "
            "The last 5 backups are kept."
        ))

        self.auto_table = QTableWidget()
        self.auto_table.setColumnCount(3)
        self.auto_table.setHorizontalHeaderLabels(["File", "Date", "Size"])
        self.auto_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.auto_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.auto_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.auto_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.auto_table.verticalHeader().setVisible(False)
        self.auto_table.setAlternatingRowColors(True)
        self.auto_table.setMaximumHeight(200)
        al.addWidget(self.auto_table)

        folder_row = QHBoxLayout()
        btn_folder = QPushButton("Open Backups Folder")
        btn_folder.setObjectName("btn_secondary")
        btn_folder.setFixedHeight(36)
        btn_folder.clicked.connect(self._on_open_folder)
        folder_row.addWidget(btn_folder)
        folder_row.addStretch()
        al.addLayout(folder_row)

        outer.addWidget(auto_card)

        # ── Google Drive card ──────────────────────────────────────────
        drive_card = self._make_card()
        dl = QVBoxLayout(drive_card)
        dl.setContentsMargins(20, 18, 20, 18)
        dl.setSpacing(12)

        dl.addWidget(self._section_title("Google Drive Backup"))
        dl.addWidget(self._hint_label(
            "Connect your Google Drive to automatically sync backups to the cloud."
        ))

        # Connected info (hidden by default)
        self.drive_connected_label = QLabel("")
        self.drive_connected_label.setObjectName("hint_label")
        self.drive_connected_label.setVisible(False)
        dl.addWidget(self.drive_connected_label)

        # Buttons row
        drive_btn_row = QHBoxLayout()

        self.btn_drive_connect = QPushButton("Connect Google Drive")
        self.btn_drive_connect.setObjectName("btn_success")
        self.btn_drive_connect.setFixedHeight(40)
        self.btn_drive_connect.setFixedWidth(200)
        self.btn_drive_connect.clicked.connect(self._on_drive_connect)
        drive_btn_row.addWidget(self.btn_drive_connect)

        self.btn_drive_upload = QPushButton("Upload Now")
        self.btn_drive_upload.setObjectName("btn_secondary")
        self.btn_drive_upload.setFixedHeight(40)
        self.btn_drive_upload.setFixedWidth(140)
        self.btn_drive_upload.clicked.connect(self._on_drive_upload)
        self.btn_drive_upload.setVisible(False)
        drive_btn_row.addWidget(self.btn_drive_upload)

        self.btn_drive_restore = QPushButton("Restore from Drive")
        self.btn_drive_restore.setObjectName("btn_secondary")
        self.btn_drive_restore.setFixedHeight(40)
        self.btn_drive_restore.setFixedWidth(160)
        self.btn_drive_restore.clicked.connect(self._on_drive_restore)
        self.btn_drive_restore.setVisible(False)
        drive_btn_row.addWidget(self.btn_drive_restore)

        self.btn_drive_disconnect = QPushButton("Disconnect")
        self.btn_drive_disconnect.setObjectName("btn_danger")
        self.btn_drive_disconnect.setFixedHeight(40)
        self.btn_drive_disconnect.setFixedWidth(140)
        self.btn_drive_disconnect.clicked.connect(self._on_drive_disconnect)
        self.btn_drive_disconnect.setVisible(False)
        drive_btn_row.addWidget(self.btn_drive_disconnect)

        drive_btn_row.addStretch()
        dl.addLayout(drive_btn_row)

        self.drive_status = QLabel("")
        dl.addWidget(self.drive_status)

        # Drive backups table
        self.drive_table = QTableWidget()
        self.drive_table.setColumnCount(3)
        self.drive_table.setHorizontalHeaderLabels(["File", "Date", "Size"])
        self.drive_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.drive_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.drive_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.drive_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.drive_table.verticalHeader().setVisible(False)
        self.drive_table.setAlternatingRowColors(True)
        self.drive_table.setMaximumHeight(200)
        self.drive_table.setVisible(False)
        dl.addWidget(self.drive_table)

        outer.addWidget(drive_card)
        outer.addStretch()

        self.refresh()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _make_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        return card

    def _section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("section_title")
        return lbl

    def _hint_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setObjectName("hint_label")
        return lbl

    def _update_theme_buttons(self):
        current = get_current_theme()
        if current == "dark":
            self.btn_dark.setObjectName("btn_success")
            self.btn_light.setObjectName("btn_secondary")
        else:
            self.btn_light.setObjectName("btn_success")
            self.btn_dark.setObjectName("btn_secondary")
        for btn in (self.btn_dark, self.btn_light):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_switch_theme(self, theme: str):
        if theme == get_current_theme():
            return
        new_qss = set_theme(theme)
        if self._main_window:
            self._main_window.apply_theme(new_qss)
        self._update_theme_buttons()

    # ── Actions ───────────────────────────────────────────────────────────

    def _on_create_backup(self):
        self.backup_status.setText("")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Backup", "inventory_backup.zip", "Zip Files (*.zip)"
        )
        if not path:
            return
        try:
            result = create_backup(path)
            self.backup_status.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 12px;")
            self.backup_status.setText(f"Backup saved to {result}")
        except Exception as e:
            self.backup_status.setStyleSheet(f"color: {COLORS['accent_red']}; font-size: 12px;")
            self.backup_status.setText(f"Backup failed: {e}")

    def _on_restore_backup(self):
        self.restore_status.setText("")
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup", "", "Zip Files (*.zip)"
        )
        if not path:
            return

        reply = QMessageBox.warning(
            self,
            "Confirm Restore",
            "This will REPLACE all current data with the selected backup.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            restore_backup(path)
            self.restore_status.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 12px;")
            self.restore_status.setText("Restore complete! All pages refreshed.")
            # Refresh all pages
            self._refresh_all_pages()
        except Exception as e:
            self.restore_status.setStyleSheet(f"color: {COLORS['accent_red']}; font-size: 12px;")
            self.restore_status.setText(f"Restore failed: {e}")

    def _on_open_folder(self):
        folder = get_backups_folder()
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    # ── Google Drive actions ──────────────────────────────────────────────

    def _on_drive_connect(self):
        self.drive_status.setText("")
        try:
            gdrive.connect()
            self._refresh_drive_ui()
            self.drive_status.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 12px;")
            self.drive_status.setText("Connected successfully!")
        except Exception as e:
            self.drive_status.setStyleSheet(f"color: {COLORS['accent_red']}; font-size: 12px;")
            self.drive_status.setText(f"Connection failed: {e}")

    def _on_drive_disconnect(self):
        reply = QMessageBox.question(
            self, "Disconnect Google Drive",
            "Disconnect your Google Drive?\n\n"
            "Existing backups on Drive will not be deleted.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        gdrive.disconnect()
        self._refresh_drive_ui()
        self.drive_status.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 12px;")
        self.drive_status.setText("Disconnected.")

    def _on_drive_upload(self):
        self.drive_status.setText("Uploading...")
        try:
            # Create a temp backup and upload it
            tmp = tempfile.mktemp(suffix=".zip", prefix="drive_backup_")
            create_backup(tmp)
            gdrive.upload_backup(tmp)
            os.remove(tmp)
            self._refresh_drive_table()
            self.drive_status.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 12px;")
            self.drive_status.setText("Uploaded to Google Drive!")
        except Exception as e:
            self.drive_status.setStyleSheet(f"color: {COLORS['accent_red']}; font-size: 12px;")
            self.drive_status.setText(f"Upload failed: {e}")

    def _on_drive_restore(self):
        self.drive_status.setText("")
        try:
            backups = gdrive.list_drive_backups()
        except Exception as e:
            self.drive_status.setStyleSheet(f"color: {COLORS['accent_red']}; font-size: 12px;")
            self.drive_status.setText(f"Failed to list Drive backups: {e}")
            return

        if not backups:
            self.drive_status.setStyleSheet(f"color: {COLORS['accent_red']}; font-size: 12px;")
            self.drive_status.setText("No backups found on Google Drive.")
            return

        # Use the latest backup
        latest = backups[0]
        reply = QMessageBox.warning(
            self, "Restore from Google Drive",
            f"This will REPLACE all current data with:\n\n"
            f"  {latest['name']}\n"
            f"  Date: {latest['date']}\n"
            f"  Size: {latest['size_mb']:.1f} MB\n\n"
            "Are you sure?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            tmp = tempfile.mktemp(suffix=".zip", prefix="drive_restore_")
            gdrive.download_backup(latest["id"], tmp)
            restore_backup(tmp)
            os.remove(tmp)
            self.drive_status.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 12px;")
            self.drive_status.setText("Restored from Google Drive! All pages refreshed.")
            self._refresh_all_pages()
        except Exception as e:
            self.drive_status.setStyleSheet(f"color: {COLORS['accent_red']}; font-size: 12px;")
            self.drive_status.setText(f"Restore failed: {e}")

    def _refresh_drive_ui(self):
        """Toggle Drive UI between connected/disconnected states."""
        connected = gdrive.is_connected()

        # Toggle visibility
        self.btn_drive_connect.setVisible(not connected)
        self.btn_drive_upload.setVisible(connected)
        self.btn_drive_restore.setVisible(connected)
        self.btn_drive_disconnect.setVisible(connected)
        self.drive_connected_label.setVisible(connected)
        self.drive_table.setVisible(connected)

        if connected:
            try:
                email = gdrive.get_user_email()
                self.drive_connected_label.setText(f"Connected as {email}")
                self.drive_connected_label.setStyleSheet(
                    f"color: {COLORS['accent_teal']}; font-size: 13px; font-weight: bold;"
                )
            except Exception:
                self.drive_connected_label.setText("Connected")
            self._refresh_drive_table()

    def _refresh_drive_table(self):
        """Load Drive backups into the table."""
        try:
            backups = gdrive.list_drive_backups()
        except Exception:
            backups = []

        self.drive_table.setRowCount(len(backups))
        for row, b in enumerate(backups):
            self.drive_table.setItem(row, 0, QTableWidgetItem(b["name"]))
            self.drive_table.setItem(row, 1, QTableWidgetItem(b["date"]))
            self.drive_table.setItem(row, 2, QTableWidgetItem(f"{b['size_mb']} MB"))
            self.drive_table.setRowHeight(row, 38)

        if not backups:
            self.drive_table.setRowCount(1)
            item = QTableWidgetItem("No backups on Google Drive yet.")
            item.setForeground(QColor(COLORS["text_secondary"]))
            self.drive_table.setItem(0, 0, item)
            self.drive_table.setSpan(0, 0, 1, 3)

    def _refresh_all_pages(self):
        """Refresh every page in the app after a restore."""
        if self._main_window is None:
            return
        stack = self._main_window.stack
        for i in range(stack.count()):
            page = stack.widget(i)
            if hasattr(page, "refresh"):
                page.refresh()

    # ── Refresh ───────────────────────────────────────────────────────────

    def refresh(self):
        self._refresh_drive_ui()

        backups = list_auto_backups()
        self.auto_table.setRowCount(len(backups))
        for row, b in enumerate(backups):
            self.auto_table.setItem(row, 0, QTableWidgetItem(b["name"]))
            self.auto_table.setItem(row, 1, QTableWidgetItem(b["date"]))
            self.auto_table.setItem(row, 2, QTableWidgetItem(f"{b['size_mb']} MB"))
            self.auto_table.setRowHeight(row, 38)

        if not backups:
            self.auto_table.setRowCount(1)
            item = QTableWidgetItem("No auto-backups yet. They are created on app startup.")
            item.setForeground(QColor(COLORS["text_secondary"]))
            self.auto_table.setItem(0, 0, item)
            self.auto_table.setSpan(0, 0, 1, 3)
