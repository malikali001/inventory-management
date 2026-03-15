from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
    QDateEdit, QLineEdit, QMessageBox, QHeaderView, QFrame, QStyle,
)
from PySide6.QtCore import Qt, QDate

from services.product_service import get_all_products
from services.sale_service import record_sale, get_sale_history, delete_sale
from models.product import Product
from ui.styles import COLORS


class SalesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._products: list[Product] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Enter Daily Sales")
        title.setObjectName("page_title")
        layout.addWidget(title)

        hint = QLabel(
            "Enter sales from your register. Select each product from the dropdown, "
            "choose its unit, then enter quantity and selling price."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(hint)

        # Entry card
        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(12)

        # Date + notes
        meta_row = QHBoxLayout()
        meta_row.addWidget(QLabel("Sale Date:"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        self.date_edit.setFixedWidth(140)
        meta_row.addWidget(self.date_edit)
        meta_row.addSpacing(20)
        meta_row.addWidget(QLabel("Notes:"))
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Optional (e.g. market day)")
        meta_row.addWidget(self.notes_edit)
        form_layout.addLayout(meta_row)

        # Sales item table
        self.item_table = QTableWidget()
        self.item_table.setColumnCount(6)
        self.item_table.setHorizontalHeaderLabels(
            ["Product", "Unit", "Quantity Sold", "Sell Price / Unit", "Total", ""]
        )
        self.item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.item_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.item_table.setColumnWidth(1, 110)
        self.item_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.item_table.setColumnWidth(2, 110)
        self.item_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.item_table.setColumnWidth(3, 130)
        self.item_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.item_table.setColumnWidth(4, 100)
        self.item_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.item_table.setColumnWidth(5, 50)
        self.item_table.verticalHeader().setVisible(False)
        self.item_table.setAlternatingRowColors(True)
        self.item_table.setMinimumHeight(220)
        form_layout.addWidget(self.item_table)

        bottom_row = QHBoxLayout()
        btn_add_row = QPushButton("+ Add Row")
        btn_add_row.setObjectName("btn_secondary")
        btn_add_row.clicked.connect(self._add_row)
        bottom_row.addWidget(btn_add_row)
        bottom_row.addStretch()
        self.total_label = QLabel("Total Revenue: 0")
        bottom_row.addWidget(self.total_label)
        form_layout.addLayout(bottom_row)

        btn_submit = QPushButton("Submit Sales Entry")
        btn_submit.setObjectName("btn_success")
        btn_submit.setFixedHeight(40)
        btn_submit.clicked.connect(self._submit)
        form_layout.addWidget(btn_submit)

        layout.addWidget(form_card)

        # History
        hist_label = QLabel("Recent Sales Entries")
        hist_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 8px;")
        layout.addWidget(hist_label)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(
            ["Sale Date", "Items", "Revenue", "Notes", ""]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setMaximumHeight(200)
        layout.addWidget(self.history_table)

        self._add_row()
        self.refresh()

    def refresh(self):
        self.total_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['accent_teal']};")
        self._products = get_all_products(active_only=True)
        for row in range(self.item_table.rowCount()):
            combo = self.item_table.cellWidget(row, 0)
            if isinstance(combo, QComboBox):
                current_id = combo.currentData()
                combo.blockSignals(True)
                self._populate_product_combo(combo)
                idx = combo.findData(current_id)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                combo.blockSignals(False)
        self._refresh_history()

    def _refresh_history(self):
        sales = get_sale_history(limit=30)
        self.history_table.setRowCount(len(sales))
        for row, s in enumerate(sales):
            self.history_table.setItem(row, 0, QTableWidgetItem(s.date))
            items_text = ", ".join(
                f"{it.product_name} ({it.quantity:g} {it.unit_name})" for it in s.items
            )
            self.history_table.setItem(row, 1, QTableWidgetItem(items_text))
            self.history_table.setItem(row, 2, QTableWidgetItem(f"{s.total:,.0f}"))
            self.history_table.setItem(row, 3, QTableWidgetItem(s.notes))

            btn_del = QPushButton()
            btn_del.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
            btn_del.setObjectName("btn_danger")
            btn_del.setFixedSize(32, 26)
            btn_del.setToolTip("Delete sale")
            btn_del.clicked.connect(lambda _, sid=s.id: self._delete_sale(sid))
            self.history_table.setCellWidget(row, 4, btn_del)
            self.history_table.setRowHeight(row, 38)

    def _populate_product_combo(self, combo: QComboBox):
        combo.clear()
        combo.addItem("-- Select Product --", None)
        for p in self._products:
            combo.addItem(p.name, p.id)

    def _add_row(self):
        row = self.item_table.rowCount()
        self.item_table.insertRow(row)
        self.item_table.setRowHeight(row, 44)

        # Product combo (searchable)
        product_combo = QComboBox()
        product_combo.setEditable(True)
        product_combo.setInsertPolicy(QComboBox.NoInsert)
        if product_combo.completer():
            product_combo.completer().setFilterMode(Qt.MatchContains)
            product_combo.completer().setCaseSensitivity(Qt.CaseInsensitive)
        self._populate_product_combo(product_combo)
        self.item_table.setCellWidget(row, 0, product_combo)

        # Unit combo
        unit_combo = QComboBox()
        self.item_table.setCellWidget(row, 1, unit_combo)

        product_combo.currentIndexChanged.connect(
            lambda _, r=row: self._on_product_changed(r)
        )

        # Qty
        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(0, 999999)
        qty_spin.setValue(0)
        qty_spin.setDecimals(0)
        qty_spin.setSpecialValueText(" ")
        qty_spin.valueChanged.connect(self._update_total)
        self.item_table.setCellWidget(row, 2, qty_spin)

        # Price
        price_spin = QDoubleSpinBox()
        price_spin.setRange(0, 9999999)
        price_spin.setValue(0)
        price_spin.setDecimals(0)
        price_spin.setSpecialValueText(" ")
        price_spin.valueChanged.connect(self._update_total)
        self.item_table.setCellWidget(row, 3, price_spin)

        # Row total
        total_item = QTableWidgetItem("0")
        total_item.setFlags(Qt.ItemIsEnabled)
        total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.item_table.setItem(row, 4, total_item)

        # Remove
        btn_remove = QPushButton("✕")
        btn_remove.setObjectName("btn_danger")
        btn_remove.setFixedSize(30, 30)
        btn_remove.clicked.connect(lambda _, r=row: self._remove_row(r))
        self.item_table.setCellWidget(row, 5, btn_remove)

    def _on_product_changed(self, row: int):
        product_combo = self.item_table.cellWidget(row, 0)
        unit_combo = self.item_table.cellWidget(row, 1)
        if not product_combo or not unit_combo:
            return
        product_id = product_combo.currentData()
        unit_combo.clear()
        if product_id is None:
            return
        product = next((p for p in self._products if p.id == product_id), None)
        if not product:
            return
        for u in product.units:
            unit_combo.addItem(u.unit_name, u.id)
            if u.conversion_to_base == 1:
                unit_combo.setCurrentIndex(unit_combo.count() - 1)

    def _remove_row(self, row: int):
        self.item_table.removeRow(row)
        self._update_total()

    def _update_total(self):
        grand = 0.0
        for row in range(self.item_table.rowCount()):
            qty_spin = self.item_table.cellWidget(row, 2)
            price_spin = self.item_table.cellWidget(row, 3)
            if qty_spin and price_spin:
                line_total = qty_spin.value() * price_spin.value()
                grand += line_total
                item = self.item_table.item(row, 4)
                if item:
                    item.setText(f"{line_total:,.0f}")
        self.total_label.setText(f"Total Revenue: {grand:,.0f}")

    def _submit(self):
        items = self._collect_items()
        if not items:
            QMessageBox.warning(self, "No Items", "Please add at least one item.")
            return
        sale_date = self.date_edit.date().toString("yyyy-MM-dd")
        notes = self.notes_edit.text().strip()
        record_sale(sale_date, notes, items)
        QMessageBox.information(self, "Saved", "Sales entry recorded successfully.")
        self._clear_form()
        self._refresh_history()

    def _collect_items(self) -> list[dict]:
        items = []
        for row in range(self.item_table.rowCount()):
            product_combo = self.item_table.cellWidget(row, 0)
            unit_combo = self.item_table.cellWidget(row, 1)
            qty_spin = self.item_table.cellWidget(row, 2)
            price_spin = self.item_table.cellWidget(row, 3)

            product_id = product_combo.currentData() if product_combo else None
            unit_id = unit_combo.currentData() if unit_combo else None
            qty = qty_spin.value() if qty_spin else 0
            price = price_spin.value() if price_spin else 0

            if product_id is None:
                continue

            product = next((p for p in self._products if p.id == product_id), None)
            if not product:
                continue
            unit = next((u for u in product.units if u.id == unit_id), None)
            if not unit:
                continue

            items.append({
                "product_id": product_id,
                "product_name": product.name,
                "unit_id": unit_id,
                "unit_name": unit.unit_name,
                "quantity": qty,
                "price_per_unit": price,
                "conversion_to_base": unit.conversion_to_base,
            })
        return items

    def _clear_form(self):
        while self.item_table.rowCount() > 0:
            self.item_table.removeRow(0)
        self.notes_edit.clear()
        self.total_label.setText("Total Revenue: 0")
        self._add_row()

    def _delete_sale(self, sale_id: int):
        reply = QMessageBox.question(
            self, "Delete Sale Entry",
            "Delete this sale? Inventory will be restored.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            delete_sale(sale_id)
            self._refresh_history()
