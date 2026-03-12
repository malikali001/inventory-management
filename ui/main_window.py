from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
)
from PySide6.QtCore import Qt

from ui.styles import APP_STYLE, COLORS
from ui.dashboard import DashboardPage
from ui.products_page import ProductsPage
from ui.purchase_page import PurchasePage
from ui.sales_page import SalesPage
from ui.inventory_page import InventoryPage
from ui.reports_page import ReportsPage
from ui.settings_page import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventory Manager")
        self.resize(1200, 750)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(APP_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = self._build_sidebar()
        layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("content_area")
        layout.addWidget(self.stack)

        self.dashboard_page = DashboardPage(self)
        self.products_page = ProductsPage(self)
        self.purchase_page = PurchasePage(self)
        self.sales_page = SalesPage(self)
        self.inventory_page = InventoryPage(self)
        self.reports_page = ReportsPage(self)
        self.settings_page = SettingsPage(self)

        for page in [
            self.dashboard_page, self.products_page, self.purchase_page,
            self.sales_page, self.inventory_page, self.reports_page,
            self.settings_page,
        ]:
            self.stack.addWidget(page)

        self._nav_buttons: list[QPushButton] = []

        for btn, idx in zip(self._raw_nav_buttons, range(7)):
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            self._nav_buttons.append(btn)

        self._switch_page(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(215)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App title block
        self._title_widget = QWidget()
        self._title_widget.setObjectName("sidebar_title")
        title_layout = QHBoxLayout(self._title_widget)
        title_layout.setContentsMargins(16, 18, 16, 18)
        title_layout.setSpacing(10)

        # Colored accent square
        self._accent_block = QLabel("■")
        title_layout.addWidget(self._accent_block)

        self._title_text = QLabel("Inventory\nManager")
        self._title_text.setObjectName("app_title")
        title_layout.addWidget(self._title_text)
        title_layout.addStretch()
        layout.addWidget(self._title_widget)

        self._apply_sidebar_title_styles()

        # Spacing before nav
        spacer = QWidget()
        spacer.setFixedHeight(8)
        spacer.setStyleSheet("background: transparent;")
        layout.addWidget(spacer)

        # Nav items with icons
        nav_items = [
            ("⊞  Dashboard",       "dashboard"),
            ("◫  Products",         "products"),
            ("↓  Record Purchase",  "purchase"),
            ("↑  Enter Sales",      "sales"),
            ("◉  Inventory",        "inventory"),
            ("▦  Reports",          "reports"),
            ("⚙  Settings",         "settings"),
        ]

        self._raw_nav_buttons = []
        for label, _ in nav_items:
            btn = QPushButton(f"  {label}")
            btn.setCheckable(False)
            btn.setProperty("active", "false")
            btn.setFixedHeight(44)
            self._raw_nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Bottom version chip
        self._version_widget = QWidget()
        vl = QHBoxLayout(self._version_widget)
        vl.setContentsMargins(16, 10, 16, 12)
        self._version_lbl = QLabel("v1.0")
        vl.addWidget(self._version_lbl)
        vl.addStretch()
        layout.addWidget(self._version_widget)

        self._apply_sidebar_version_styles()

        return sidebar

    def _switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)

        for i, btn in enumerate(self._raw_nav_buttons):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        page = self.stack.currentWidget()
        if hasattr(page, "refresh"):
            page.refresh()

    def navigate_to_sales(self):
        self._switch_page(3)

    def navigate_to_purchase(self):
        self._switch_page(2)

    def navigate_to_dashboard(self):
        self._switch_page(0)

    def _apply_sidebar_title_styles(self):
        """Apply current theme colors to sidebar title block."""
        self._title_widget.setStyleSheet(
            f"background-color: {COLORS['bg_sidebar']};"
            f"border-bottom: 1px solid {COLORS['border']};"
        )
        self._accent_block.setStyleSheet(
            f"color: {COLORS['accent_blue']}; font-size: 22px; background: transparent;"
        )
        self._title_text.setStyleSheet(
            "color: #E8EAF0; font-size: 13px; "
            "font-weight: bold; background: transparent; padding: 0;"
        )

    def _apply_sidebar_version_styles(self):
        """Apply current theme colors to sidebar version chip."""
        self._version_widget.setStyleSheet(
            f"border-top: 1px solid {COLORS['border']}; background: transparent;"
        )
        self._version_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 11px; background: transparent;"
        )

    def apply_theme(self, qss: str):
        """Re-apply stylesheet and rebuild dynamic sidebar colors."""
        self.setStyleSheet(qss)
        self._apply_sidebar_title_styles()
        self._apply_sidebar_version_styles()
        # Refresh all pages to update inline styles
        for i in range(self.stack.count()):
            page = self.stack.widget(i)
            if hasattr(page, "refresh"):
                page.refresh()
