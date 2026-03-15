# ── Theme Definitions ──────────────────────────────────────────────────────────

_DARK = {
    "bg_deep":        "#0D0F18",
    "bg_surface":     "#151823",
    "bg_elevated":    "#1C2033",
    "bg_hover":       "#232740",
    "bg_sidebar":     "#10131E",
    "bg_active":      "#1C2540",
    "accent_blue":    "#4F8EF7",
    "accent_teal":    "#00D4AA",
    "accent_red":     "#F7525F",
    "accent_amber":   "#F7B731",
    "accent_purple":  "#9D79F2",
    "text_primary":   "#E8EAF0",
    "text_secondary": "#8892A4",
    "text_dimmed":    "#4A4F6A",
    "border":         "#2A2D40",
    "low_stock_bg":   "#2A1F00",
    "low_stock_fg":   "#F7B731",
    "alt_row":        "#1A1D2E",
    "hover_row":      "#1E2540",
    "btn_danger_bg":  "#3D1A1D",
    "btn_danger_border": "#5A2228",
    "spin_btn":       "#232740",
    "spin_btn_hover": "#2A3050",
}

_LIGHT = {
    "bg_deep":        "#F0F2F5",
    "bg_surface":     "#FFFFFF",
    "bg_elevated":    "#EDF0F4",
    "bg_hover":       "#E8ECF1",
    "bg_sidebar":     "#1E2A3A",
    "bg_active":      "#DBEAFE",
    "accent_blue":    "#2563EB",
    "accent_teal":    "#059669",
    "accent_red":     "#DC2626",
    "accent_amber":   "#D97706",
    "accent_purple":  "#7C3AED",
    "text_primary":   "#1F2937",
    "text_secondary": "#6B7280",
    "text_dimmed":    "#9CA3AF",
    "border":         "#D1D5DB",
    "low_stock_bg":   "#FEF3C7",
    "low_stock_fg":   "#92400E",
    "alt_row":        "#F9FAFB",
    "hover_row":      "#EEF2FF",
    "btn_danger_bg":  "#FEE2E2",
    "btn_danger_border": "#FECACA",
    "spin_btn":       "#D1D5DB",
    "spin_btn_hover": "#9CA3AF",
}

# ── Active theme state ─────────────────────────────────────────────────────────

_current_theme = "dark"

# Mutable dict — updated in-place so all imports see changes
COLORS = dict(_DARK)

LOW_STOCK_ROW_COLOR  = _DARK["low_stock_bg"]
LOW_STOCK_TEXT_COLOR = _DARK["low_stock_fg"]


def get_current_theme() -> str:
    return _current_theme


def set_theme(theme: str) -> str:
    """Switch theme ('dark' or 'light'). Returns the new QSS string."""
    global _current_theme, LOW_STOCK_ROW_COLOR, LOW_STOCK_TEXT_COLOR
    _current_theme = theme
    src = _DARK if theme == "dark" else _LIGHT
    COLORS.clear()
    COLORS.update(src)
    LOW_STOCK_ROW_COLOR = src["low_stock_bg"]
    LOW_STOCK_TEXT_COLOR = src["low_stock_fg"]
    return _build_style(src)


def _build_style(c: dict) -> str:
    """Generate full QSS from a color dict."""
    # Sidebar text colors depend on theme
    is_dark = c is _DARK or c["bg_deep"] == _DARK["bg_deep"]
    sidebar_text = "#8892A4" if is_dark else "#94A3B8"
    sidebar_text_hover = "#E8EAF0" if is_dark else "#FFFFFF"
    sidebar_active_text = c["accent_blue"] if is_dark else "#FFFFFF"
    sidebar_active_bg = c["bg_active"] if is_dark else "#253550"
    btn_success_text = "#0D1A15" if is_dark else "#FFFFFF"
    selection_text = c["text_primary"]

    return f"""
/* ── Base ─────────────────────────────────────────────────────────────────── */
QMainWindow, QWidget {{
    background-color: {c["bg_deep"]};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: {c["text_primary"]};
}}

QDialog {{
    background-color: {c["bg_surface"]};
    color: {c["text_primary"]};
}}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
#sidebar {{
    background-color: {c["bg_sidebar"]};
    border-right: 1px solid {c["border"]};
}}

#sidebar QPushButton {{
    background-color: transparent;
    color: {sidebar_text};
    border: none;
    border-left: 3px solid transparent;
    padding: 11px 18px;
    text-align: left;
    font-size: 13px;
    border-radius: 0;
}}

#sidebar QPushButton:hover {{
    background-color: {c["bg_elevated"] if is_dark else "#253550"};
    color: {sidebar_text_hover};
    border-left: 3px solid {c["border"] if is_dark else "#475569"};
}}

#sidebar QPushButton[active="true"] {{
    background-color: {sidebar_active_bg};
    color: {sidebar_active_text};
    border-left: 3px solid {c["accent_blue"]};
    font-weight: bold;
}}

#sidebar_title {{
    background-color: {c["bg_sidebar"]};
    border-bottom: 1px solid {c["border"]};
}}

#sidebar_title QLabel {{
    color: #E8EAF0;
    background: transparent;
}}

#app_title {{
    color: #E8EAF0;
    font-size: 14px;
    font-weight: bold;
    padding: 20px 16px 14px 16px;
}}

/* ── Content area ─────────────────────────────────────────────────────────── */
#content_area {{
    background-color: {c["bg_deep"]};
}}

/* ── Page title ───────────────────────────────────────────────────────────── */
#page_title {{
    font-size: 20px;
    font-weight: bold;
    color: {c["text_primary"]};
}}

/* ── Cards ────────────────────────────────────────────────────────────────── */
QFrame#card {{
    background-color: {c["bg_surface"]};
    border: 1px solid {c["border"]};
    border-radius: 10px;
    padding: 0px;
}}

/* ── Tables ───────────────────────────────────────────────────────────────── */
QTableWidget {{
    background-color: {c["bg_surface"]};
    border: 1px solid {c["border"]};
    border-radius: 8px;
    gridline-color: {c["bg_elevated"]};
    selection-background-color: {c["bg_active"]};
    selection-color: {selection_text};
    alternate-background-color: {c["alt_row"]};
    color: {c["text_primary"]};
    outline: none;
}}

QTableWidget::item {{
    padding: 6px 10px;
    border: none;
    color: {c["text_primary"]};
}}

QTableWidget::item:selected {{
    background-color: {c["bg_active"]};
    color: {selection_text};
}}

QHeaderView {{
    background-color: {c["bg_elevated"]};
}}

QHeaderView::section {{
    background-color: {c["bg_elevated"]};
    color: {c["text_secondary"]};
    font-weight: bold;
    font-size: 12px;
    letter-spacing: 0.5px;
    padding: 10px 10px;
    border: none;
    border-bottom: 1px solid {c["border"]};
    border-right: 1px solid {c["border"]};
}}

QHeaderView::section:last {{
    border-right: none;
}}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {c["accent_blue"]};
    color: #FFFFFF;
    border: none;
    padding: 8px 18px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {"#5A97FF" if is_dark else "#3B82F6"};
}}

QPushButton:pressed {{
    background-color: {"#3A78E8" if is_dark else "#1D4ED8"};
}}

QPushButton:disabled {{
    background-color: {c["border"]};
    color: {c["text_dimmed"]};
}}

QPushButton#btn_danger {{
    background-color: {c["btn_danger_bg"]};
    color: {c["accent_red"]};
    border: 1px solid {c["btn_danger_border"]};
}}

QPushButton#btn_danger:hover {{
    background-color: {c["accent_red"]};
    color: #FFFFFF;
    border: 1px solid {c["accent_red"]};
}}

QPushButton#btn_secondary {{
    background-color: {c["bg_elevated"]};
    color: {c["text_secondary"]};
    border: 1px solid {c["border"]};
}}

QPushButton#btn_secondary:hover {{
    background-color: {c["bg_hover"]};
    color: {c["text_primary"]};
    border: 1px solid {c["accent_blue"]};
}}

QPushButton#btn_success {{
    background-color: {c["accent_teal"]};
    color: {btn_success_text};
    font-weight: bold;
}}

QPushButton#btn_success:hover {{
    background-color: {"#00E5B8" if is_dark else "#10B981"};
}}

/* ── Inputs ───────────────────────────────────────────────────────────────── */
QLineEdit, QTextEdit {{
    background-color: {c["bg_elevated"]};
    border: 1px solid {c["border"]};
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 13px;
    color: {c["text_primary"]};
    selection-background-color: {c["accent_blue"]};
    selection-color: #FFFFFF;
}}

QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {c["accent_blue"]};
}}

QDoubleSpinBox, QSpinBox {{
    background-color: {c["bg_elevated"]};
    border: 1px solid {c["border"]};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    color: {c["text_primary"]};
}}

QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 1px solid {c["accent_blue"]};
}}

QDoubleSpinBox::up-button, QSpinBox::up-button,
QDoubleSpinBox::down-button, QSpinBox::down-button {{
    background-color: {c["spin_btn"]};
    border: {"none" if is_dark else f"1px solid {c['border']}"};
    width: 20px;
}}

QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover,
QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {{
    background-color: {c["spin_btn_hover"]};
}}

QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {{
    width: 8px;
    height: 8px;
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid {c["text_secondary"]};
}}

QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {{
    width: 8px;
    height: 8px;
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {c["text_secondary"]};
}}

QDateEdit {{
    background-color: {c["bg_elevated"]};
    border: 1px solid {c["border"]};
    border-radius: 6px;
    padding: 6px 10px;
    color: {c["text_primary"]};
}}

QDateEdit:focus {{
    border: 1px solid {c["accent_blue"]};
}}

QDateEdit::drop-down {{
    border: none;
    background-color: {c["spin_btn"]};
    width: 22px;
    border-radius: 0 6px 6px 0;
}}

QCalendarWidget {{
    background-color: {c["bg_surface"]};
    color: {c["text_primary"]};
}}

QCalendarWidget QAbstractItemView {{
    background-color: {c["bg_elevated"]};
    selection-background-color: {c["accent_blue"]};
    selection-color: #FFFFFF;
    color: {c["text_primary"]};
}}

QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {c["bg_sidebar"]};
}}

QCalendarWidget QToolButton {{
    background-color: transparent;
    color: {"#E8EAF0" if is_dark else "#FFFFFF"};
}}

/* ── ComboBox ─────────────────────────────────────────────────────────────── */
QComboBox {{
    background-color: {c["bg_elevated"]};
    border: 1px solid {c["border"]};
    border-radius: 6px;
    padding: 6px 10px;
    color: {c["text_primary"]};
    font-size: 13px;
}}

QComboBox:focus {{
    border: 1px solid {c["accent_blue"]};
}}

QComboBox:hover {{
    border: 1px solid {c["bg_hover"]};
}}

QComboBox::drop-down {{
    border: none;
    background-color: transparent;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {c["bg_elevated"]};
    border: 1px solid {c["border"]};
    selection-background-color: {c["accent_blue"]};
    selection-color: #FFFFFF;
    color: {c["text_primary"]};
    outline: none;
}}

QComboBox QAbstractItemView::item {{
    padding: 6px 10px;
    min-height: 28px;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {c["bg_hover"]};
}}

/* ── Labels ───────────────────────────────────────────────────────────────── */
QLabel {{
    color: {c["text_primary"]};
    background-color: transparent;
}}

QLabel#stat_value {{
    font-size: 26px;
    font-weight: bold;
}}

QLabel#stat_label {{
    font-size: 11px;
    color: {c["text_secondary"]};
}}

QLabel#section_title {{
    font-size: 15px;
    font-weight: bold;
    color: {c["text_primary"]};
}}

QLabel#hint_label {{
    color: {c["text_secondary"]};
    font-size: 12px;
}}

QLabel#warning_label {{
    color: {c["accent_amber"]};
    font-weight: bold;
    font-size: 12px;
}}

/* ── Tab widget ───────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {c["border"]};
    border-radius: 8px;
    background: {c["bg_surface"]};
    top: -1px;
}}

QTabBar {{
    background-color: transparent;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {c["text_secondary"]};
    padding: 8px 20px;
    border: 1px solid transparent;
    border-radius: 6px;
    margin-right: 4px;
    font-size: 13px;
}}

QTabBar::tab:hover {{
    background-color: {c["bg_elevated"]};
    color: {c["text_primary"]};
}}

QTabBar::tab:selected {{
    background-color: {c["accent_blue"]};
    color: #FFFFFF;
    font-weight: bold;
    border: 1px solid {c["accent_blue"]};
}}

/* ── Form labels ──────────────────────────────────────────────────────────── */
QFormLayout QLabel {{
    color: {c["text_secondary"]};
    font-size: 12px;
}}

/* ── Scrollbars ───────────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {c["bg_deep"]};
    width: 6px;
    border-radius: 3px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {c["border"]};
    border-radius: 3px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: {c["accent_blue"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {c["bg_deep"]};
    height: 6px;
    border-radius: 3px;
}}

QScrollBar::handle:horizontal {{
    background: {c["border"]};
    border-radius: 3px;
}}

/* ── Message box ──────────────────────────────────────────────────────────── */
QMessageBox {{
    background-color: {c["bg_surface"]};
}}

QMessageBox QLabel {{
    color: {c["text_primary"]};
}}

QMessageBox QPushButton {{
    min-width: 80px;
}}

/* ── Separators ───────────────────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {c["border"]};
    background-color: {c["border"]};
    border: none;
    max-height: 1px;
}}

/* ── CheckBox ─────────────────────────────────────────────────────────────── */
QCheckBox {{
    color: {c["text_primary"]};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {c["border"]};
    background-color: {c["bg_elevated"]};
}}

QCheckBox::indicator:checked {{
    background-color: {c["accent_blue"]};
    border: 1px solid {c["accent_blue"]};
}}

QCheckBox::indicator:hover {{
    border: 1px solid {c["accent_blue"]};
}}

/* ── ToolTip ──────────────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {c["bg_elevated"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}

/* ── Widgets inside table cells (compact padding) ─────────────────────────── */
QTableWidget QWidget {{
    background-color: {c["bg_surface"]};
}}

QTableWidget QDoubleSpinBox, QTableWidget QSpinBox {{
    padding: 2px 4px;
    border-radius: 4px;
    min-height: 28px;
    max-height: 32px;
    background-color: {c["bg_elevated"]};
}}

QTableWidget QComboBox {{
    padding: 2px 6px;
    border-radius: 4px;
    min-height: 28px;
    max-height: 32px;
    background-color: {c["bg_elevated"]};
}}

QTableWidget QPushButton {{
    padding: 2px 8px;
    border-radius: 4px;
    min-height: 26px;
    max-height: 30px;
}}
"""


# ── Default style (dark) ───────────────────────────────────────────────────────
APP_STYLE = _build_style(_DARK)
