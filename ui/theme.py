# -*- coding: utf-8 -*-
"""Visual design system for GeoToolkit for Google Earth Engine.

One source of truth for colour, typography and component styling. The main
window and the layer chooser apply ``STYLESHEET`` once and use semantic roles
(``primaryButton``, ``stepButton``, ``hint``, ``detailTitle``). Nothing here
touches plugin behaviour.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

TEXT = "#1F2933"
TEXT_SECONDARY = "#66727E"
TEXT_DISABLED = "#9AA4AE"

CANVAS = "#F6F7F9"
SURFACE = "#FFFFFF"
SUBTLE = "#FBFCFD"

BORDER = "#E2E6EB"
BORDER_STRONG = "#CDD4DC"

PRIMARY = "#0B5E8E"
PRIMARY_HOVER = "#0A517A"
PRIMARY_PRESSED = "#08425F"
ACCENT = "#1499D6"
ACCENT_SOFT = "#EAF5FB"
SUCCESS = "#3F7F2E"          # restrained green for the connected state
DANGER = "#B42318"

FONT_STACK = (
    '"Segoe UI", "SF Pro Text", "Inter", "Helvetica Neue", '
    '"Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans SC", "Noto Naskh Arabic", '
    'Arial, sans-serif'
)
MONO_STACK = '"Cascadia Mono", "Consolas", "SF Mono", "DejaVu Sans Mono", monospace'

_ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def resource_path(name: str) -> str:
    """Absolute, forward-slash path usable by ``url(...)`` in Qt style sheets."""
    return os.path.join(_ASSET_DIR, name).replace("\\", "/")


_QSS_TEMPLATE = """
QDialog#GeoToolkitDialog, QDialog#GeoToolkitChooser {
    background-color: @CANVAS@;
    color: @TEXT@;
}

QMessageBox {
    background-color: @SURFACE@;
}

QMessageBox QLabel {
    color: @TEXT@;
}

QWidget {
    font-family: @FONT@;
    font-size: 9pt;
    color: @TEXT@;
}

QLabel {
    background: transparent;
    color: @TEXT@;
}

QLabel:disabled {
    color: @TEXT_DISABLED@;
}

/* ---------- Application header ---------- */
QFrame#appHeader {
    background-color: @SURFACE@;
    border: 0;
    border-bottom: 1px solid @BORDER@;
}

QLabel#appTitle {
    font-size: 12pt;
    font-weight: 600;
    color: @TEXT@;
}

QLabel#appSubtitle {
    font-size: 8.5pt;
    color: @TEXT_SECONDARY@;
}

QLabel#connectionState {
    color: @TEXT_SECONDARY@;
    font-size: 8.5pt;
}

QLabel#connectionState[state="connected"] {
    color: @SUCCESS@;
    font-weight: 600;
}

/* ---------- Workflow sidebar ---------- */
QFrame#sidebar {
    background-color: @SUBTLE@;
    border: 0;
    border-right: 1px solid @BORDER@;
}

QPushButton#stepButton {
    text-align: left;
    background: transparent;
    border: 0;
    border-left: 2px solid transparent;
    border-radius: 0;
    padding: 8px 12px;
    color: @TEXT_SECONDARY@;
    font-weight: 400;
}

QPushButton#stepButton:hover {
    background-color: #F1F4F7;
    color: @TEXT@;
}

QPushButton#stepButton:checked {
    background-color: @ACCENT_SOFT@;
    border-left: 2px solid @ACCENT@;
    color: @PRIMARY@;
    font-weight: 600;
}

/* ---------- Pages ---------- */
QScrollArea {
    border: 0;
    background: transparent;
}

/* ---------- Panels ---------- */
QGroupBox {
    background-color: @SURFACE@;
    border: 1px solid @BORDER@;
    border-radius: 4px;
    margin-top: 20px;
    padding: 12px;
    font-size: 9.5pt;
    font-weight: 600;
    color: @TEXT@;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 0;
    padding: 0 0 6px 0;
    background: transparent;
}

QFrame#detailPanel {
    background-color: @SURFACE@;
    border: 1px solid @BORDER@;
    border-radius: 4px;
}

QLabel#fieldLabel {
    color: #4B5763;
    font-size: 8.5pt;
    font-weight: 600;
}

QLabel#hint {
    color: @TEXT_SECONDARY@;
    font-size: 8.5pt;
}

QLabel#stepCaption {
    color: @TEXT_SECONDARY@;
    font-size: 8.5pt;
}

QLabel#summaryKey {
    color: @TEXT_SECONDARY@;
}

QLabel#summaryValue {
    color: @TEXT@;
    font-weight: 600;
}

QLabel#detailTitle {
    font-size: 11pt;
    font-weight: 600;
    color: @TEXT@;
}

QLabel#detailProvider {
    color: @TEXT_SECONDARY@;
    font-size: 8.5pt;
}

QLabel#subsectionTitle {
    font-size: 9pt;
    font-weight: 600;
    color: #4B5763;
}

QLabel#notice {
    background-color: #FFF9EC;
    border: 1px solid #F0E2C4;
    border-radius: 4px;
    color: #6B4E00;
    padding: 8px 10px;
    font-size: 8.5pt;
}

/* ---------- Inputs ---------- */
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
    background-color: @SURFACE@;
    color: @TEXT@;
    border: 1px solid @BORDER_STRONG@;
    border-radius: 4px;
    padding: 3px 8px;
    min-height: 0px;
    selection-background-color: @ACCENT@;
    selection-color: #FFFFFF;
}

QLineEdit:hover, QComboBox:hover, QDateEdit:hover, QSpinBox:hover,
QDoubleSpinBox:hover {
    border-color: #B4BEC8;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QComboBox:on {
    border-color: @ACCENT@;
}

QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled,
QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #F2F4F6;
    color: @TEXT_DISABLED@;
    border-color: @BORDER@;
}

QLineEdit {
    placeholder-text-color: #8B96A2;
}

QComboBox {
    padding-right: 26px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: 0;
}

QComboBox::down-arrow {
    image: url("@CHEVRON_DOWN@");
    width: 10px;
    height: 6px;
}

QComboBox QAbstractItemView {
    background-color: @SURFACE@;
    color: @TEXT@;
    border: 1px solid @BORDER_STRONG@;
    selection-background-color: @ACCENT_SOFT@;
    selection-color: @TEXT@;
    outline: 0;
    padding: 2px;
}

QDateEdit {
    padding-right: 26px;
}

QDateEdit::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: 0;
}

QDateEdit::down-arrow {
    image: url("@CHEVRON_DOWN@");
    width: 10px;
    height: 6px;
}

QSpinBox {
    padding-right: 24px;
}

QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 18px;
    border-left: 1px solid @BORDER_STRONG@;
    border-bottom: 1px solid @BORDER_STRONG@;
    border-top-right-radius: 4px;
    background: transparent;
}

QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 18px;
    border-left: 1px solid @BORDER_STRONG@;
    border-bottom-right-radius: 4px;
    background: transparent;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: #F2F5F8;
}

QSpinBox::up-arrow {
    image: url("@CHEVRON_UP@");
    width: 8px;
    height: 5px;
}

QSpinBox::down-arrow {
    image: url("@CHEVRON_DOWN@");
    width: 8px;
    height: 5px;
}

/* ---------- Buttons ---------- */
QPushButton {
    background-color: @SURFACE@;
    color: @TEXT@;
    border: 1px solid @BORDER_STRONG@;
    border-radius: 4px;
    padding: 3px 10px;
    min-height: 0px;
}

QPushButton:hover {
    background-color: #F2F5F8;
    border-color: #B4BEC8;
}

QPushButton:pressed {
    background-color: #E9EDF1;
}

QPushButton:focus {
    border-color: @ACCENT@;
}

QPushButton:disabled {
    color: @TEXT_DISABLED@;
    background-color: #F7F8FA;
    border-color: #E6E9ED;
}

QPushButton#primaryButton {
    background-color: @PRIMARY@;
    color: #FFFFFF;
    border-color: @PRIMARY@;
    font-weight: 600;
    padding: 4px 16px;
}

QPushButton#primaryButton:hover {
    background-color: @PRIMARY_HOVER@;
    border-color: @PRIMARY_HOVER@;
}

QPushButton#primaryButton:pressed {
    background-color: @PRIMARY_PRESSED@;
    border-color: @PRIMARY_PRESSED@;
}

QPushButton#primaryButton:disabled {
    background-color: #B7C8D5;
    border-color: #B7C8D5;
    color: #F4F7F9;
}

QPushButton#ghostButton {
    background: transparent;
    border-color: transparent;
    color: @TEXT_SECONDARY@;
}

QPushButton#ghostButton:hover {
    background-color: #EEF1F4;
    color: @TEXT@;
}

/* ---------- Checkboxes and radios ---------- */
QCheckBox, QRadioButton {
    spacing: 8px;
    color: @TEXT@;
}

QCheckBox:disabled, QRadioButton:disabled {
    color: @TEXT_DISABLED@;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 15px;
    height: 15px;
}

QCheckBox::indicator {
    border: 1px solid #A9B4BF;
    border-radius: 3px;
    background: @SURFACE@;
}

QCheckBox::indicator:hover {
    border-color: @ACCENT@;
}

QCheckBox::indicator:checked {
    background: @PRIMARY@;
    border-color: @PRIMARY@;
    image: url("@CHECK@");
}

QCheckBox::indicator:disabled {
    background: #F2F4F6;
    border-color: @BORDER@;
}

QCheckBox::indicator:checked:disabled {
    background: #B7C8D5;
    border-color: #B7C8D5;
}

QRadioButton::indicator {
    border: 1px solid #A9B4BF;
    border-radius: 8px;
    background: @SURFACE@;
}

QRadioButton::indicator:hover {
    border-color: @ACCENT@;
}

QRadioButton::indicator:checked {
    border-color: @PRIMARY@;
    background: @SURFACE@;
    image: url("@RADIO_DOT@");
}

QRadioButton::indicator:disabled {
    background: #F2F4F6;
    border-color: @BORDER@;
}

QRadioButton::indicator:checked:disabled {
    border-color: #B7C8D5;
}

QTreeView::indicator {
    width: 14px;
    height: 14px;
    margin-right: 6px;
    border: 1px solid #A9B4BF;
    border-radius: 3px;
    background: @SURFACE@;
}

QTreeView::indicator:checked {
    background: @PRIMARY@;
    border-color: @PRIMARY@;
    image: url("@CHECK@");
}

QTreeView::indicator:indeterminate {
    background: @PRIMARY@;
    border-color: @PRIMARY@;
    image: url("@DASH@");
}

/* ---------- Trees and tables ---------- */
QTreeWidget, QTableWidget {
    background-color: @SURFACE@;
    alternate-background-color: #FAFBFC;
    border: 1px solid @BORDER@;
    border-radius: 4px;
    gridline-color: #EEF1F4;
    selection-background-color: @ACCENT_SOFT@;
    selection-color: @TEXT@;
    outline: 0;
}

QTreeWidget {
    padding-left: 6px;
}

QTreeWidget::item {
    padding: 4px 2px 4px 8px;
    margin: 1px 4px; /* adds a 4px gap on left/right of the highlight box itself */
    border-radius: 0px; /* makes the hover/selection highlight have rounded corners */   

}

QTreeWidget::item:hover {
    background-color: #F4F7F9;
}

QTreeWidget::item:selected {
    background-color: @ACCENT_SOFT@;
    color: @TEXT@;
}

QTableWidget::item {
    padding: 4px 6px;
}

QHeaderView::section {
    background-color: #F3F5F7;
    color: #4B5763;
    border: 0;
    border-bottom: 1px solid @BORDER@;
    padding: 6px 8px;
    font-size: 8.5pt;
    font-weight: 600;
}

QTableCornerButton::section {
    background-color: #F3F5F7;
    border: 0;
}

/* ---------- Tabs ---------- */
QTabWidget::pane {
    border: 1px solid @BORDER@;
    border-radius: 4px;
    background: @SURFACE@;
    top: 0;
}

QTabBar::tab {
    background: transparent;
    color: @TEXT_SECONDARY@;
    padding: 4px 12px;
    border: 0;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:hover {
    color: @TEXT@;
}

QTabBar::tab:selected {
    color: @PRIMARY@;
    background-color: @ACCENT_SOFT@;
    border-bottom: 2px solid @ACCENT@;
    font-weight: 600;
}

/* ---------- Progress ---------- */
QProgressBar {
    background-color: #E7ECF1;
    border: 0;
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
}

QProgressBar::chunk {
    background-color: @ACCENT@;
    border-radius: 3px;
}

/* ---------- Text areas ---------- */
QPlainTextEdit {
    background-color: #FBFCFD;
    color: #2B3440;
    border: 1px solid @BORDER@;
    border-radius: 4px;
    padding: 6px;
    font-family: @MONO@;
    font-size: 8.5pt;
    selection-background-color: @ACCENT@;
    selection-color: #FFFFFF;
}

/* ---------- Footer ---------- */
QFrame#footer {
    background-color: @SURFACE@;
    border: 0;
    border-top: 1px solid @BORDER@;
}

QFrame#footer QPushButton#primaryButton {
    padding: 4px 18px;
}

/* ---------- Menus ---------- */
QMenu {
    background-color: @SURFACE@;
    border: 1px solid @BORDER_STRONG@;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px 6px 12px;
    color: @TEXT@;
}

QMenu::item:selected {
    background-color: @ACCENT_SOFT@;
    color: @TEXT@;
}

/* ---------- Scroll bars ---------- */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #C7D0D9;
    min-height: 16px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #AAB6C0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #C7D0D9;
    min-width: 30px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #AAB6C0;
}

QScrollBar::add-line, QScrollBar::sub-line {
    width: 0;
    height: 0;
}

QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
}

/* ---------- Tooltips ---------- */
QToolTip {
    background-color: #1F2933;
    color: #FFFFFF;
    border: 1px solid #1F2933;
    padding: 4px 6px;
}
"""


def build_stylesheet() -> str:
    """Return the complete style sheet with palette and fonts substituted."""
    tokens = {
        "@TEXT@": TEXT,
        "@TEXT_SECONDARY@": TEXT_SECONDARY,
        "@TEXT_DISABLED@": TEXT_DISABLED,
        "@CANVAS@": CANVAS,
        "@SURFACE@": SURFACE,
        "@SUBTLE@": SUBTLE,
        "@BORDER@": BORDER,
        "@BORDER_STRONG@": BORDER_STRONG,
        "@PRIMARY@": PRIMARY,
        "@PRIMARY_HOVER@": PRIMARY_HOVER,
        "@PRIMARY_PRESSED@": PRIMARY_PRESSED,
        "@ACCENT@": ACCENT,
        "@ACCENT_SOFT@": ACCENT_SOFT,
        "@SUCCESS@": SUCCESS,
        "@DANGER@": DANGER,
        "@FONT@": FONT_STACK,
        "@MONO@": MONO_STACK,
        "@CHECK@": resource_path("check.svg"),
        "@DASH@": resource_path("dash.svg"),
        "@CHEVRON_DOWN@": resource_path("chevron-down.svg"),
        "@CHEVRON_UP@": resource_path("chevron-up.svg"),
        "@CHEVRON_RIGHT@": resource_path("chevron-right.svg"),
        "@RADIO_DOT@": resource_path("radio-dot.svg"),
    }
    qss = _QSS_TEMPLATE
    for token, value in tokens.items():
        qss = qss.replace(token, value)
    return qss


STYLESHEET = build_stylesheet()


def apply_theme(widget) -> None:
    """Apply the design system to one window and its child widgets."""
    widget.setStyleSheet(STYLESHEET)


def repolish(widget) -> None:
    """Re-evaluate dynamic-property selectors after a state change."""
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()
