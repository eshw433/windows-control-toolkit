from __future__ import annotations


PALETTE = {
    "bg_window":     "#0b1020",
    "bg_panel":      "#10172a",
    "bg_card":       "#141d35",
    "bg_card_hi":    "#19243f",
    "bg_input":      "#0d1428",
    "border":        "#1c2945",
    "border_hi":     "#2b3d68",
    "text":          "#e6ecf5",
    "text_dim":      "#8d99b3",
    "text_mute":     "#5b6a8a",
    "accent":        "#5cd0ff",
    "accent_hot":    "#84e1ff",
    "accent_alt":    "#9a7dff",
    "success":       "#4dd599",
    "warning":       "#ffb547",
    "danger":        "#ff6b6b",
    "info":          "#5cd0ff",
}


def _fmt(template: str, palette: dict[str, str]) -> str:
    out = template
    for key, value in palette.items():
        out = out.replace("{" + key + "}", value)
    return out


_BASE = """
* {
    outline: 0;
}

QWidget {
    background-color: {bg_window};
    color: {text};
    font-family: "Inter", "Segoe UI", "SF Pro Text", "Roboto", sans-serif;
    font-size: 13px;
    selection-background-color: {accent};
    selection-color: {bg_window};
}

QMainWindow, QDialog {
    background-color: {bg_window};
}

QToolTip {
    background-color: {bg_card_hi};
    color: {text};
    border: 1px solid {border_hi};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

#sidebar {
    background-color: {bg_panel};
    border-right: 1px solid {border};
    min-width: 260px;
    max-width: 260px;
}

#sidebar QPushButton {
    background-color: transparent;
    border: none;
    border-radius: 10px;
    color: {text_dim};
    font-size: 13px;
    font-weight: 500;
    padding: 10px 14px 10px 18px;
    text-align: left;
}

#sidebar QPushButton:hover {
    background-color: {bg_card};
    color: {text};
}

#sidebar QPushButton:checked,
#sidebar QPushButton[active="true"] {
    background-color: {bg_card_hi};
    color: {accent};
    font-weight: 600;
    border-left: 3px solid {accent};
}

#appTitle {
    color: {accent};
    font-size: 17px;
    font-weight: 800;
    letter-spacing: 0.4px;
    padding: 24px 18px 4px 18px;
}

#appSubtitle {
    color: {text_mute};
    font-size: 11px;
    padding: 0 18px 18px 18px;
}

#contentStack { background-color: {bg_window}; }

#pageTitle {
    font-size: 22px;
    font-weight: 800;
    color: {text};
    padding-bottom: 4px;
}

#pageSubtitle {
    font-size: 12px;
    color: {text_mute};
    padding-bottom: 12px;
}

#section {
    color: {text_dim};
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    padding: 12px 0 4px 0;
}

.StatCard, QFrame#card {
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 16px;
}

.StatCard QLabel#statValue {
    font-size: 28px;
    font-weight: 800;
    color: {accent};
}

.StatCard QLabel#statLabel {
    font-size: 12px;
    color: {text_dim};
    letter-spacing: 0.4px;
    text-transform: uppercase;
}

QTableWidget, QTableView, QTreeWidget, QTreeView, QListWidget, QListView {
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: 10px;
    gridline-color: {border};
    selection-background-color: {bg_card_hi};
    selection-color: {accent_hot};
    alternate-background-color: {bg_panel};
    show-decoration-selected: 1;
}

QHeaderView::section {
    background-color: {bg_panel};
    color: {text_dim};
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 9px 12px;
    border: none;
    border-right: 1px solid {border};
    border-bottom: 1px solid {border};
}

QTableWidget::item, QTableView::item, QTreeWidget::item, QListWidget::item {
    padding: 6px 12px;
    border-bottom: 1px solid {border};
}

QTableWidget::item:selected, QTableView::item:selected, QTreeWidget::item:selected, QListWidget::item:selected {
    background-color: {bg_card_hi};
    color: {accent_hot};
}

QPushButton {
    background-color: {bg_card_hi};
    color: {text};
    border: 1px solid {border_hi};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: {border_hi};
    border-color: {accent};
    color: {accent_hot};
}

QPushButton:pressed {
    background-color: {bg_card};
}

QPushButton:disabled {
    color: {text_mute};
    border-color: {border};
    background-color: {bg_panel};
}

QPushButton#btnPrimary {
    background-color: {accent};
    color: {bg_window};
    border-color: {accent};
    font-weight: 700;
}
QPushButton#btnPrimary:hover { background-color: {accent_hot}; border-color: {accent_hot}; color: {bg_window}; }
QPushButton#btnPrimary:pressed { background-color: #3eb5e8; }

QPushButton#btnSuccess {
    background-color: {success};
    color: {bg_window};
    border-color: {success};
    font-weight: 700;
}
QPushButton#btnSuccess:hover { background-color: #6ee0ad; border-color: #6ee0ad; }

QPushButton#btnDanger {
    background-color: {danger};
    color: {bg_window};
    border-color: {danger};
    font-weight: 700;
}
QPushButton#btnDanger:hover { background-color: #ff8b8b; border-color: #ff8b8b; }

QPushButton#btnGhost {
    background-color: transparent;
    color: {text_dim};
    border: 1px solid {border};
}
QPushButton#btnGhost:hover {
    color: {accent_hot};
    border-color: {accent};
}

QPushButton#btnLink {
    background-color: transparent;
    color: {accent};
    border: none;
    padding: 4px 6px;
    text-align: left;
}
QPushButton#btnLink:hover {
    color: {accent_hot};
    text-decoration: underline;
}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: {bg_input};
    border: 1px solid {border};
    border-radius: 8px;
    color: {text};
    padding: 7px 12px;
    selection-background-color: {accent};
    selection-color: {bg_window};
}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    border-color: {border_hi};
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: {accent};
}

QComboBox::drop-down {
    border: none;
    width: 24px;
    padding-right: 4px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {text_dim};
    width: 0;
    height: 0;
}

QComboBox QAbstractItemView {
    background-color: {bg_card};
    border: 1px solid {border_hi};
    border-radius: 8px;
    padding: 4px;
    selection-background-color: {bg_card_hi};
    selection-color: {accent_hot};
}

QScrollBar:vertical {
    background-color: transparent;
    width: 10px;
    margin: 2px 0;
}
QScrollBar::handle:vertical {
    background-color: {border_hi};
    border-radius: 5px;
    min-height: 36px;
}
QScrollBar::handle:vertical:hover { background-color: {accent}; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QScrollBar:horizontal {
    background-color: transparent;
    height: 10px;
    margin: 0 2px;
}
QScrollBar::handle:horizontal {
    background-color: {border_hi};
    border-radius: 5px;
    min-width: 36px;
}
QScrollBar::handle:horizontal:hover { background-color: {accent}; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }

QTabWidget::pane {
    border: 1px solid {border};
    border-radius: 10px;
    background-color: {bg_card};
    top: -1px;
}

QTabBar::tab {
    background-color: transparent;
    color: {text_dim};
    padding: 9px 18px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
}

QTabBar::tab:hover { color: {text}; }

QTabBar::tab:selected {
    background-color: {bg_card};
    color: {accent};
    border-bottom: 2px solid {accent};
}

QCheckBox {
    spacing: 8px;
    color: {text};
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid {border_hi};
    border-radius: 5px;
    background-color: {bg_input};
}

QCheckBox::indicator:hover { border-color: {accent}; }

QCheckBox::indicator:checked {
    background-color: {accent};
    border-color: {accent};
    image: none;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 9px;
    border: 2px solid {border_hi};
    background-color: {bg_input};
}
QRadioButton::indicator:checked {
    background-color: {accent};
    border-color: {accent};
}

QGroupBox {
    border: 1px solid {border};
    border-radius: 10px;
    margin-top: 16px;
    padding: 16px 12px 12px 12px;
    font-weight: 700;
    color: {text_dim};
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    background-color: {bg_window};
    color: {text_dim};
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}

QStatusBar {
    background-color: {bg_panel};
    border-top: 1px solid {border};
    color: {text_mute};
    font-size: 11px;
}

QProgressBar {
    background-color: {bg_input};
    border-radius: 6px;
    text-align: center;
    color: {text};
    font-size: 11px;
    height: 10px;
}

QProgressBar::chunk {
    background-color: {accent};
    border-radius: 6px;
}

QMenu {
    background-color: {bg_card};
    border: 1px solid {border_hi};
    border-radius: 8px;
    padding: 6px;
    color: {text};
}

QMenu::item {
    padding: 7px 16px;
    border-radius: 6px;
}

QMenu::item:selected {
    background-color: {bg_card_hi};
    color: {accent_hot};
}

QMenu::separator {
    height: 1px;
    background: {border};
    margin: 4px 6px;
}

QSlider::groove:horizontal {
    background: {bg_input};
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: {accent};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover { background: {accent_hot}; }

QSplitter::handle {
    background-color: {border};
}

QToolBar {
    background-color: {bg_panel};
    border: none;
    spacing: 4px;
    padding: 6px;
}

QToolButton {
    background-color: transparent;
    border-radius: 6px;
    padding: 5px 8px;
    color: {text_dim};
}
QToolButton:hover {
    background-color: {bg_card_hi};
    color: {accent_hot};
}
"""


PRESETS = {
    "midnight": PALETTE,
    "aurora": {
        **PALETTE,
        "bg_window": "#0b1620",
        "bg_panel": "#11202c",
        "bg_card": "#13283a",
        "bg_card_hi": "#18324a",
        "border": "#1f3d52",
        "border_hi": "#2b5774",
        "accent": "#39e6b3",
        "accent_hot": "#65f0c4",
        "accent_alt": "#7af0d4",
    },
    "solar": {
        **PALETTE,
        "bg_window": "#1c1a14",
        "bg_panel": "#26221a",
        "bg_card": "#2e2820",
        "bg_card_hi": "#3a3328",
        "border": "#3a3328",
        "border_hi": "#56493a",
        "accent": "#ffb347",
        "accent_hot": "#ffc977",
        "accent_alt": "#ff8c4b",
        "success": "#a4d65e",
    },
    "amethyst": {
        **PALETTE,
        "bg_window": "#100926",
        "bg_panel": "#1a1136",
        "bg_card": "#221a4a",
        "bg_card_hi": "#2c2466",
        "border": "#2b2257",
        "border_hi": "#473b8b",
        "accent": "#b489ff",
        "accent_hot": "#d2b3ff",
        "accent_alt": "#ff89d6",
    },
    "graphite": {
        **PALETTE,
        "bg_window": "#15171a",
        "bg_panel": "#1c1f23",
        "bg_card": "#23272d",
        "bg_card_hi": "#2c313a",
        "border": "#2a2f37",
        "border_hi": "#3c424d",
        "accent": "#ff9966",
        "accent_hot": "#ffb38a",
        "accent_alt": "#ffd6a3",
    },
    "light": {
        **PALETTE,
        "bg_window": "#f5f7fa",
        "bg_panel": "#eaecf0",
        "bg_card": "#ffffff",
        "bg_card_hi": "#e8f0fe",
        "bg_input": "#ffffff",
        "border": "#d0d7e3",
        "border_hi": "#a8b8d8",
        "text": "#1a2035",
        "text_dim": "#4a5568",
        "text_mute": "#8a9ab8",
        "accent": "#1a73e8",
        "accent_hot": "#1557b0",
        "accent_alt": "#7c4dff",
        "success": "#1e8e3e",
        "warning": "#f29900",
        "danger": "#d93025",
        "info": "#1a73e8",
    },
}


def list_presets() -> list[str]:
    return list(PRESETS.keys())


def get_palette(name: str) -> dict[str, str]:
    return dict(PRESETS.get(name, PALETTE))


def stylesheet_for(name: str = "midnight") -> str:
    return _fmt(_BASE, get_palette(name))


DARK_STYLESHEET = stylesheet_for("midnight")
