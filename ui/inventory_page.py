from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QLineEdit, QHeaderView,
    QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from services.inventory_service import get_inventory_summary
from services.export_service import export_inventory
from ui.styles import COLORS, LOW_STOCK_ROW_COLOR, LOW_STOCK_TEXT_COLOR


class InventoryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("Inventory")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search product...")
        self.search_box.setFixedWidth(220)
        self.search_box.textChanged.connect(self._filter)
        header.addWidget(self.search_box)

        btn_export = QPushButton("Export CSV")
        btn_export.setObjectName("btn_secondary")
        btn_export.clicked.connect(self._export_csv)
        header.addWidget(btn_export)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setObjectName("btn_secondary")
        btn_refresh.clicked.connect(self.refresh)
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        # Low stock legend
        legend = QLabel("  Items highlighted in yellow are below their low-stock threshold.")
        legend.setStyleSheet(
            f"background: {LOW_STOCK_ROW_COLOR}; color: {LOW_STOCK_TEXT_COLOR};"
            " padding: 6px 10px; border-radius: 4px; font-size: 12px;"
        )
        layout.addWidget(legend)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Product", "Category", "In Stock", "Unit", "Final Cost / Unit", "Stock Value", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Summary bar
        summary_row = QHBoxLayout()
        summary_row.setSpacing(24)
        self.lbl_total_products = QLabel("Products: 0")
        self.lbl_total_products.setStyleSheet("font-size: 13px; font-weight: bold;")
        summary_row.addWidget(self.lbl_total_products)
        self.lbl_total_items = QLabel("Total Items: 0")
        self.lbl_total_items.setStyleSheet("font-size: 13px; font-weight: bold;")
        summary_row.addWidget(self.lbl_total_items)
        summary_row.addStretch()
        self.lbl_total_value = QLabel("Total Stock Value: 0")
        self.lbl_total_value.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['accent_blue']};")
        summary_row.addWidget(self.lbl_total_value)
        layout.addLayout(summary_row)

        self._all_data = []
        self.refresh()

    def refresh(self):
        self._all_data = get_inventory_summary()
        self._render(self._all_data)

    def _filter(self, text: str):
        text = text.lower()
        filtered = [
            d for d in self._all_data
            if text in d["name"].lower() or text in (d["category"] or "").lower()
        ]
        self._render(filtered)

    def _render(self, data: list[dict]):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(data))
        for row, d in enumerate(data):
            name_item = QTableWidgetItem(d["name"])
            cat_item = QTableWidgetItem(d["category"] or "")
            qty_item = QTableWidgetItem(f"{d['display_qty']:,.0f}")
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            unit_item = QTableWidgetItem(d["display_unit"])

            cost = d.get("final_cost_per_unit", 0)
            cost_item = QTableWidgetItem(f"{cost:,.0f}" if cost else "—")
            cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            value = d.get("stock_value", 0)
            value_item = QTableWidgetItem(f"{value:,.0f}" if value else "—")
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            status_item = QTableWidgetItem(
                "Low Stock" if d["is_low"] else "OK"
            )

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, cat_item)
            self.table.setItem(row, 2, qty_item)
            self.table.setItem(row, 3, unit_item)
            self.table.setItem(row, 4, cost_item)
            self.table.setItem(row, 5, value_item)
            self.table.setItem(row, 6, status_item)

            if d["is_low"]:
                bg = QColor(LOW_STOCK_ROW_COLOR)
                fg = QColor(LOW_STOCK_TEXT_COLOR)
                for col in range(7):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(bg)
                        item.setForeground(fg)

            self.table.setRowHeight(row, 38)

        self.table.setSortingEnabled(True)

        # Update summary
        total_products = len(data)
        total_items = sum(d["display_qty"] for d in data)
        total_value = sum(d.get("stock_value", 0) for d in data)
        self.lbl_total_products.setText(f"Products: {total_products}")
        self.lbl_total_items.setText(f"Total Items: {total_items:,.0f}")
        self.lbl_total_value.setText(f"Total Stock Value: {total_value:,.0f}")

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Inventory", "inventory.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            result = export_inventory(path)
            QMessageBox.information(self, "Export Complete", f"Saved to:\n{result}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))
