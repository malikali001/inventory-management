from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QWidget, QGridLayout,
    QDoubleSpinBox, QMessageBox, QFrame,
)
from PySide6.QtCore import Qt

from services.picker_service import (
    get_all_units, add_custom_unit,
    get_all_categories, add_custom_category,
)
from ui.styles import COLORS


class ItemPickerDialog(QDialog):
    """Reusable picker modal for units (with counts) or categories."""

    def __init__(self, parent=None, mode="unit"):
        super().__init__(parent)
        self._mode = mode
        self._selected_name = None
        self._selected_count = None

        self.setWindowTitle("Select Unit" if mode == "unit" else "Select Category")
        self.setMinimumWidth(480)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Search field
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search...")
        self._search.textChanged.connect(self._filter_items)
        layout.addWidget(self._search)

        # Scrollable grid area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(8)
        self._scroll.setWidget(self._grid_container)
        layout.addWidget(self._scroll, 1)

        # Add custom section
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        self._custom_frame = QWidget()
        custom_layout = QHBoxLayout(self._custom_frame)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(8)

        self._custom_name = QLineEdit()
        self._custom_name.setPlaceholderText(
            "New unit name..." if mode == "unit" else "New category name..."
        )
        custom_layout.addWidget(self._custom_name, 1)

        if mode == "unit":
            custom_layout.addWidget(QLabel("Count:"))
            self._custom_count = QDoubleSpinBox()
            self._custom_count.setRange(0.001, 999999)
            self._custom_count.setDecimals(3)
            self._custom_count.setValue(1)
            self._custom_count.setFixedWidth(90)
            custom_layout.addWidget(self._custom_count)

        btn_add = QPushButton("+ Add")
        btn_add.clicked.connect(self._add_custom)
        custom_layout.addWidget(btn_add)

        layout.addWidget(self._custom_frame)

        # Cancel
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)

        self._load_items()

    def _load_items(self):
        """Load items from DB and build the grid."""
        if self._mode == "unit":
            self._items = get_all_units()
        else:
            self._items = [{"name": c} for c in get_all_categories()]
        self._build_grid(self._items)

    def _build_grid(self, items):
        """Build the grid of clickable chips."""
        # Clear existing
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = 3
        for i, item in enumerate(items):
            name = item["name"]
            if self._mode == "unit":
                count = item.get("default_count", 1)
                count_str = f"{count:g}"
                label = f"{name} ({count_str})"
            else:
                label = name

            btn = QPushButton(label)
            btn.setFixedHeight(36)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self._chip_style())
            if self._mode == "unit":
                btn.clicked.connect(
                    lambda _, n=name, c=item.get("default_count", 1): self._pick(n, c)
                )
            else:
                btn.clicked.connect(lambda _, n=name: self._pick(n))
            self._grid_layout.addWidget(btn, i // cols, i % cols)

    def _chip_style(self):
        c = COLORS
        return f"""
            QPushButton {{
                background: {c['bg_elevated']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {c['accent_blue']};
                color: white;
                border-color: {c['accent_blue']};
            }}
        """

    def _filter_items(self, text):
        query = text.strip().lower()
        if not query:
            filtered = self._items
        else:
            filtered = [i for i in self._items if query in i["name"].lower()]
        self._build_grid(filtered)

    def _pick(self, name, count=None):
        self._selected_name = name
        self._selected_count = count
        self.accept()

    def _add_custom(self):
        name = self._custom_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Name is required.")
            return
        if self._mode == "unit":
            count = self._custom_count.value()
            add_custom_unit(name, count)
            self._pick(name, count)
        else:
            add_custom_category(name)
            self._pick(name)

    def get_selected(self):
        """Return (name, count) for units or (name, None) for categories."""
        return self._selected_name, self._selected_count
