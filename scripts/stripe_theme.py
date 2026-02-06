"""Stripe-inspired theme for PyRHEED.

This module provides a complete styling system based on Stripe's design language.
Apply using: apply_stripe_theme(app) or apply_stripe_theme(window)

References:
- https://stripe.com/blog/accessible-color-systems
- https://docs.stripe.com/elements/appearance-api
- https://docs.stripe.com/stripe-apps/style
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StripeColors:
    """Stripe design system colors."""

    # Brand colors (暗色主题优化)
    BLURPLE: str = "#8B7EFF"           # Primary brand color (柔和一些)
    BLURPLE_LIGHT: str = "#A49AFF"     # Hover state (更亮但柔和)
    BLURPLE_DARK: str = "#7A73FF"      # Pressed state

    # Neutrals (Notion Dark style)
    DOWNRIVER: str = "#FFFFFF"         # Darkest text/headers (白色文字)
    SLATE_900: str = "#191919"         # Dark backgrounds (Notion 深色背景)
    SLATE_800: str = "#2F3437"         # Elevated dark surfaces (Notion 卡片)
    SLATE_700: str = "#3F4447"         # Borders on dark (Notion 边框)
    SLATE_600: str = "#4F5458"         # Muted dark text
    SLATE_500: str = "#6B7177"         # Secondary text
    SLATE_400: str = "#9B9A97"         # Placeholder text (Notion 灰)
    SLATE_300: str = "#787774"         # Disabled text
    SLATE_200: str = "#3F4447"         # Subtle borders
    SLATE_100: str = "#2F3437"         # Light borders
    SLATE_50: str = "#252525"          # Light backgrounds

    # Semantic colors (Notion Dark style)
    TEXT_PRIMARY: str = "#FFFFFF"      # Main text (纯白)
    TEXT_SECONDARY: str = "#9B9A97"    # Secondary text (Notion 浅灰)
    TEXT_MUTED: str = "#6B7177"        # Muted/disabled text

    # Interactive (暗色主题优化)
    INTERACTIVE: str = "#5B9EF7"       # Links, secondary actions (柔和蓝)
    INTERACTIVE_HOVER: str = "#7FB4F9" # Link hover (更亮但柔和)

    # Status (暗色主题版本 - 柔和不刺眼)
    SUCCESS: str = "#4CAF50"           # Success green (柔和)
    SUCCESS_BG: str = "#1B3A1F"        # Success background (深色)
    WARNING: str = "#FFA726"           # Warning orange (柔和)
    WARNING_BG: str = "#3A2F1B"        # Warning background (深色)
    DANGER: str = "#EF5350"            # Error red (柔和)
    DANGER_BG: str = "#3A1B1B"         # Error background (深色)
    INFO: str = "#42A5F5"              # Info blue (柔和)
    INFO_BG: str = "#1B2A3A"           # Info background (深色)

    # Surfaces (Notion Dark style)
    BACKGROUND: str = "#191919"        # Page background (Notion 深色背景)
    SURFACE: str = "#2F3437"           # Card/panel background (Notion 卡片)
    SURFACE_ELEVATED: str = "#373C43"  # Elevated surface (稍亮)
    CANVAS_DARK: str = "#0D1117"       # Image canvas background (更深)

    # Borders (Notion Dark style)
    BORDER: str = "#3F4447"            # Default border (Notion 深色边框)
    BORDER_FOCUS: str = "#8B7EFF"      # Focus border (柔和紫，不刺眼)
    BORDER_DARK: str = "#3F4447"       # Border on dark bg

    # Chart colors (for data visualization - 暗色主题优化，柔和不刺眼)
    CHART_1: str = "#8B7EFF"           # Blurple (柔和紫)
    CHART_2: str = "#5FD4BC"           # Teal (柔和青)
    CHART_3: str = "#FF9999"           # Coral (柔和珊瑚)
    CHART_4: str = "#FFD88A"           # Yellow (柔和黄)
    CHART_5: str = "#B88FFF"           # Purple (柔和紫)
    CHART_6: str = "#78D4E8"           # Cyan (柔和青蓝)


@dataclass(frozen=True)
class StripeSpacing:
    """Stripe spacing tokens (in pixels)."""

    XS: int = 4
    SM: int = 8
    MD: int = 12
    LG: int = 16
    XL: int = 24
    XXL: int = 32


@dataclass(frozen=True)
class StripeBorderRadius:
    """Stripe border radius tokens."""

    SM: str = "4px"
    MD: str = "6px"
    LG: str = "8px"
    XL: str = "12px"
    PILL: str = "9999px"


@dataclass(frozen=True)
class StripeShadows:
    """Stripe box shadow definitions."""

    LEVEL_1: str = "0 1px 1px rgba(0, 0, 0, 0.03), 0 3px 6px rgba(18, 42, 66, 0.02)"
    LEVEL_2: str = "0 2px 5px rgba(50, 50, 93, 0.1), 0 1px 2px rgba(0, 0, 0, 0.08)"
    LEVEL_3: str = "0 7px 14px rgba(50, 50, 93, 0.1), 0 3px 6px rgba(0, 0, 0, 0.08)"
    LEVEL_4: str = "0 15px 35px rgba(50, 50, 93, 0.1), 0 5px 15px rgba(0, 0, 0, 0.07)"
    FOCUS: str = "0 0 0 3px rgba(99, 91, 255, 0.25)"
    INSET: str = "inset 0 1px 2px rgba(0, 0, 0, 0.1)"


# Instantiate for easy access
Colors = StripeColors()
Spacing = StripeSpacing()
BorderRadius = StripeBorderRadius()
Shadows = StripeShadows()


# Font stack matching Stripe's typography
FONT_FAMILY = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'


STRIPE_STYLESHEET = f"""
/* ============================================================
   Stripe-Inspired Theme for PyRHEED
   Based on Stripe's Design System
   ============================================================ */

/* ---------- Global Defaults ---------- */
QWidget {{
    font-family: {FONT_FAMILY};
    font-size: 13px;
    color: {Colors.TEXT_PRIMARY};
}}

QMainWindow {{
    background-color: {Colors.BACKGROUND};
}}

/* ---------- Buttons ---------- */
QPushButton {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER};
    border-radius: {BorderRadius.MD};
    padding: 8px 16px;
    font-weight: 500;
    font-size: 13px;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {Colors.SLATE_50};
    border-color: {Colors.SLATE_200};
}}

QPushButton:pressed {{
    background-color: {Colors.SLATE_100};
}}

QPushButton:disabled {{
    background-color: {Colors.SLATE_50};
    color: {Colors.TEXT_MUTED};
    border-color: {Colors.SLATE_100};
}}

QPushButton:checked {{
    background-color: {Colors.BLURPLE};
    color: white;
    border-color: {Colors.BLURPLE};
}}

QPushButton:checked:hover {{
    background-color: {Colors.BLURPLE_LIGHT};
}}

/* ---------- Labels ---------- */
QLabel {{
    color: {Colors.TEXT_PRIMARY};
    background: transparent;
}}

/* ---------- Input Fields ---------- */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER};
    border-radius: {BorderRadius.SM};
    padding: 8px 12px;
    font-size: 14px;
    color: {Colors.TEXT_PRIMARY};
    selection-background-color: {Colors.BLURPLE};
    selection-color: white;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {Colors.BLURPLE};
    outline: none;
}}

QLineEdit:disabled {{
    background-color: {Colors.SLATE_50};
    color: {Colors.TEXT_MUTED};
}}

/* ---------- SpinBox ---------- */
QSpinBox, QDoubleSpinBox {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER};
    border-radius: {BorderRadius.SM};
    padding: 6px 8px;
    font-size: 13px;
    color: {Colors.TEXT_PRIMARY};
    min-width: 60px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {Colors.BLURPLE};
}}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {Colors.SLATE_50};
    border: none;
    width: 20px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {Colors.SLATE_100};
}}

QSpinBox::up-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid {Colors.SLATE_500};
    width: 0;
    height: 0;
}}

QSpinBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {Colors.SLATE_500};
    width: 0;
    height: 0;
}}

/* ---------- ComboBox ---------- */
QComboBox {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER};
    border-radius: {BorderRadius.SM};
    padding: 8px 12px;
    padding-right: 30px;
    font-size: 13px;
    color: {Colors.TEXT_PRIMARY};
    min-width: 100px;
}}

QComboBox:hover {{
    border-color: {Colors.SLATE_200};
}}

QComboBox:focus {{
    border-color: {Colors.BLURPLE};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
    background: transparent;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {Colors.SLATE_500};
    width: 0;
    height: 0;
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER};
    border-radius: {BorderRadius.SM};
    padding: 4px;
    selection-background-color: {Colors.SLATE_50};
    selection-color: {Colors.TEXT_PRIMARY};
}}

/* ---------- CheckBox ---------- */
QCheckBox {{
    spacing: 8px;
    color: {Colors.TEXT_PRIMARY};
    font-size: 13px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {Colors.BORDER};
    border-radius: {BorderRadius.SM};
    background-color: {Colors.SURFACE};
}}

QCheckBox::indicator:hover {{
    border-color: {Colors.BLURPLE};
}}

QCheckBox::indicator:checked {{
    background-color: {Colors.BLURPLE};
    border-color: {Colors.BLURPLE};
}}

/* ---------- GroupBox ---------- */
QGroupBox {{
    font-weight: 600;
    font-size: 13px;
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER};
    border-radius: {BorderRadius.LG};
    margin-top: 16px;
    padding: 16px 12px 12px 12px;
    background-color: {Colors.SURFACE};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 8px;
    background-color: {Colors.SURFACE};
    color: {Colors.DOWNRIVER};
}}

/* ---------- Slider ---------- */
QSlider::groove:horizontal {{
    height: 4px;
    background-color: {Colors.SLATE_200};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background-color: {Colors.BLURPLE};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
    border: 2px solid white;
}}

QSlider::handle:horizontal:hover {{
    background-color: {Colors.BLURPLE_LIGHT};
}}

QSlider::sub-page:horizontal {{
    background-color: {Colors.BLURPLE};
    border-radius: 2px;
}}

QSlider:disabled {{
    opacity: 0.5;
}}

/* ---------- List Widget ---------- */
QListWidget {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER};
    border-radius: {BorderRadius.MD};
    padding: 4px;
    outline: none;
}}

QListWidget::item {{
    padding: 8px 12px;
    border-radius: {BorderRadius.SM};
    margin: 2px 0;
}}

QListWidget::item:hover {{
    background-color: {Colors.SLATE_50};
}}

QListWidget::item:selected {{
    background-color: rgba(99, 91, 255, 0.1);
    color: {Colors.BLURPLE};
}}

/* ---------- Splitter ---------- */
QSplitter::handle {{
    background-color: {Colors.BORDER};
}}

QSplitter::handle:horizontal {{
    width: 1px;
}}

QSplitter::handle:vertical {{
    height: 1px;
}}

/* ---------- Tab Widget ---------- */
QTabWidget::pane {{
    border: 1px solid {Colors.BORDER};
    border-radius: {BorderRadius.MD};
    background-color: {Colors.SURFACE};
    top: -1px;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {Colors.TEXT_SECONDARY};
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 500;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
}}

QTabBar::tab:hover {{
    color: {Colors.TEXT_PRIMARY};
}}

QTabBar::tab:selected {{
    color: {Colors.BLURPLE};
    border-bottom: 2px solid {Colors.BLURPLE};
}}

/* ---------- Status Bar ---------- */
QStatusBar {{
    background-color: {Colors.SURFACE};
    border-top: 1px solid {Colors.BORDER};
    color: {Colors.TEXT_SECONDARY};
    font-size: 12px;
    padding: 4px 12px;
}}

QStatusBar::item {{
    border: none;
}}

/* ---------- Scroll Bars ---------- */
QScrollBar:vertical {{
    background-color: transparent;
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {Colors.SLATE_300};
    border-radius: 4px;
    min-height: 30px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {Colors.SLATE_400};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 12px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {Colors.SLATE_300};
    border-radius: 4px;
    min-width: 30px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {Colors.SLATE_400};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ---------- Graphics View (Canvas) ---------- */
QGraphicsView {{
    background-color: {Colors.CANVAS_DARK};
    border: 1px solid {Colors.BORDER};
    border-radius: {BorderRadius.MD};
}}

/* ---------- Chart View ---------- */
QChartView {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER};
    border-radius: {BorderRadius.MD};
}}

/* ---------- ToolTip ---------- */
QToolTip {{
    background-color: {Colors.DOWNRIVER};
    color: white;
    border: none;
    border-radius: {BorderRadius.SM};
    padding: 6px 10px;
    font-size: 12px;
}}

/* ---------- Progress Bar ---------- */
QProgressBar {{
    background-color: {Colors.SLATE_100};
    border: none;
    border-radius: {BorderRadius.SM};
    height: 6px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {Colors.BLURPLE};
    border-radius: {BorderRadius.SM};
}}
"""


# Convenience function to apply theme
def apply_stripe_theme(widget) -> None:
    """Apply Stripe theme to a widget or application.

    Args:
        widget: QApplication, QMainWindow, or any QWidget

    Example:
        app = QApplication(sys.argv)
        apply_stripe_theme(app)
        # or
        window = QMainWindow()
        apply_stripe_theme(window)
    """
    widget.setStyleSheet(STRIPE_STYLESHEET)


# Export chart colors as a list for easy iteration
CHART_COLORS = [
    Colors.CHART_1,
    Colors.CHART_2,
    Colors.CHART_3,
    Colors.CHART_4,
    Colors.CHART_5,
    Colors.CHART_6,
]
