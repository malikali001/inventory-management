from datetime import date, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from services.report_service import (
    get_daily_summary, get_low_stock_items, get_sales_by_date, get_profit_per_product,
)
from services.inventory_service import get_total_inventory_value
from ui.styles import LOW_STOCK_ROW_COLOR, LOW_STOCK_TEXT_COLOR, COLORS


class StatCard(QFrame):
    """Fintech-style stat card with colored left-border accent strip."""
    def __init__(self, label: str, value: str, accent_color: str = "#4F8EF7",
                 icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(110)
        self._accent = accent_color

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        strip = QFrame()
        strip.setFixedWidth(4)
        strip.setStyleSheet(f"background-color: {accent_color}; border-radius: 10px 0 0 10px;")
        outer.addWidget(strip)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(14, 12, 14, 10)
        cl.setSpacing(2)
        outer.addWidget(content)

        top = QHBoxLayout()
        top.setSpacing(0)
        self.val_label = QLabel(value)
        self.val_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {accent_color};")
        top.addWidget(self.val_label)
        top.addStretch()
        if icon:
            ic = QLabel(icon)
            ic.setStyleSheet(f"font-size: 18px; color: {accent_color}; opacity: 0.6;")
            ic.setAlignment(Qt.AlignRight | Qt.AlignTop)
            top.addWidget(ic)
        cl.addLayout(top)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        cl.addWidget(lbl)
        cl.addStretch()

    def update_value(self, value: str):
        self.val_label.setText(value)

    def set_color(self, color: str):
        self.val_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")


def _chart_colors():
    """Return theme-aware matplotlib styling."""
    return {
        "bg": COLORS["bg_surface"],
        "fg": COLORS["text_primary"],
        "grid": COLORS["border"],
        "fg_secondary": COLORS["text_secondary"],
    }


class _ChartCard(QFrame):
    """Card wrapper around a matplotlib FigureCanvas."""
    def __init__(self, title: str, fig_w: float = 4.5, fig_h: float = 2.8, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 10)
        layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {COLORS['text_primary']};"
        )
        layout.addWidget(self.title_label)

        cc = _chart_colors()
        self.figure = Figure(figsize=(fig_w, fig_h), dpi=100)
        self.figure.patch.set_facecolor(cc["bg"])
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: transparent;")
        self.canvas.setFixedHeight(int(fig_h * 100))
        layout.addWidget(self.canvas)

    def clear(self):
        self.figure.clear()

    def draw(self):
        self.canvas.draw_idle()

    def update_theme(self):
        cc = _chart_colors()
        self.figure.patch.set_facecolor(cc["bg"])
        self.title_label.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {COLORS['text_primary']};"
        )


class DashboardPage(QWidget):
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
        outer.setSpacing(16)

        # ── Header ─────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()
        self.date_label = QLabel()
        header.addWidget(self.date_label)
        outer.addLayout(header)

        # ── Stat cards row ─────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self.card_revenue = StatCard("Today's Revenue", "0",
                                     accent_color=COLORS["accent_teal"], icon="↑")
        self.card_cost = StatCard("Today's Purchases", "0",
                                  accent_color=COLORS["accent_blue"], icon="↓")
        self.card_profit = StatCard("Today's Gross Profit", "0",
                                    accent_color=COLORS["accent_purple"], icon="◈")
        self.card_inventory_val = StatCard("Inventory Value", "0",
                                           accent_color=COLORS["accent_amber"], icon="◆")
        self.card_lowstock = StatCard("Low Stock", "0",
                                      accent_color=COLORS["accent_red"], icon="⚠")
        for card in [self.card_revenue, self.card_cost, self.card_profit,
                     self.card_inventory_val, self.card_lowstock]:
            cards_row.addWidget(card)
        outer.addLayout(cards_row)

        # ── Charts row 1: Revenue trend + Top products ─────────────────
        charts_row1 = QHBoxLayout()
        charts_row1.setSpacing(14)

        self.chart_revenue = _ChartCard("Revenue — Last 7 Days", fig_w=5, fig_h=2.6)
        charts_row1.addWidget(self.chart_revenue, stretch=3)

        self.chart_products = _ChartCard("Top Products by Profit", fig_w=4, fig_h=2.6)
        charts_row1.addWidget(self.chart_products, stretch=2)

        outer.addLayout(charts_row1)

        # ── Charts row 2: Inventory donut + Stock levels ───────────────
        charts_row2 = QHBoxLayout()
        charts_row2.setSpacing(14)

        self.chart_inventory = _ChartCard("Inventory Value Breakdown", fig_w=3.5, fig_h=2.6)
        charts_row2.addWidget(self.chart_inventory, stretch=2)

        # Stock level progress bars in a card
        self.stock_card = QFrame()
        self.stock_card.setObjectName("card")
        self.stock_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        stock_layout = QVBoxLayout(self.stock_card)
        stock_layout.setContentsMargins(16, 14, 16, 10)
        stock_layout.setSpacing(8)
        self.stock_title = QLabel("Stock Levels")
        self.stock_title.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {COLORS['text_primary']};"
        )
        stock_layout.addWidget(self.stock_title)
        self.stock_bars_layout = QVBoxLayout()
        self.stock_bars_layout.setSpacing(6)
        stock_layout.addLayout(self.stock_bars_layout)
        stock_layout.addStretch()
        charts_row2.addWidget(self.stock_card, stretch=3)

        outer.addLayout(charts_row2)

        # ── Quick actions ──────────────────────────────────────────────
        self.actions_label = QLabel("Quick Actions")
        outer.addWidget(self.actions_label)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(12)
        btn_sales = QPushButton("↑  Enter Today's Sales")
        btn_sales.setObjectName("btn_success")
        btn_sales.setFixedHeight(42)
        btn_sales.clicked.connect(lambda: self._main_window.navigate_to_sales())
        actions_row.addWidget(btn_sales)

        btn_purchase = QPushButton("↓  Record a Purchase")
        btn_purchase.setFixedHeight(42)
        btn_purchase.clicked.connect(lambda: self._main_window.navigate_to_purchase())
        actions_row.addWidget(btn_purchase)
        actions_row.addStretch()
        outer.addLayout(actions_row)

        # ── Low stock table ────────────────────────────────────────────
        self.low_label = QLabel("⚠  Low Stock Alerts")
        outer.addWidget(self.low_label)

        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(4)
        self.low_stock_table.setHorizontalHeaderLabels(
            ["Product", "Category", "In Stock", "Threshold"]
        )
        self.low_stock_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.low_stock_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.low_stock_table.verticalHeader().setVisible(False)
        self.low_stock_table.setAlternatingRowColors(True)
        outer.addWidget(self.low_stock_table)

        outer.addStretch()
        self.refresh()

    # ── Styling ────────────────────────────────────────────────────────

    def _apply_styles(self):
        self.date_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px;"
        )
        self.actions_label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {COLORS['text_primary']};"
        )
        self.low_label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {COLORS['accent_amber']};"
        )
        self.stock_title.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {COLORS['text_primary']};"
        )

    # ── Chart rendering ───────────────────────────────────────────────

    def _draw_revenue_chart(self):
        """Area line chart: last 7 days revenue."""
        cc = _chart_colors()
        self.chart_revenue.clear()
        self.chart_revenue.update_theme()

        today = date.today()
        start = today - timedelta(days=6)
        data = get_sales_by_date(start.isoformat(), today.isoformat())
        data_map = {d["date"]: d["revenue"] for d in data}

        dates = [(start + timedelta(days=i)) for i in range(7)]
        labels = [d.strftime("%d %b") for d in dates]
        values = [data_map.get(d.isoformat(), 0) for d in dates]

        ax = self.chart_revenue.figure.add_subplot(111)
        ax.set_facecolor(cc["bg"])

        ax.fill_between(range(7), values, alpha=0.15, color=COLORS["accent_teal"])
        ax.plot(range(7), values, color=COLORS["accent_teal"], linewidth=2.5,
                marker="o", markersize=5, markerfacecolor=COLORS["accent_teal"])

        ax.set_xticks(range(7))
        ax.set_xticklabels(labels, fontsize=8, color=cc["fg_secondary"])
        ax.tick_params(axis="y", labelsize=8, labelcolor=cc["fg_secondary"])
        ax.grid(True, axis="y", alpha=0.3, color=cc["grid"], linestyle="--")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(cc["grid"])
        ax.spines["bottom"].set_color(cc["grid"])
        self.chart_revenue.figure.tight_layout(pad=1.0)
        self.chart_revenue.draw()

    def _draw_products_chart(self):
        """Horizontal bar chart: top 5 products by profit (last 30 days)."""
        cc = _chart_colors()
        self.chart_products.clear()
        self.chart_products.update_theme()

        today = date.today()
        start = today - timedelta(days=29)
        data = get_profit_per_product(start.isoformat(), today.isoformat())[:5]

        ax = self.chart_products.figure.add_subplot(111)
        ax.set_facecolor(cc["bg"])

        if not data:
            ax.text(0.5, 0.5, "No sales data yet", ha="center", va="center",
                    fontsize=11, color=cc["fg_secondary"], transform=ax.transAxes)
            self.chart_products.figure.tight_layout(pad=1.0)
            self.chart_products.draw()
            return

        data.reverse()  # bottom-to-top for horizontal bars
        names = [d["product_name"][:15] for d in data]
        profits = [d["profit"] for d in data]
        colors = [COLORS["accent_teal"] if p >= 0 else COLORS["accent_red"] for p in profits]

        bars = ax.barh(range(len(data)), profits, color=colors, height=0.6, edgecolor="none")
        ax.set_yticks(range(len(data)))
        ax.set_yticklabels(names, fontsize=8, color=cc["fg_secondary"])
        ax.tick_params(axis="x", labelsize=8, labelcolor=cc["fg_secondary"])
        ax.grid(True, axis="x", alpha=0.3, color=cc["grid"], linestyle="--")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(cc["grid"])
        ax.spines["bottom"].set_color(cc["grid"])

        # Value labels
        max_abs = max((abs(v) for v in profits), default=1)
        for bar, val in zip(bars, profits):
            offset = max_abs * 0.03
            x = bar.get_width() + offset if val >= 0 else bar.get_width() - offset
            ax.text(x, bar.get_y() + bar.get_height() / 2,
                    f"{val:,.0f}", va="center", fontsize=7, color=cc["fg_secondary"])

        self.chart_products.figure.tight_layout(pad=1.0)
        self.chart_products.draw()

    def _draw_inventory_donut(self):
        """Donut chart: inventory value by product (top 5 + others)."""
        cc = _chart_colors()
        self.chart_inventory.clear()
        self.chart_inventory.update_theme()

        inv = get_total_inventory_value()
        items = [i for i in inv["items"] if i["value"] > 0]

        ax = self.chart_inventory.figure.add_subplot(111)
        ax.set_facecolor(cc["bg"])

        if not items:
            ax.text(0.5, 0.5, "No inventory data", ha="center", va="center",
                    fontsize=11, color=cc["fg_secondary"], transform=ax.transAxes)
            self.chart_inventory.figure.tight_layout(pad=1.0)
            self.chart_inventory.draw()
            return

        top = items[:5]
        others_val = sum(i["value"] for i in items[5:])

        labels = [i["name"][:12] for i in top]
        sizes = [i["value"] for i in top]
        if others_val > 0:
            labels.append("Others")
            sizes.append(others_val)

        palette = [
            COLORS["accent_teal"], COLORS["accent_blue"], COLORS["accent_purple"],
            COLORS["accent_amber"], COLORS["accent_red"], COLORS["text_dimmed"],
        ]
        colors = palette[:len(sizes)]

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct="%1.0f%%", startangle=90,
            colors=colors, pctdistance=0.78,
            wedgeprops={"width": 0.45, "edgecolor": cc["bg"], "linewidth": 2},
            textprops={"fontsize": 7, "color": cc["fg_secondary"]},
        )
        for at in autotexts:
            at.set_fontsize(7)
            at.set_color(cc["fg"])

        # Center label: total value
        ax.text(0, 0, f"{inv['total_value']:,.0f}", ha="center", va="center",
                fontsize=11, fontweight="bold", color=cc["fg"])

        self.chart_inventory.figure.tight_layout(pad=0.5)
        self.chart_inventory.draw()

    def _draw_stock_levels(self):
        """Progress bars showing stock level vs threshold."""
        # Clear existing bars
        while self.stock_bars_layout.count():
            child = self.stock_bars_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        low_stock = get_low_stock_items()

        if not low_stock:
            lbl = QLabel("All items well stocked")
            lbl.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 12px; padding: 20px 0;")
            lbl.setAlignment(Qt.AlignCenter)
            self.stock_bars_layout.addWidget(lbl)
            return

        for item in low_stock[:8]:
            threshold = item["low_stock_threshold"]
            qty = item["quantity_base"]
            pct = int((qty / threshold * 100)) if threshold > 0 else 0
            pct = min(pct, 100)

            row = QWidget()
            rl = QVBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(2)

            top = QHBoxLayout()
            name_lbl = QLabel(item["name"])
            name_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 11px;")
            top.addWidget(name_lbl)
            top.addStretch()
            pct_color = COLORS["accent_red"] if pct <= 30 else (
                COLORS["accent_amber"] if pct <= 70 else COLORS["accent_teal"]
            )
            pct_lbl = QLabel(f"{pct}%")
            pct_lbl.setStyleSheet(f"color: {pct_color}; font-size: 11px; font-weight: bold;")
            top.addWidget(pct_lbl)
            rl.addLayout(top)

            bar = QProgressBar()
            bar.setValue(pct)
            bar.setTextVisible(False)
            bar.setFixedHeight(6)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {COLORS['bg_elevated']};
                    border: none;
                    border-radius: 3px;
                }}
                QProgressBar::chunk {{
                    background-color: {pct_color};
                    border-radius: 3px;
                }}
            """)
            rl.addWidget(bar)
            self.stock_bars_layout.addWidget(row)

    # ── Refresh ────────────────────────────────────────────────────────

    def refresh(self):
        self._apply_styles()
        today = date.today()
        self.date_label.setText(f"Today: {today.strftime('%d %B %Y')}")

        # Stat cards
        summary = get_daily_summary(today.isoformat(), today.isoformat())
        self.card_revenue.update_value(f"{summary['revenue']:,.0f}")
        self.card_cost.update_value(f"{summary['cost']:,.0f}")

        profit = summary["profit"]
        profit_color = COLORS["accent_teal"] if profit >= 0 else COLORS["accent_red"]
        self.card_profit.set_color(profit_color)
        self.card_profit.update_value(f"{profit:,.0f}")

        inv_val = get_total_inventory_value()
        self.card_inventory_val.update_value(f"{inv_val['total_value']:,.0f}")

        low_stock = get_low_stock_items()
        self.card_lowstock.update_value(str(len(low_stock)))

        # Charts
        self._draw_revenue_chart()
        self._draw_products_chart()
        self._draw_inventory_donut()
        self._draw_stock_levels()

        # Low stock table
        self.low_stock_table.setRowCount(len(low_stock))
        for row, item in enumerate(low_stock):
            self.low_stock_table.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.low_stock_table.setItem(row, 1, QTableWidgetItem(item["category"] or ""))
            qty_str = f"{item['display_qty']:,.0f}"
            self.low_stock_table.setItem(
                row, 2, QTableWidgetItem(f"{qty_str} {item['display_unit']}")
            )
            self.low_stock_table.setItem(
                row, 3, QTableWidgetItem(f"{item['low_stock_threshold']:,.0f}")
            )
            bg = QColor(LOW_STOCK_ROW_COLOR)
            fg = QColor(LOW_STOCK_TEXT_COLOR)
            for col in range(4):
                cell = self.low_stock_table.item(row, col)
                if cell:
                    cell.setBackground(bg)
                    cell.setForeground(fg)
            self.low_stock_table.setRowHeight(row, 38)

        if not low_stock:
            self.low_stock_table.setRowCount(1)
            ok_item = QTableWidgetItem("  All items are well stocked.")
            ok_item.setForeground(QColor(COLORS["accent_teal"]))
            self.low_stock_table.setItem(0, 0, ok_item)
            self.low_stock_table.setSpan(0, 0, 1, 4)

        # Resize table to fit rows
        header_h = self.low_stock_table.horizontalHeader().height()
        rows_h = sum(self.low_stock_table.rowHeight(r) for r in range(self.low_stock_table.rowCount()))
        self.low_stock_table.setFixedHeight(header_h + rows_h + 4)
