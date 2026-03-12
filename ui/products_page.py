from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QLineEdit, QDoubleSpinBox, QMessageBox, QHeaderView,
    QCheckBox, QFrame, QScrollArea, QStyle, QComboBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from services.product_service import (
    get_all_products, create_product, update_product,
    deactivate_product, reactivate_product, delete_product,
    get_units_for_product, add_unit, delete_unit, update_unit,
    SUGGESTED_UNITS,
)
from models.product import Product, ProductUnit
from ui.styles import COLORS

# Common units used in retail / wholesale markets
COMMON_BASE_UNITS = [
    "",
    # Count
    "piece", "unit", "pair", "set",
    # Weight
    "kg", "gram", "lb", "oz",
    # Volume
    "litre", "ml", "gallon",
    # Length
    "meter", "foot", "inch", "yard",
    # Packaging
    "bottle", "can", "bag", "roll", "sheet",
]

COMMON_EXTRA_UNITS = [
    "",
    # Count / grouping
    "piece", "unit", "dozen (12 pcs)", "half dozen (6 pcs)",
    "pair (2 pcs)", "set", "bundle",
    # Packaging / wholesale
    "box", "carton", "case", "pack", "packet",
    "bag", "pallet", "crate",
    # Weight
    "kg", "gram", "lb", "oz",
    # Volume
    "litre", "ml", "gallon",
    # Length / area
    "meter", "foot", "yard", "roll", "sheet", "ream",
]


class ProductsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("Products")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()
        btn_add = QPushButton("+ Add Product")
        btn_add.clicked.connect(self._add_product)
        header.addWidget(btn_add)
        layout.addLayout(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Category", "Base Unit", "Units Defined", "Low Stock At", "Actions"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 130)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        products = get_all_products(active_only=False)
        self.table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.table.setItem(row, 0, QTableWidgetItem(p.name))
            self.table.setItem(row, 1, QTableWidgetItem(p.category))
            self.table.setItem(row, 2, QTableWidgetItem(p.base_unit))
            self.table.setItem(row, 3, QTableWidgetItem(str(len(p.units))))
            self.table.setItem(row, 4, QTableWidgetItem(f"{p.low_stock_threshold:,.0f}"))

            # Dim inactive rows
            if not p.is_active:
                for col in range(5):
                    item = self.table.item(row, col)
                    if item:
                        item.setForeground(QColor(COLORS["text_dimmed"]))

            # Action buttons
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            style = self.style()

            btn_edit = QPushButton()
            btn_edit.setIcon(style.standardIcon(QStyle.SP_FileDialogDetailedView))
            btn_edit.setFixedSize(32, 28)
            btn_edit.setToolTip("Edit product")
            btn_edit.clicked.connect(lambda _, prod=p: self._edit_product(prod))
            btn_layout.addWidget(btn_edit)

            btn_units = QPushButton()
            btn_units.setIcon(style.standardIcon(QStyle.SP_FileDialogListView))
            btn_units.setFixedSize(32, 28)
            btn_units.setToolTip("Manage units")
            btn_units.setObjectName("btn_secondary")
            btn_units.clicked.connect(lambda _, prod=p: self._manage_units(prod))
            btn_layout.addWidget(btn_units)

            if p.is_active:
                btn_remove = QPushButton()
                btn_remove.setIcon(style.standardIcon(QStyle.SP_TrashIcon))
                btn_remove.setObjectName("btn_danger")
                btn_remove.setFixedSize(32, 28)
                btn_remove.setToolTip("Remove product")
                btn_remove.clicked.connect(
                    lambda _, pid=p.id, pname=p.name: self._remove_product(pid, pname)
                )
                btn_layout.addWidget(btn_remove)
            else:
                btn_enable = QPushButton()
                btn_enable.setIcon(style.standardIcon(QStyle.SP_DialogApplyButton))
                btn_enable.setObjectName("btn_success")
                btn_enable.setFixedSize(32, 28)
                btn_enable.setToolTip("Re-enable product")
                btn_enable.clicked.connect(lambda _, pid=p.id: self._enable_product(pid))
                btn_layout.addWidget(btn_enable)

            self.table.setCellWidget(row, 5, btn_widget)
            self.table.setRowHeight(row, 44)

    def _add_product(self):
        dlg = ProductDialog(self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.get_data()
            create_product(
                d["name"], d["category"], d["base_unit"], d["threshold"],
                purchase_unit=d.get("purchase_unit"),
                purchase_conversion=d.get("purchase_conversion"),
                sale_unit=d.get("sale_unit"),
                sale_conversion=d.get("sale_conversion"),
            )
            self.refresh()

    def _edit_product(self, product: Product):
        dlg = ProductDialog(self, product)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.get_data()
            update_product(product.id, d["name"], d["category"], d["base_unit"], d["threshold"])
            # Update purchase/sale unit defaults if changed
            self._sync_unit_defaults(product, d)
            self.refresh()

    def _sync_unit_defaults(self, product: Product, data: dict):
        """Sync purchase/sale default units after product edit."""
        base = data["base_unit"]
        pu_name = data.get("purchase_unit")  # None means base unit
        su_name = data.get("sale_unit")      # None means base unit
        pu_conv = data.get("purchase_conversion") or 1
        su_conv = data.get("sale_conversion") or 1

        units = get_units_for_product(product.id)
        existing_by_name = {u.unit_name.lower(): u for u in units}

        # Determine desired purchase default
        desired_purchase = pu_name or base
        desired_sale = su_name or base

        # Handle purchase unit
        if desired_purchase.lower() in existing_by_name:
            u = existing_by_name[desired_purchase.lower()]
            if not u.is_default_purchase:
                update_unit(u.id, u.unit_name, u.conversion_to_base, True, u.is_default_sale)
        elif pu_name:
            add_unit(product.id, pu_name, pu_conv, is_default_purchase=True)

        # Refresh units after purchase change
        units = get_units_for_product(product.id)
        existing_by_name = {u.unit_name.lower(): u for u in units}

        # Handle sale unit
        if desired_sale.lower() in existing_by_name:
            u = existing_by_name[desired_sale.lower()]
            if not u.is_default_sale:
                update_unit(u.id, u.unit_name, u.conversion_to_base, u.is_default_purchase, True)
        elif su_name:
            add_unit(product.id, su_name, su_conv, is_default_sale=True)

    def _remove_product(self, product_id: int, product_name: str):
        """Two-step removal: first ask Disable or Delete, then confirm if Delete."""
        dlg = RemoveProductDialog(self, product_name)
        result = dlg.exec()
        if result == RemoveProductDialog.DISABLE:
            deactivate_product(product_id)
            self.refresh()
        elif result == RemoveProductDialog.DELETE:
            confirm = QMessageBox.warning(
                self, "Confirm Permanent Deletion",
                f"Are you absolutely sure?\n\n"
                f"\"{product_name}\" and ALL its purchase/sale history "
                f"will be permanently deleted.\n\n"
                "This cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if confirm == QMessageBox.Yes:
                delete_product(product_id)
                self.refresh()

    def _enable_product(self, product_id: int):
        reactivate_product(product_id)
        self.refresh()

    def _manage_units(self, product: Product):
        dlg = UnitsDialog(self, product)
        dlg.exec()
        self.refresh()


class RemoveProductDialog(QDialog):
    """First-step modal: asks the user to Disable or Delete Permanently."""
    DISABLE = 1
    DELETE = 2

    def __init__(self, parent=None, product_name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Remove Product")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        msg = QLabel(f"What do you want to do with \"{product_name}\"?")
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 14px;")
        layout.addWidget(msg)

        # Option 1: Disable
        btn_disable = QPushButton("Disable  —  hide from dropdowns, keep history")
        btn_disable.setObjectName("btn_secondary")
        btn_disable.setFixedHeight(42)
        btn_disable.clicked.connect(lambda: self.done(self.DISABLE))
        layout.addWidget(btn_disable)

        # Option 2: Delete permanently
        btn_delete = QPushButton("Delete Permanently  —  remove all data forever")
        btn_delete.setObjectName("btn_danger")
        btn_delete.setFixedHeight(42)
        btn_delete.clicked.connect(lambda: self.done(self.DELETE))
        layout.addWidget(btn_delete)

        # Cancel
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(36)
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)


class ProductDialog(QDialog):
    def __init__(self, parent=None, product: Product = None):
        super().__init__(parent)
        self._product = product
        self.setWindowTitle("Add Product" if not product else "Edit Product")
        self.setMinimumWidth(440)
        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Soap, Rice, Oil")
        layout.addRow("Product Name *", self.name_edit)

        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("e.g. Household, Food")
        layout.addRow("Category", self.category_edit)

        self.base_unit_edit = QComboBox()
        self.base_unit_edit.setEditable(True)
        self.base_unit_edit.addItems(COMMON_BASE_UNITS)
        self.base_unit_edit.setCurrentText("")
        self.base_unit_edit.lineEdit().setPlaceholderText("e.g. piece, kg, litre")
        layout.addRow("Base Unit *", self.base_unit_edit)

        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0, 999999)
        self.threshold_spin.setDecimals(0)
        self.threshold_spin.setToolTip("Warn when stock (in base units) falls to or below this")
        layout.addRow("Low Stock Alert (base units)", self.threshold_spin)

        # ── Unit Setup section ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addRow(sep)

        unit_header = QLabel("Unit Setup")
        unit_header.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addRow(unit_header)

        # Purchase unit row: combo + conversion spin
        purchase_row = QHBoxLayout()
        self.purchase_unit_combo = QComboBox()
        self.purchase_unit_combo.setEditable(True)
        self.purchase_unit_combo.lineEdit().setPlaceholderText("same as base unit")
        self.purchase_unit_combo.setMinimumWidth(140)
        purchase_row.addWidget(self.purchase_unit_combo)
        purchase_row.addWidget(QLabel("1 unit ="))
        self.purchase_conversion = QDoubleSpinBox()
        self.purchase_conversion.setRange(0.001, 999999)
        self.purchase_conversion.setDecimals(3)
        self.purchase_conversion.setValue(1)
        self.purchase_conversion.setEnabled(False)
        purchase_row.addWidget(self.purchase_conversion)
        self.purchase_base_label = QLabel("base unit(s)")
        purchase_row.addWidget(self.purchase_base_label)
        layout.addRow("Purchase Unit", purchase_row)

        # Sale unit row: combo + conversion spin
        sale_row = QHBoxLayout()
        self.sale_unit_combo = QComboBox()
        self.sale_unit_combo.setEditable(True)
        self.sale_unit_combo.lineEdit().setPlaceholderText("same as base unit")
        self.sale_unit_combo.setMinimumWidth(140)
        sale_row.addWidget(self.sale_unit_combo)
        sale_row.addWidget(QLabel("1 unit ="))
        self.sale_conversion = QDoubleSpinBox()
        self.sale_conversion.setRange(0.001, 999999)
        self.sale_conversion.setDecimals(3)
        self.sale_conversion.setValue(1)
        self.sale_conversion.setEnabled(False)
        sale_row.addWidget(self.sale_conversion)
        self.sale_base_label = QLabel("base unit(s)")
        sale_row.addWidget(self.sale_base_label)
        layout.addRow("Sale Unit", sale_row)

        # Manage Units button (for adding more units beyond purchase/sale defaults)
        if product:
            btn_manage = QPushButton("Manage Units...")
            btn_manage.setObjectName("btn_secondary")
            btn_manage.setToolTip("Add more units or change defaults")
            btn_manage.clicked.connect(self._open_units_dialog)
            layout.addRow("", btn_manage)

        # Connect signals
        self.base_unit_edit.currentTextChanged.connect(self._on_base_unit_changed)
        self.purchase_unit_combo.currentTextChanged.connect(self._on_purchase_unit_changed)
        self.sale_unit_combo.currentTextChanged.connect(self._on_sale_unit_changed)

        # Populate with existing data
        if product:
            self.name_edit.setText(product.name)
            self.category_edit.setText(product.category)
            self.base_unit_edit.setCurrentText(product.base_unit)
            self.threshold_spin.setValue(product.low_stock_threshold)
            self._populate_unit_combos(product.base_unit)
            # Pre-select current default purchase/sale units
            for u in product.units:
                if u.is_default_purchase:
                    self.purchase_unit_combo.setCurrentText(u.unit_name)
                    self.purchase_conversion.setValue(u.conversion_to_base)
                if u.is_default_sale:
                    self.sale_unit_combo.setCurrentText(u.unit_name)
                    self.sale_conversion.setValue(u.conversion_to_base)
        else:
            self._populate_unit_combos("")

        btns = QHBoxLayout()
        btn_ok = QPushButton("Save")
        btn_ok.clicked.connect(self._validate_and_accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addRow(btns)

    def _populate_unit_combos(self, base_unit: str):
        """Populate purchase/sale unit combos with base unit + suggestions."""
        base = base_unit.strip()
        suggestions = SUGGESTED_UNITS.get(base.lower(), [])

        for combo in (self.purchase_unit_combo, self.sale_unit_combo):
            prev = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            # First item: the base unit itself (means "same as base")
            if base:
                combo.addItem(base)
            # Add suggested units
            for name, _conv in suggestions:
                combo.addItem(name)
            combo.setCurrentText(prev if prev else base)
            combo.blockSignals(False)

        # Update labels
        label_text = f"{base}(s)" if base else "base unit(s)"
        self.purchase_base_label.setText(label_text)
        self.sale_base_label.setText(label_text)

    def _on_base_unit_changed(self, text: str):
        self._populate_unit_combos(text)
        # Reset to base unit
        base = text.strip()
        self.purchase_unit_combo.setCurrentText(base)
        self.sale_unit_combo.setCurrentText(base)

    def _on_purchase_unit_changed(self, text: str):
        base = self.base_unit_edit.currentText().strip()
        is_base = (text.strip().lower() == base.lower()) or not text.strip()
        self.purchase_conversion.setEnabled(not is_base)
        if is_base:
            self.purchase_conversion.setValue(1)
        else:
            # Auto-fill conversion from suggestions if available
            for name, conv in SUGGESTED_UNITS.get(base.lower(), []):
                if name.lower() == text.strip().lower():
                    self.purchase_conversion.setValue(conv)
                    break

    def _on_sale_unit_changed(self, text: str):
        base = self.base_unit_edit.currentText().strip()
        is_base = (text.strip().lower() == base.lower()) or not text.strip()
        self.sale_conversion.setEnabled(not is_base)
        if is_base:
            self.sale_conversion.setValue(1)
        else:
            for name, conv in SUGGESTED_UNITS.get(base.lower(), []):
                if name.lower() == text.strip().lower():
                    self.sale_conversion.setValue(conv)
                    break

    def _open_units_dialog(self):
        if self._product:
            from services.product_service import get_product_by_id
            product = get_product_by_id(self._product.id)
            if product:
                dlg = UnitsDialog(self, product)
                dlg.exec()

    def _validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Product name is required.")
            return
        if not self.base_unit_edit.currentText().strip():
            QMessageBox.warning(self, "Validation", "Base unit is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        base = self.base_unit_edit.currentText().strip()
        pu = self.purchase_unit_combo.currentText().strip()
        su = self.sale_unit_combo.currentText().strip()
        return {
            "name": self.name_edit.text().strip(),
            "category": self.category_edit.text().strip(),
            "base_unit": base,
            "threshold": self.threshold_spin.value(),
            "purchase_unit": pu if pu and pu.lower() != base.lower() else None,
            "purchase_conversion": self.purchase_conversion.value() if pu and pu.lower() != base.lower() else None,
            "sale_unit": su if su and su.lower() != base.lower() else None,
            "sale_conversion": self.sale_conversion.value() if su and su.lower() != base.lower() else None,
        }


class UnitsDialog(QDialog):
    def __init__(self, parent=None, product: Product = None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle(f"Units — {product.name}")
        self.setMinimumWidth(520)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info = QLabel(
            f"Base unit: <b>{product.base_unit}</b>  "
            "— All other units are defined as multiples of the base unit."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Units table
        self.units_table = QTableWidget()
        self.units_table.setColumnCount(5)
        self.units_table.setHorizontalHeaderLabels(
            ["Unit Name", "= N base units", "Default Purchase", "Default Sale", ""]
        )
        self.units_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.units_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.units_table.verticalHeader().setVisible(False)
        layout.addWidget(self.units_table)

        # Add unit form
        form_frame = QFrame()
        form_frame.setObjectName("card")
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(8)

        add_label = QLabel("Add New Unit")
        add_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow(add_label)

        self.new_unit_name = QComboBox()
        self.new_unit_name.setEditable(True)
        self.new_unit_name.addItems(COMMON_EXTRA_UNITS)
        self.new_unit_name.setCurrentText("")
        self.new_unit_name.lineEdit().setPlaceholderText("e.g. dozen, bundle, carton")
        form_layout.addRow("Unit Name", self.new_unit_name)

        self.new_conversion = QDoubleSpinBox()
        self.new_conversion.setRange(0.001, 999999)
        self.new_conversion.setValue(12)
        self.new_conversion.setDecimals(0)
        form_layout.addRow(f"1 unit = N {product.base_unit}s", self.new_conversion)

        self.chk_def_purchase = QCheckBox("Set as default for purchases")
        self.chk_def_sale = QCheckBox("Set as default for sales")
        form_layout.addRow(self.chk_def_purchase)
        form_layout.addRow(self.chk_def_sale)

        btn_add = QPushButton("Add Unit")
        btn_add.clicked.connect(self._add_unit)
        form_layout.addRow(btn_add)

        layout.addWidget(form_frame)

        btn_close = QPushButton("Close")
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self._refresh_units()

    def _refresh_units(self):
        units = get_units_for_product(self.product.id)
        self.units_table.setRowCount(len(units))
        for row, u in enumerate(units):
            self.units_table.setItem(row, 0, QTableWidgetItem(u.unit_name))
            self.units_table.setItem(row, 1, QTableWidgetItem(f"{u.conversion_to_base:,.0f}"))
            self.units_table.setItem(row, 2, QTableWidgetItem("Yes" if u.is_default_purchase else ""))
            self.units_table.setItem(row, 3, QTableWidgetItem("Yes" if u.is_default_sale else ""))
            for col in range(4):
                item = self.units_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)

            btn_del = QPushButton()
            btn_del.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
            btn_del.setObjectName("btn_danger")
            btn_del.setFixedSize(32, 26)
            btn_del.setToolTip("Remove unit")
            btn_del.clicked.connect(lambda _, uid=u.id: self._delete_unit(uid))
            self.units_table.setCellWidget(row, 4, btn_del)
            self.units_table.setRowHeight(row, 38)

    def _add_unit(self):
        name = self.new_unit_name.currentText().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Unit name is required.")
            return
        add_unit(
            self.product.id,
            name,
            self.new_conversion.value(),
            self.chk_def_purchase.isChecked(),
            self.chk_def_sale.isChecked(),
        )
        self.new_unit_name.setCurrentText("")
        self._refresh_units()

    def _delete_unit(self, unit_id: int):
        reply = QMessageBox.question(
            self, "Remove Unit", "Remove this unit? Historical records are not affected.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            delete_unit(unit_id)
            self._refresh_units()
