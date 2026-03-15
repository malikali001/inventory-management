import sys

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QDialog, QMessageBox,
)
from PySide6.QtCore import Qt

from ui.styles import APP_STYLE, COLORS
from ui.dashboard import DashboardPage
from ui.products_page import ProductsPage
from ui.purchase_page import PurchasePage
from ui.sales_page import SalesPage
from ui.inventory_page import InventoryPage
from ui.reports_page import ReportsPage
from ui.guide_page import GuidePage
from ui.settings_page import SettingsPage
from version import __version__


class MainWindow(QMainWindow):
    def __init__(self, is_fresh: bool = False):
        super().__init__()
        self._is_fresh = is_fresh
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
        self.guide_page = GuidePage(self)
        self.settings_page = SettingsPage(self)

        for page in [
            self.dashboard_page, self.products_page, self.purchase_page,
            self.sales_page, self.inventory_page, self.reports_page,
            self.guide_page, self.settings_page,
        ]:
            self.stack.addWidget(page)

        self._nav_buttons: list[QPushButton] = []

        for btn, idx in zip(self._raw_nav_buttons, range(len(self._raw_nav_buttons))):
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            self._nav_buttons.append(btn)

        self._switch_page(0)

    def show(self):
        super().show()
        if self._is_fresh:
            self._show_onboarding()

    def _show_onboarding(self):
        """Show welcome dialog on first launch."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Welcome")
        dlg.setMinimumWidth(440)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Welcome to Inventory Manager!")
        title.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {COLORS['accent_blue']};"
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        msg = QLabel(
            "Here's how to get started:\n\n"
            "1.  Add your products (name, unit, category)\n"
            "2.  Record purchases when you buy stock\n"
            "3.  Enter daily sales at the end of each day\n"
            "4.  Check the Dashboard for insights and reports"
        )
        msg.setWordWrap(True)
        msg.setStyleSheet(f"font-size: 13px; color: {COLORS['text_primary']};")
        layout.addWidget(msg)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_guide = QPushButton("View User Guide")
        btn_guide.setObjectName("btn_secondary")
        btn_guide.setFixedHeight(40)
        btn_guide.clicked.connect(lambda: (dlg.accept(), self._switch_page(6)))
        btn_row.addWidget(btn_guide)

        btn_product = QPushButton("Add First Product")
        btn_product.setObjectName("btn_success")
        btn_product.setFixedHeight(40)
        btn_product.clicked.connect(lambda: (dlg.accept(), self._switch_page(1)))
        btn_row.addWidget(btn_product)

        layout.addLayout(btn_row)
        dlg.exec()

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
            ("?  User Guide",       "guide"),
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

        # Bottom version chip (clickable → About)
        self._version_widget = QWidget()
        vl = QHBoxLayout(self._version_widget)
        vl.setContentsMargins(16, 10, 16, 12)
        self._version_lbl = QPushButton(f"v{__version__}")
        self._version_lbl.setFlat(True)
        self._version_lbl.setCursor(Qt.PointingHandCursor)
        self._version_lbl.setToolTip("About Inventory Manager")
        self._version_lbl.clicked.connect(self._show_about)
        vl.addWidget(self._version_lbl)
        vl.addStretch()
        layout.addWidget(self._version_widget)

        self._apply_sidebar_version_styles()

        return sidebar

    def _show_about(self):
        from database.connection import get_db_path
        import PySide6

        QMessageBox.about(
            self,
            "About Inventory Manager",
            f"<h3>Inventory Manager</h3>"
            f"<p>Version <b>{__version__}</b></p>"
            f"<p>Python {sys.version.split()[0]}<br>"
            f"PySide6 {PySide6.__version__}</p>"
            f"<p><small>Database: {get_db_path()}</small></p>",
        )

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

    def navigate_to_guide(self):
        self._switch_page(6)

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
            "color: #94A3B8; font-size: 11px; background: transparent; "
            "border: none; text-align: left; padding: 0;"
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
