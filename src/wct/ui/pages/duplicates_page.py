from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wct.core.format import human_size
from wct.core.i18n import t
from wct.ui.widgets.search_box import SearchBox
from wct.ui.widgets.stat_card import StatCard


class DuplicatesPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._folder = ""
        self._groups: list[dict] = []
        self._filter = ""
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        self._header = QLabel(t("duplicate_finder"))
        self._header.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        root.addWidget(self._header)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self.card_groups = StatCard(t("duplicate_groups"), "0", "#9b59b6")
        self.card_wasted = StatCard(t("duplicate_wasted"), "0 B", "#e74c3c")
        cards_row.addWidget(self.card_groups)
        cards_row.addWidget(self.card_wasted)
        cards_row.addStretch()
        root.addLayout(cards_row)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self._folder_label = QLabel(t("no_folder"))
        self._folder_label.setStyleSheet("color: #8892b0; border: none;")
        toolbar.addWidget(self._folder_label, 1)

        self.btn_choose = QPushButton(t("choose_folder"))
        self.btn_choose.clicked.connect(self._pick_folder)
        toolbar.addWidget(self.btn_choose)

        self.btn_scan = QPushButton(t("find_duplicates"))
        self.btn_scan.setObjectName("btnPrimary")
        toolbar.addWidget(self.btn_scan)

        root.addLayout(toolbar)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        self._strategy_label = QLabel(t("duplicate_strategy"))
        self._strategy_label.setStyleSheet("color: #8892b0; border: none;")
        controls.addWidget(self._strategy_label)

        self.cmb_strategy = QComboBox()
        self.cmb_strategy.addItem(t("strategy_oldest"), "oldest")
        self.cmb_strategy.addItem(t("strategy_newest"), "newest")
        self.cmb_strategy.addItem(t("strategy_shortest"), "shortest")
        controls.addWidget(self.cmb_strategy)

        self.chk_dry_run = QCheckBox(t("duplicate_dry_run"))
        self.chk_dry_run.setChecked(True)
        controls.addWidget(self.chk_dry_run)

        controls.addStretch()

        self.search = SearchBox(t("search_placeholder"))
        self.search.text_changed.connect(self._on_search)
        controls.addWidget(self.search)

        self.btn_clean = QPushButton(t("duplicate_clean"))
        controls.addWidget(self.btn_clean)

        root.addLayout(controls)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([t("col_path"), t("col_size"), t("col_count")])
        self.tree.setColumnCount(3)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.setMinimumHeight(320)
        root.addWidget(self.tree, 1)

    def retranslate(self) -> None:
        self._header.setText(t("duplicate_finder"))
        self.card_groups.set_label(t("duplicate_groups"))
        self.card_wasted.set_label(t("duplicate_wasted"))
        self.btn_choose.setText(t("choose_folder"))
        self.btn_scan.setText(t("find_duplicates"))
        self.btn_clean.setText(t("duplicate_clean"))
        self.chk_dry_run.setText(t("duplicate_dry_run"))
        self._strategy_label.setText(t("duplicate_strategy"))
        self.cmb_strategy.setItemText(0, t("strategy_oldest"))
        self.cmb_strategy.setItemText(1, t("strategy_newest"))
        self.cmb_strategy.setItemText(2, t("strategy_shortest"))
        if not self._folder:
            self._folder_label.setText(t("no_folder"))
        self.tree.setHeaderLabels([t("col_path"), t("col_size"), t("col_count")])

    def _on_search(self, text: str) -> None:
        self._filter = text.lower()
        self._refresh_tree()

    def _pick_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, t("choose_folder"))
        if path:
            self._folder = path
            self._folder_label.setText(path)

    def selected_folder(self) -> str:
        return self._folder

    def selected_strategy(self) -> str:
        return self.cmb_strategy.currentData() or "oldest"

    def is_dry_run(self) -> bool:
        return self.chk_dry_run.isChecked()

    def set_groups(self, groups: list[dict]) -> None:
        self._groups = groups
        self.card_groups.set_value(str(len(groups)))
        wasted = sum(int(g.get("wasted", 0)) for g in groups)
        self.card_wasted.set_value(human_size(wasted))
        self._refresh_tree()

    def _refresh_tree(self) -> None:
        items = self._groups
        if self._filter:
            items = [
                g for g in items
                if any(self._filter in p.lower() for p in g.get("paths", []))
            ]
        self.tree.clear()
        for g in items:
            parent = QTreeWidgetItem([
                f"{g.get('digest', '')[:16]}…",
                human_size(int(g.get("size", 0))),
                str(len(g.get("paths", []))),
            ])
            for p in g.get("paths", []):
                child = QTreeWidgetItem([p, human_size(int(g.get("size", 0))), ""])
                child.setForeground(0, Qt.GlobalColor.lightGray)
                parent.addChild(child)
            self.tree.addTopLevelItem(parent)
            parent.setExpanded(False)
