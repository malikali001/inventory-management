import logging
from datetime import date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
    QDateEdit, QLineEdit, QMessageBox, QHeaderView, QFrame,
    QScrollArea, QStyle,
)
from PySide6.QtCore import Qt, QDate

from services.product_service import get_all_products
from services.purchase_service import record_purchase, get_purchase_history, delete_purchase
from models.product import Product, ProductUnit
from ui.styles import COLORS

logger = logging.getLogger(__name__)


class PurchasePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._products: list[Product] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Record Purchase")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # Entry form card
        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(12)

        # Date + notes row
        meta_row = QHBoxLayout()
        meta_row.addWidget(QLabel("Purchase Date:"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        self.date_edit.setFixedWidth(140)
        meta_row.addWidget(self.date_edit)
        meta_row.addSpacing(20)
        meta_row.addWidget(QLabel("Notes:"))
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Optional note (e.g. supplier name)")
        meta_row.addWidget(self.notes_edit)
        form_layout.addLayout(meta_row)

        # Item entry table
        self.item_table = QTableWidget()
        self.item_table.setColumnCount(6)
        self.item_table.setHorizontalHeaderLabels(
            ["Product", "Unit", "Quantity", "Price / Unit", "Total", ""]
        )
        self.item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.item_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.item_table.setColumnWidth(1, 110)
        self.item_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.item_table.setColumnWidth(2, 90)
        self.item_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.item_table.setColumnWidth(3, 110)
        self.item_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.item_table.setColumnWidth(4, 100)
        self.item_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.item_table.setColumnWidth(5, 50)
        self.item_table.verticalHeader().setVisible(False)
        self.item_table.setAlternatingRowColors(True)
        self.item_table.setMinimumHeight(200)
        form_layout.addWidget(self.item_table)

        # Add row + purchase subtotal
        bottom_row = QHBoxLayout()
        btn_add_row = QPushButton("+ Add Row")
        btn_add_row.setObjectName("btn_secondary")
        btn_add_row.clicked.connect(self._add_row)
        bottom_row.addWidget(btn_add_row)
        bottom_row.addStretch()
        self.subtotal_label = QLabel("Subtotal: 0")
        bottom_row.addWidget(self.subtotal_label)
        form_layout.addLayout(bottom_row)

        # --- Additional Costs Section ---
        costs_header = QHBoxLayout()
        costs_title = QLabel("Additional Costs")
        costs_title.setStyleSheet("font-size: 13px; font-weight: bold; margin-top: 4px;")
        costs_header.addWidget(costs_title)
        costs_header.addStretch()
        btn_add_cost = QPushButton("+ Add Cost")
        btn_add_cost.setObjectName("btn_secondary")
        btn_add_cost.clicked.connect(self._add_cost_row)
        costs_header.addWidget(btn_add_cost)
        form_layout.addLayout(costs_header)

        self.cost_table = QTableWidget()
        self.cost_table.setColumnCount(3)
        self.cost_table.setHorizontalHeaderLabels(["Cost Name", "Amount", ""])
        self.cost_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cost_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.cost_table.setColumnWidth(1, 150)
        self.cost_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.cost_table.setColumnWidth(2, 50)
        self.cost_table.verticalHeader().setVisible(False)
        self.cost_table.setAlternatingRowColors(True)
        self.cost_table.setVisible(False)
        form_layout.addWidget(self.cost_table)

        # Final total row
        total_row = QHBoxLayout()
        total_row.addStretch()
        self.additional_total_label = QLabel("Additional Costs: 0")
        self.additional_total_label.setStyleSheet("font-size: 13px; color: #888;")
        total_row.addWidget(self.additional_total_label)
        total_row.addSpacing(20)
        self.total_label = QLabel("Final Total: 0")
        total_row.addWidget(self.total_label)
        form_layout.addLayout(total_row)

        btn_submit = QPushButton("Submit Purchase")
        btn_submit.setObjectName("btn_success")
        btn_submit.setFixedHeight(40)
        btn_submit.clicked.connect(self._submit)
        form_layout.addWidget(btn_submit)

        layout.addWidget(form_card)

        # History
        hist_label = QLabel("Recent Purchases")
        hist_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 8px;")
        layout.addWidget(hist_label)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            ["Date", "Items", "Purchase Cost", "Final Cost", "Notes", ""]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setMaximumHeight(200)
        layout.addWidget(self.history_table)

        self._add_row()
        self.refresh()

    def refresh(self):
        self.subtotal_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLORS['accent_blue']};")
        self.total_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['accent_blue']};")
        self._products = get_all_products(active_only=True)
        # Refresh product combos in existing rows
        for row in range(self.item_table.rowCount()):
            combo = self.item_table.cellWidget(row, 0)
            if isinstance(combo, QComboBox):
                current_id = combo.currentData()
                combo.blockSignals(True)
                self._populate_product_combo(combo)
                # Restore selection
                idx = combo.findData(current_id)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                combo.blockSignals(False)
        self._refresh_history()

    def _refresh_history(self):
        purchases = get_purchase_history(limit=30)
        self.history_table.setRowCount(len(purchases))
        for row, p in enumerate(purchases):
            self.history_table.setItem(row, 0, QTableWidgetItem(p.date))
            items_text = ", ".join(
                f"{it.product_name} ({it.quantity:g} {it.unit_name})" for it in p.items
            )
            self.history_table.setItem(row, 1, QTableWidgetItem(items_text))
            self.history_table.setItem(row, 2, QTableWidgetItem(f"{p.total:,.0f}"))
            self.history_table.setItem(row, 3, QTableWidgetItem(f"{p.final_total:,.0f}"))
            self.history_table.setItem(row, 4, QTableWidgetItem(p.notes))

            btn_del = QPushButton()
            btn_del.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
            btn_del.setObjectName("btn_danger")
            btn_del.setFixedSize(32, 26)
            btn_del.setToolTip("Delete purchase")
            btn_del.clicked.connect(lambda _, pid=p.id: self._delete_purchase(pid))
            self.history_table.setCellWidget(row, 5, btn_del)
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

        # Product combo
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
        unit_combo.setMinimumWidth(100)
        self.item_table.setCellWidget(row, 1, unit_combo)

        # Wire product → unit
        product_combo.currentIndexChanged.connect(
            lambda _, r=row: self._on_product_changed(r)
        )

        # Quantity
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

        # Row total (read-only label)
        total_item = QTableWidgetItem("0")
        total_item.setFlags(Qt.ItemIsEnabled)
        total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.item_table.setItem(row, 4, total_item)

        # Remove button
        btn_remove = QPushButton("✕")
        btn_remove.setObjectName("btn_danger")
        btn_remove.setFixedSize(30, 30)
        btn_remove.clicked.connect(lambda _, r=row: self._remove_row(r))
        self.item_table.setCellWidget(row, 5, btn_remove)

    def _add_cost_row(self):
        self.cost_table.setVisible(True)
        row = self.cost_table.rowCount()
        self.cost_table.insertRow(row)
        self.cost_table.setRowHeight(row, 40)

        # Cost name
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g. Transport, Rent, Labour")
        name_edit.setMinimumHeight(32)
        self.cost_table.setCellWidget(row, 0, name_edit)

        # Amount
        amount_spin = QDoubleSpinBox()
        amount_spin.setRange(0, 9999999)
        amount_spin.setValue(0)
        amount_spin.setDecimals(0)
        amount_spin.setSpecialValueText(" ")
        amount_spin.setMinimumHeight(32)
        amount_spin.valueChanged.connect(self._update_total)
        self.cost_table.setCellWidget(row, 1, amount_spin)

        # Remove button
        btn_remove = QPushButton("✕")
        btn_remove.setObjectName("btn_danger")
        btn_remove.setFixedSize(30, 30)
        btn_remove.clicked.connect(lambda _, r=row: self._remove_cost_row(r))
        self.cost_table.setCellWidget(row, 2, btn_remove)

        self._resize_cost_table()

    def _remove_cost_row(self, row: int):
        self.cost_table.removeRow(row)
        if self.cost_table.rowCount() == 0:
            self.cost_table.setVisible(False)
        else:
            self._resize_cost_table()
        self._update_total()

    def _resize_cost_table(self):
        """Resize cost table to fit its content exactly."""
        header_h = self.cost_table.horizontalHeader().height()
        rows_h = sum(
            self.cost_table.rowHeight(r) for r in range(self.cost_table.rowCount())
        )
        # +2 for border
        self.cost_table.setFixedHeight(header_h + rows_h + 2)

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
        # Items subtotal
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
        self.subtotal_label.setText(f"Subtotal: {grand:,.0f}")

        # Additional costs total
        extra = 0.0
        for row in range(self.cost_table.rowCount()):
            amount_spin = self.cost_table.cellWidget(row, 1)
            if amount_spin:
                extra += amount_spin.value()
        self.additional_total_label.setText(f"Additional Costs: {extra:,.0f}")

        # Final total
        self.total_label.setText(f"Final Total: {grand + extra:,.0f}")

    def _submit(self):
        items = self._collect_items()
        if items is None:
            return  # validation error already shown
        if not items:
            QMessageBox.warning(self, "No Items", "Please add at least one item.")
            return
        additional_costs = self._collect_additional_costs()
        if additional_costs is None:
            return  # validation error already shown
        purchase_date = self.date_edit.date().toString("yyyy-MM-dd")
        notes = self.notes_edit.text().strip()
        try:
            record_purchase(purchase_date, notes, items, additional_costs)
        except Exception as e:
            logger.exception("Failed to record purchase")
            QMessageBox.critical(self, "Error", f"Failed to record purchase:\n{e}")
            return
        QMessageBox.information(self, "Saved", "Purchase recorded successfully.")
        self._clear_form()
        self._refresh_history()

    def _collect_items(self) -> list[dict] | None:
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
                QMessageBox.warning(self, "Validation", f"Row {row + 1}: please select a unit.")
                return None

            if qty <= 0:
                QMessageBox.warning(self, "Validation", f"Row {row + 1}: quantity must be greater than 0.")
                return None

            if price <= 0:
                QMessageBox.warning(self, "Validation", f"Row {row + 1}: price must be greater than 0.")
                return None

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

    def _collect_additional_costs(self) -> list[dict] | None:
        costs = []
        for row in range(self.cost_table.rowCount()):
            name_edit = self.cost_table.cellWidget(row, 0)
            amount_spin = self.cost_table.cellWidget(row, 1)

            name = name_edit.text().strip() if name_edit else ""
            amount = amount_spin.value() if amount_spin else 0

            if not name and amount > 0:
                QMessageBox.warning(
                    self, "Validation",
                    f"Additional cost row {row + 1}: please enter a cost name.",
                )
                return None

            if name and amount <= 0:
                QMessageBox.warning(
                    self, "Validation",
                    f"Additional cost row {row + 1}: amount must be greater than 0.",
                )
                return None

            if name and amount > 0:
                costs.append({"cost_name": name, "amount": amount})
        return costs

    def _clear_form(self):
        while self.item_table.rowCount() > 0:
            self.item_table.removeRow(0)
        while self.cost_table.rowCount() > 0:
            self.cost_table.removeRow(0)
        self.cost_table.setVisible(False)
        self.notes_edit.clear()
        self.subtotal_label.setText("Subtotal: 0")
        self.additional_total_label.setText("Additional Costs: 0")
        self.total_label.setText("Final Total: 0")
        self._add_row()

    def _delete_purchase(self, purchase_id: int):
        reply = QMessageBox.question(
            self, "Delete Purchase",
            "Delete this purchase? Inventory will be adjusted.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                delete_purchase(purchase_id)
            except Exception as e:
                logger.exception("Failed to delete purchase")
                QMessageBox.critical(self, "Error", f"Failed to delete purchase:\n{e}")
                return
            self._refresh_history()
