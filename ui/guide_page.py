from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from ui.styles import COLORS


# ── Section content ──────────────────────────────────────────────────────────

_SECTIONS = [
    {
        "title": "Getting Started",
        "icon": "1",
        "body": (
            "Follow these steps to set up your inventory:\n\n"
            "1.  Add Products — Go to the Products page and create your items. "
            "Pick a base unit (e.g. piece, kg, litre) for each product.\n\n"
            "2.  Record Purchases — Every time you buy stock, go to Record Purchase "
            "and enter the items, quantities, and prices. Your inventory goes up.\n\n"
            "3.  Enter Daily Sales — At the end of each day, go to Enter Sales "
            "and log what you sold. Your inventory goes down.\n\n"
            "4.  View Reports — Check the Dashboard and Reports page to see "
            "revenue, profit, and stock levels at a glance."
        ),
        "diagram": "workflow",
    },
    {
        "title": "Products & Units",
        "icon": "2",
        "body": (
            "Each product has a base unit — the smallest unit you track "
            "(e.g. 'piece' for eggs, 'kg' for rice).\n\n"
            "You can add extra units with conversion factors. For example, "
            "if your base unit is 'piece', you can add:\n"
            "  - Dozen = 12 pieces\n"
            "  - Box = 24 pieces\n"
            "  - Carton = 48 pieces\n\n"
            "When recording purchases or sales you can pick any unit — "
            "the app converts everything to the base unit automatically.\n\n"
            "Set a Low Stock Threshold to get alerts when inventory drops "
            "below a certain level."
        ),
        "diagram": "units",
    },
    {
        "title": "Purchases",
        "icon": "3",
        "body": (
            "Use the Record Purchase page every time you buy stock from a supplier.\n\n"
            "  - Select the date, pick a product, choose a unit, and enter "
            "the quantity and price per unit.\n"
            "  - You can add multiple products in one purchase.\n"
            "  - After submitting, your inventory is updated instantly.\n\n"
            "You can delete a purchase from the history — this will "
            "subtract the quantities from your inventory."
        ),
    },
    {
        "title": "Sales",
        "icon": "4",
        "body": (
            "Use the Enter Sales page to record your daily sales.\n\n"
            "  - Pick each product, choose the selling unit, enter quantity sold "
            "and selling price per unit.\n"
            "  - Submit to deduct stock from inventory and record revenue.\n\n"
            "Tip: Enter sales at the end of each day for accurate daily reports."
        ),
    },
    {
        "title": "Inventory",
        "icon": "5",
        "body": (
            "The Inventory page shows the current stock for every product, "
            "displayed in the base unit.\n\n"
            "Stock goes UP when you record purchases and DOWN when you enter sales.\n\n"
            "Products with stock at or below the Low Stock Threshold appear "
            "as warnings on the Dashboard."
        ),
        "diagram": "inventory_flow",
    },
    {
        "title": "Reports",
        "icon": "6",
        "body": (
            "The Reports page provides insights into your business:\n\n"
            "  - Revenue & profit summaries by date range\n"
            "  - Profit per product (uses most recent purchase price as cost)\n"
            "  - Sales breakdown by product\n\n"
            "The Dashboard shows a quick snapshot: today's revenue, purchases, "
            "profit, inventory value, and low-stock alerts with charts."
        ),
    },
    {
        "title": "Backups",
        "icon": "7",
        "body": (
            "Your data is stored locally. Backups protect against data loss.\n\n"
            "Auto-Backups: The app automatically creates a backup every time "
            "it closes. The last 5 are kept in your data folder.\n\n"
            "Manual Backups: Go to Settings to create a backup .zip file "
            "you can save to USB, external drive, or anywhere safe.\n\n"
            "Restore: In Settings, you can restore from a backup file. "
            "This replaces all current data.\n\n"
            "Google Drive: If a credentials.json file is available, you can "
            "connect Google Drive in Settings for automatic cloud sync."
        ),
        "diagram": "backup",
    },
]


# ── Diagram builders ─────────────────────────────────────────────────────────

def _box(text: str, color: str, bg: str, min_w: int = 0) -> QFrame:
    """Create a styled rounded box with a label inside."""
    frame = QFrame()
    frame.setStyleSheet(
        f"QFrame {{ background: {bg}; border: 1px solid {color}; "
        f"border-radius: 6px; }}"
    )
    if min_w:
        frame.setMinimumWidth(min_w)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(12, 8, 12, 8)
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        f"color: {color}; font-size: 11px; font-weight: bold; "
        "background: transparent; border: none;"
    )
    lay.addWidget(lbl)
    return frame


def _arrow(text: str = "\u2192", vertical: bool = False) -> QLabel:
    """Create an arrow label between boxes."""
    symbol = "\u2193" if vertical else text
    lbl = QLabel(symbol)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"color: {COLORS['text_secondary']}; font-size: 16px; "
        "font-weight: bold; background: transparent;"
    )
    if not vertical:
        lbl.setFixedWidth(28)
    return lbl


def _caption(text: str) -> QLabel:
    """Small caption below a diagram."""
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"color: {COLORS['text_dimmed']}; font-size: 10px; "
        "background: transparent; font-style: italic;"
    )
    return lbl


def _diagram_container() -> tuple[QFrame, QVBoxLayout]:
    """Outer container for a diagram block with subtle background."""
    frame = QFrame()
    frame.setStyleSheet(
        f"QFrame {{ background: {COLORS['bg_deep']}; "
        f"border: 1px solid {COLORS['border']}; border-radius: 8px; }}"
    )
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(8)
    return frame, lay


def _build_workflow_diagram() -> QFrame:
    """Getting Started: 4-step workflow flow."""
    frame, lay = _diagram_container()

    title = QLabel("Your Daily Workflow")
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet(
        f"color: {COLORS['text_secondary']}; font-size: 11px; "
        "font-weight: bold; background: transparent; border: none;"
    )
    lay.addWidget(title)

    row = QHBoxLayout()
    row.setSpacing(0)
    row.addStretch()

    steps = [
        ("Add\nProducts", COLORS["accent_blue"], "#1a2a4a"),
        ("Record\nPurchases", COLORS["accent_teal"], "#0a2a25"),
        ("Enter\nSales", COLORS["accent_amber"], "#2a2200"),
        ("View\nReports", COLORS["accent_purple"], "#1f1a35"),
    ]
    for i, (text, color, bg) in enumerate(steps):
        row.addWidget(_box(text, color, bg, min_w=90))
        if i < len(steps) - 1:
            row.addWidget(_arrow())

    row.addStretch()
    lay.addLayout(row)
    lay.addWidget(_caption("Set up once, then repeat steps 2-3 daily"))
    return frame


def _build_units_diagram() -> QFrame:
    """Products & Units: conversion chain."""
    frame, lay = _diagram_container()

    title = QLabel("Unit Conversion Example  (Eggs)")
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet(
        f"color: {COLORS['text_secondary']}; font-size: 11px; "
        "font-weight: bold; background: transparent; border: none;"
    )
    lay.addWidget(title)

    row = QHBoxLayout()
    row.setSpacing(0)
    row.addStretch()

    units = [
        ("Carton\n48 pcs", COLORS["accent_purple"], "#1f1a35"),
        ("Box\n24 pcs", COLORS["accent_blue"], "#1a2a4a"),
        ("Dozen\n12 pcs", COLORS["accent_teal"], "#0a2a25"),
        ("Piece\n1 pc", COLORS["accent_amber"], "#2a2200"),
    ]
    for i, (text, color, bg) in enumerate(units):
        row.addWidget(_box(text, color, bg, min_w=80))
        if i < len(units) - 1:
            row.addWidget(_arrow("\u2192"))

    row.addStretch()
    lay.addLayout(row)

    # Base unit indicator
    base_lbl = QLabel("\u2190  All convert to base unit (piece)")
    base_lbl.setAlignment(Qt.AlignCenter)
    base_lbl.setStyleSheet(
        f"color: {COLORS['accent_amber']}; font-size: 10px; "
        "background: transparent; border: none;"
    )
    lay.addWidget(base_lbl)
    return frame


def _build_inventory_flow_diagram() -> QFrame:
    """Inventory: stock in/out flow."""
    frame, lay = _diagram_container()

    title = QLabel("How Stock Moves")
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet(
        f"color: {COLORS['text_secondary']}; font-size: 11px; "
        "font-weight: bold; background: transparent; border: none;"
    )
    lay.addWidget(title)

    row = QHBoxLayout()
    row.setSpacing(0)
    row.addStretch()

    # Purchase box
    row.addWidget(_box("Purchase\n(+Stock)", COLORS["accent_teal"], "#0a2a25", min_w=100))
    row.addWidget(_arrow("\u2192"))

    # Central inventory box — larger and prominent
    inv_frame = QFrame()
    inv_frame.setStyleSheet(
        f"QFrame {{ background: {COLORS['bg_elevated']}; "
        f"border: 2px solid {COLORS['accent_blue']}; border-radius: 8px; }}"
    )
    inv_frame.setMinimumWidth(130)
    inv_lay = QVBoxLayout(inv_frame)
    inv_lay.setContentsMargins(14, 10, 14, 10)
    inv_icon = QLabel("INVENTORY")
    inv_icon.setAlignment(Qt.AlignCenter)
    inv_icon.setStyleSheet(
        f"color: {COLORS['accent_blue']}; font-size: 13px; font-weight: bold; "
        "background: transparent; border: none;"
    )
    inv_lay.addWidget(inv_icon)
    inv_sub = QLabel("Current Stock\n(base units)")
    inv_sub.setAlignment(Qt.AlignCenter)
    inv_sub.setStyleSheet(
        f"color: {COLORS['text_secondary']}; font-size: 10px; "
        "background: transparent; border: none;"
    )
    inv_lay.addWidget(inv_sub)
    row.addWidget(inv_frame)

    row.addWidget(_arrow("\u2192"))

    # Sales box
    row.addWidget(_box("Sales\n(\u2212Stock)", COLORS["accent_red"], "#2a1215", min_w=100))

    row.addStretch()
    lay.addLayout(row)

    # Low-stock warning line
    warn = QLabel("\u26a0  Low stock threshold triggers Dashboard alerts")
    warn.setAlignment(Qt.AlignCenter)
    warn.setStyleSheet(
        f"color: {COLORS['accent_amber']}; font-size: 10px; "
        "background: transparent; border: none;"
    )
    lay.addWidget(warn)
    return frame


def _build_backup_diagram() -> QFrame:
    """Backups: backup strategy overview."""
    frame, lay = _diagram_container()

    title = QLabel("Backup Strategy")
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet(
        f"color: {COLORS['text_secondary']}; font-size: 11px; "
        "font-weight: bold; background: transparent; border: none;"
    )
    lay.addWidget(title)

    row = QHBoxLayout()
    row.setSpacing(12)
    row.addStretch()

    # Source
    row.addWidget(_box("Your\nDatabase", COLORS["accent_blue"], "#1a2a4a", min_w=85))
    row.addWidget(_arrow("\u2192"))

    # Three backup destinations in a vertical stack
    dest_frame = QFrame()
    dest_frame.setStyleSheet("background: transparent; border: none;")
    dest_lay = QVBoxLayout(dest_frame)
    dest_lay.setContentsMargins(0, 0, 0, 0)
    dest_lay.setSpacing(6)

    dest_lay.addWidget(_box("Auto-Backup  (on close, last 5 kept)", COLORS["accent_teal"], "#0a2a25"))
    dest_lay.addWidget(_box("Manual Backup  (export .zip anywhere)", COLORS["accent_amber"], "#2a2200"))
    dest_lay.addWidget(_box("Google Drive  (automatic cloud sync)", COLORS["accent_purple"], "#1f1a35"))

    row.addWidget(dest_frame)
    row.addStretch()
    lay.addLayout(row)

    lay.addWidget(_caption("Restore from any backup in Settings"))
    return frame


_DIAGRAM_BUILDERS = {
    "workflow": _build_workflow_diagram,
    "units": _build_units_diagram,
    "inventory_flow": _build_inventory_flow_diagram,
    "backup": _build_backup_diagram,
}


# ── Guide Page ───────────────────────────────────────────────────────────────

class GuidePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

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

        title = QLabel("User Guide")
        title.setObjectName("page_title")
        outer.addWidget(title)

        subtitle = QLabel(
            "Everything you need to know to manage your inventory effectively."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        outer.addWidget(subtitle)

        for section in _SECTIONS:
            card = self._make_section(
                section["title"],
                section["icon"],
                section["body"],
                section.get("diagram"),
            )
            outer.addWidget(card)

        outer.addStretch()

    def _make_section(self, title: str, number: str, body: str,
                      diagram_key: str | None = None) -> QFrame:
        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        header = QLabel(f"Step {number}  \u2014  {title}")
        header.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {COLORS['accent_blue']};"
        )
        layout.addWidget(header)

        # Diagram (before the text body so the visual context comes first)
        if diagram_key and diagram_key in _DIAGRAM_BUILDERS:
            diagram = _DIAGRAM_BUILDERS[diagram_key]()
            layout.addWidget(diagram)

        content = QLabel(body)
        content.setWordWrap(True)
        content.setTextFormat(Qt.PlainText)
        content.setStyleSheet(
            f"font-size: 12px; color: {COLORS['text_primary']}; line-height: 1.5;"
        )
        layout.addWidget(content)

        return card

    def refresh(self):
        """No-op — static content, but needed for page refresh protocol."""
        pass
