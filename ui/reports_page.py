from datetime import date, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit,
    QTabWidget, QFrame, QSizePolicy, QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from services.report_service import (
    get_daily_summary, get_profit_per_product,
    get_low_stock_items, get_purchase_history_summary,
    get_sales_by_date,
)
from services.export_service import (
    export_daily_summary, export_profit_per_product,
    export_low_stock, export_purchase_history,
)
from ui.styles import LOW_STOCK_ROW_COLOR, LOW_STOCK_TEXT_COLOR, COLORS


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Reports")
        title.setObjectName("page_title")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._build_daily_summary_tab(), "Daily Summary")
        tabs.addTab(self._build_profit_tab(), "Profit per Product")
        tabs.addTab(self._build_low_stock_tab(), "Low Stock")
        tabs.addTab(self._build_purchase_history_tab(), "Purchase History")
        layout.addWidget(tabs)

        self.refresh()

    # ── Daily Summary ──────────────────────────────────────────────────────
    def _build_daily_summary_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Date range selector
        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("From:"))
        self.ds_from = QDateEdit(QDate.currentDate().addDays(-6))
        self.ds_from.setCalendarPopup(True)
        self.ds_from.setDisplayFormat("dd-MM-yyyy")
        range_row.addWidget(self.ds_from)
        range_row.addWidget(QLabel("To:"))
        self.ds_to = QDateEdit(QDate.currentDate())
        self.ds_to.setCalendarPopup(True)
        self.ds_to.setDisplayFormat("dd-MM-yyyy")
        range_row.addWidget(self.ds_to)
        btn = QPushButton("Load")
        btn.clicked.connect(self._load_daily_summary)
        range_row.addWidget(btn)
        btn_export = QPushButton("Export CSV")
        btn_export.setObjectName("btn_secondary")
        btn_export.clicked.connect(self._export_daily_summary)
        range_row.addWidget(btn_export)
        range_row.addStretch()
        layout.addLayout(range_row)

        # Summary totals
        summary_row = QHBoxLayout()
        self.ds_revenue_lbl = self._make_stat_box("Total Revenue", "0", COLORS["accent_teal"])
        self.ds_cost_lbl = self._make_stat_box("Total Purchases", "0", COLORS["accent_blue"])
        self.ds_profit_lbl = self._make_stat_box("Gross Profit", "0", COLORS["accent_purple"])
        for box in [self.ds_revenue_lbl, self.ds_cost_lbl, self.ds_profit_lbl]:
            summary_row.addWidget(box)
        summary_row.addStretch()
        layout.addLayout(summary_row)

        # Day-by-day table
        self.daily_table = QTableWidget()
        self.daily_table.setColumnCount(3)
        self.daily_table.setHorizontalHeaderLabels(["Date", "Revenue", "Sale Batches"])
        self.daily_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.daily_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.daily_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.daily_table.verticalHeader().setVisible(False)
        self.daily_table.setAlternatingRowColors(True)
        layout.addWidget(self.daily_table)
        return w

    def _make_stat_box(self, label: str, value: str, color: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFixedWidth(180)
        frame.setFixedHeight(80)
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(12, 10, 12, 10)
        val = QLabel(value)
        val.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
        vl.addWidget(val)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        vl.addWidget(lbl)
        frame._val_label = val
        return frame

    def _load_daily_summary(self):
        date_from = self.ds_from.date().toString("yyyy-MM-dd")
        date_to = self.ds_to.date().toString("yyyy-MM-dd")
        summary = get_daily_summary(date_from, date_to)
        self.ds_revenue_lbl._val_label.setText(f"{summary['revenue']:,.0f}")
        self.ds_cost_lbl._val_label.setText(f"{summary['cost']:,.0f}")
        profit = summary["profit"]
        color = COLORS["accent_teal"] if profit >= 0 else COLORS["accent_red"]
        self.ds_profit_lbl._val_label.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {color};"
        )
        self.ds_profit_lbl._val_label.setText(f"{profit:,.0f}")

        rows = get_sales_by_date(date_from, date_to)
        self.daily_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.daily_table.setItem(i, 0, QTableWidgetItem(r["date"]))
            rev_item = QTableWidgetItem(f"{r['revenue']:,.0f}")
            rev_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.daily_table.setItem(i, 1, rev_item)
            self.daily_table.setItem(i, 2, QTableWidgetItem(str(r["batches"])))
            self.daily_table.setRowHeight(i, 38)

    # ── Profit per Product ─────────────────────────────────────────────────
    def _build_profit_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("From:"))
        self.pp_from = QDateEdit(QDate.currentDate().addDays(-29))
        self.pp_from.setCalendarPopup(True)
        self.pp_from.setDisplayFormat("dd-MM-yyyy")
        range_row.addWidget(self.pp_from)
        range_row.addWidget(QLabel("To:"))
        self.pp_to = QDateEdit(QDate.currentDate())
        self.pp_to.setCalendarPopup(True)
        self.pp_to.setDisplayFormat("dd-MM-yyyy")
        range_row.addWidget(self.pp_to)
        btn = QPushButton("Load")
        btn.clicked.connect(self._load_profit)
        range_row.addWidget(btn)
        btn_export = QPushButton("Export CSV")
        btn_export.setObjectName("btn_secondary")
        btn_export.clicked.connect(self._export_profit)
        range_row.addWidget(btn_export)
        range_row.addStretch()
        layout.addLayout(range_row)

        self._profit_note = QLabel(
            "Cost is estimated using the most recent purchase price for each product."
        )
        self._profit_note.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        layout.addWidget(self._profit_note)

        self.profit_table = QTableWidget()
        self.profit_table.setColumnCount(4)
        self.profit_table.setHorizontalHeaderLabels(
            ["Product", "Revenue", "Est. Cost", "Est. Profit"]
        )
        self.profit_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.profit_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.profit_table.verticalHeader().setVisible(False)
        self.profit_table.setAlternatingRowColors(True)
        layout.addWidget(self.profit_table)
        return w

    def _load_profit(self):
        self._profit_note.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        date_from = self.pp_from.date().toString("yyyy-MM-dd")
        date_to = self.pp_to.date().toString("yyyy-MM-dd")
        rows = get_profit_per_product(date_from, date_to)
        self.profit_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.profit_table.setItem(i, 0, QTableWidgetItem(r["product_name"]))
            rev_item = QTableWidgetItem(f"{r['revenue']:,.0f}")
            rev_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            cost_item = QTableWidgetItem(f"{r['estimated_cost']:,.0f}")
            cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            profit_item = QTableWidgetItem(f"{r['profit']:,.0f}")
            profit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if r["profit"] < 0:
                profit_item.setForeground(QColor(COLORS["accent_red"]))
            else:
                profit_item.setForeground(QColor(COLORS["accent_teal"]))
            self.profit_table.setItem(i, 1, rev_item)
            self.profit_table.setItem(i, 2, cost_item)
            self.profit_table.setItem(i, 3, profit_item)
            self.profit_table.setRowHeight(i, 38)

    # ── Low Stock ──────────────────────────────────────────────────────────
    def _build_low_stock_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("Products at or below their low-stock threshold:"))
        hdr.addStretch()
        btn_export = QPushButton("Export CSV")
        btn_export.setObjectName("btn_secondary")
        btn_export.clicked.connect(self._export_low_stock)
        hdr.addWidget(btn_export)
        btn = QPushButton("Refresh")
        btn.setObjectName("btn_secondary")
        btn.clicked.connect(self._load_low_stock)
        hdr.addWidget(btn)
        layout.addLayout(hdr)

        self.low_table = QTableWidget()
        self.low_table.setColumnCount(4)
        self.low_table.setHorizontalHeaderLabels(
            ["Product", "Category", "In Stock", "Threshold (base units)"]
        )
        self.low_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.low_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.low_table.verticalHeader().setVisible(False)
        self.low_table.setAlternatingRowColors(True)
        layout.addWidget(self.low_table)
        return w

    def _load_low_stock(self):
        items = get_low_stock_items()
        self.low_table.setRowCount(len(items))
        for i, item in enumerate(items):
            self.low_table.setItem(i, 0, QTableWidgetItem(item["name"]))
            self.low_table.setItem(i, 1, QTableWidgetItem(item["category"] or ""))
            qty_str = f"{item['display_qty']:,.0f}"
            self.low_table.setItem(
                i, 2, QTableWidgetItem(f"{qty_str} {item['display_unit']}")
            )
            self.low_table.setItem(
                i, 3, QTableWidgetItem(f"{item['low_stock_threshold']:,.0f}")
            )
            bg = QColor(LOW_STOCK_ROW_COLOR)
            for col in range(4):
                cell = self.low_table.item(i, col)
                if cell:
                    cell.setBackground(bg)
            self.low_table.setRowHeight(i, 38)

    # ── Purchase History ───────────────────────────────────────────────────
    def _build_purchase_history_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("Last 50 purchase sessions:"))
        hdr.addStretch()
        btn_export = QPushButton("Export CSV")
        btn_export.setObjectName("btn_secondary")
        btn_export.clicked.connect(self._export_purchase_history)
        hdr.addWidget(btn_export)
        btn = QPushButton("Refresh")
        btn.setObjectName("btn_secondary")
        btn.clicked.connect(self._load_purchase_history)
        hdr.addWidget(btn)
        layout.addLayout(hdr)

        self.purchase_hist_table = QTableWidget()
        self.purchase_hist_table.setColumnCount(4)
        self.purchase_hist_table.setHorizontalHeaderLabels(
            ["Date", "Items", "Total Spent", "Notes"]
        )
        self.purchase_hist_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.purchase_hist_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.purchase_hist_table.verticalHeader().setVisible(False)
        self.purchase_hist_table.setAlternatingRowColors(True)
        layout.addWidget(self.purchase_hist_table)
        return w

    def _load_purchase_history(self):
        rows = get_purchase_history_summary(limit=50)
        self.purchase_hist_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.purchase_hist_table.setItem(i, 0, QTableWidgetItem(r["date"]))
            self.purchase_hist_table.setItem(i, 1, QTableWidgetItem(str(r["item_count"])))
            total_item = QTableWidgetItem(f"{r['total']:,.0f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.purchase_hist_table.setItem(i, 2, total_item)
            self.purchase_hist_table.setItem(i, 3, QTableWidgetItem(r["notes"]))
            self.purchase_hist_table.setRowHeight(i, 38)

    # ── CSV Exports ──────────────────────────────────────────────────────────
    def _save_csv(self, default_name: str, export_fn, *args):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", default_name, "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            result = export_fn(path, *args)
            QMessageBox.information(self, "Export Complete", f"Saved to:\n{result}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))

    def _export_daily_summary(self):
        d_from = self.ds_from.date().toString("yyyy-MM-dd")
        d_to = self.ds_to.date().toString("yyyy-MM-dd")
        self._save_csv("daily_summary.csv", export_daily_summary, d_from, d_to)

    def _export_profit(self):
        d_from = self.pp_from.date().toString("yyyy-MM-dd")
        d_to = self.pp_to.date().toString("yyyy-MM-dd")
        self._save_csv("profit_per_product.csv", export_profit_per_product, d_from, d_to)

    def _export_low_stock(self):
        self._save_csv("low_stock.csv", export_low_stock)

    def _export_purchase_history(self):
        self._save_csv("purchase_history.csv", export_purchase_history)

    # ── Refresh all tabs ───────────────────────────────────────────────────
    def refresh(self):
        self._load_daily_summary()
        self._load_profit()
        self._load_low_stock()
        self._load_purchase_history()
