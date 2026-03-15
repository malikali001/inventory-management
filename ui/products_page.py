from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QLineEdit, QDoubleSpinBox, QMessageBox, QHeaderView,
    QFrame, QStyle,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from services.product_service import (
    get_all_products, create_product, update_product,
    deactivate_product, reactivate_product, delete_product,
    get_units_for_product, add_unit, delete_unit,
    SUGGESTED_UNITS,
)
from models.product import Product, ProductUnit
from ui.styles import COLORS
from ui.dialogs.picker_dialog import ItemPickerDialog


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
            create_product(d["name"], d["category"], d["base_unit"], d["threshold"])
            self.refresh()

    def _edit_product(self, product: Product):
        dlg = ProductDialog(self, product)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.get_data()
            update_product(product.id, d["name"], d["category"], d["base_unit"], d["threshold"])
            self.refresh()

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
        self.setWindowTitle("Add Product" if not product else "Edit Product")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Soap, Rice, Oil")
        layout.addRow("Product Name *", self.name_edit)

        # Category field with picker button
        cat_row = QHBoxLayout()
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Click browse to select")
        self.category_edit.setReadOnly(True)
        cat_row.addWidget(self.category_edit)
        btn_cat = QPushButton("...")
        btn_cat.setFixedWidth(36)
        btn_cat.setToolTip("Select category")
        btn_cat.clicked.connect(self._pick_category)
        cat_row.addWidget(btn_cat)
        layout.addRow("Category", cat_row)

        # Base unit field with picker button
        unit_row = QHBoxLayout()
        self.base_unit_edit = QLineEdit()
        self.base_unit_edit.setPlaceholderText("Click browse to select")
        self.base_unit_edit.setReadOnly(True)
        unit_row.addWidget(self.base_unit_edit)
        btn_unit = QPushButton("...")
        btn_unit.setFixedWidth(36)
        btn_unit.setToolTip("Select unit")
        btn_unit.clicked.connect(self._pick_unit)
        unit_row.addWidget(btn_unit)
        layout.addRow("Base Unit *", unit_row)

        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0, 999999)
        self.threshold_spin.setDecimals(0)
        self.threshold_spin.setToolTip("Warn when stock (in base units) falls to or below this")
        layout.addRow("Low Stock Alert (base units)", self.threshold_spin)

        if product:
            self.name_edit.setText(product.name)
            self.category_edit.setText(product.category)
            self.base_unit_edit.setText(product.base_unit)
            self.threshold_spin.setValue(product.low_stock_threshold)

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

    def _pick_category(self):
        dlg = ItemPickerDialog(self, mode="category")
        if dlg.exec() == QDialog.Accepted:
            name, _ = dlg.get_selected()
            if name:
                self.category_edit.setText(name)

    def _pick_unit(self):
        dlg = ItemPickerDialog(self, mode="unit")
        if dlg.exec() == QDialog.Accepted:
            name, _ = dlg.get_selected()
            if name:
                self.base_unit_edit.setText(name)

    def _validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Product name is required.")
            return
        if not self.base_unit_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Base unit is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "category": self.category_edit.text().strip(),
            "base_unit": self.base_unit_edit.text().strip(),
            "threshold": self.threshold_spin.value(),
        }


class UnitsDialog(QDialog):
    def __init__(self, parent=None, product: Product = None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle(f"Units — {product.name}")
        self.setMinimumWidth(480)
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
        self.units_table.setColumnCount(3)
        self.units_table.setHorizontalHeaderLabels(
            ["Unit Name", f"= N {product.base_unit}(s)", ""]
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

        # Unit name with picker button
        name_row = QHBoxLayout()
        self.new_unit_name = QLineEdit()
        self.new_unit_name.setPlaceholderText("Click browse to select")
        self.new_unit_name.setReadOnly(True)
        name_row.addWidget(self.new_unit_name)
        btn_pick = QPushButton("...")
        btn_pick.setFixedWidth(36)
        btn_pick.setToolTip("Select unit from list")
        btn_pick.clicked.connect(self._pick_unit_name)
        name_row.addWidget(btn_pick)
        form_layout.addRow("Unit Name", name_row)

        self.new_conversion = QDoubleSpinBox()
        self.new_conversion.setRange(0.001, 999999)
        self.new_conversion.setValue(1)
        self.new_conversion.setDecimals(3)
        form_layout.addRow(f"1 unit = N {product.base_unit}(s)", self.new_conversion)

        btn_add = QPushButton("Add Unit")
        btn_add.clicked.connect(self._add_unit)
        form_layout.addRow(btn_add)

        layout.addWidget(form_frame)

        btn_close = QPushButton("Close")
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self._refresh_units()

    def _pick_unit_name(self):
        dlg = ItemPickerDialog(self, mode="unit")
        if dlg.exec() == QDialog.Accepted:
            name, count = dlg.get_selected()
            if name:
                self.new_unit_name.setText(name)
                self.new_conversion.setValue(
                    self._compute_conversion(name, count or 1)
                )

    def _compute_conversion(self, unit_name: str, fallback: float) -> float:
        """Compute conversion_to_base for unit_name relative to product's base unit.

        Strategy:
        1. Same as base unit → 1
        2. Direct lookup: SUGGESTED_UNITS[base] has this unit → use that value
        3. Inverse lookup: SUGGESTED_UNITS[unit_name] has base → use 1/value
        4. Fall back to the picker's default_count
        """
        base = self.product.base_unit.lower()
        picked = unit_name.strip().lower()

        if picked == base:
            return 1.0

        # Direct: base unit's suggestions contain the picked unit
        for sname, sconv in SUGGESTED_UNITS.get(base, []):
            if sname.lower() == picked:
                return sconv

        # Inverse: picked unit's suggestions contain the base unit
        for sname, sconv in SUGGESTED_UNITS.get(picked, []):
            if sname.lower() == base:
                # sconv means "1 picked = sconv base" from picked's perspective
                # We need "1 picked = ? product_base"
                # Since picked is the base in that entry, sconv = how many picked per sname
                # So 1 unit_name = 1/sconv base_units
                return round(1.0 / sconv, 6) if sconv else fallback

        return fallback

    def _refresh_units(self):
        units = get_units_for_product(self.product.id)
        self.units_table.setRowCount(len(units))
        for row, u in enumerate(units):
            self.units_table.setItem(row, 0, QTableWidgetItem(u.unit_name))
            conv_display = f"{u.conversion_to_base:g}"
            self.units_table.setItem(row, 1, QTableWidgetItem(conv_display))
            for col in range(2):
                item = self.units_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)

            btn_del = QPushButton()
            btn_del.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
            btn_del.setObjectName("btn_danger")
            btn_del.setFixedSize(32, 26)
            btn_del.setToolTip("Remove unit")
            btn_del.clicked.connect(lambda _, uid=u.id: self._delete_unit(uid))
            self.units_table.setCellWidget(row, 2, btn_del)
            self.units_table.setRowHeight(row, 38)

    def _add_unit(self):
        name = self.new_unit_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Unit name is required.")
            return
        add_unit(
            self.product.id,
            name,
            self.new_conversion.value(),
        )
        self.new_unit_name.setText("")
        self.new_conversion.setValue(1)
        self._refresh_units()

    def _delete_unit(self, unit_id: int):
        reply = QMessageBox.question(
            self, "Remove Unit", "Remove this unit? Historical records are not affected.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            delete_unit(unit_id)
            self._refresh_units()
