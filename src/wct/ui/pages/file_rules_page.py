from __future__ import annotations

import json

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wct.core.i18n import t


class AddFileRuleDialog(QDialog):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add File Rule")
        self.setMinimumWidth(460)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Rule name")
        layout.addRow("Name:", self.name_input)

        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 9999)
        self.priority_spin.setValue(100)
        layout.addRow("Priority:", self.priority_spin)

        # Condition fields
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText(".pdf, .docx")
        layout.addRow("Extensions:", self.ext_input)

        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("invoice, receipt, ...")
        layout.addRow("Filename contains:", self.pattern_input)

        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(0, 999999)
        self.min_size_spin.setSuffix(" MB")
        layout.addRow("Min size:", self.min_size_spin)

        self.max_age_spin = QSpinBox()
        self.max_age_spin.setRange(0, 9999)
        self.max_age_spin.setSuffix(" days")
        layout.addRow("Older than:", self.max_age_spin)

        # Action fields
        self.action_combo = QComboBox()
        self.action_combo.addItems(["Move", "Rename", "Quarantine", "Delete to Recycle Bin", "Ignore"])
        layout.addRow("Action:", self.action_combo)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Target subfolder name or full path")
        layout.addRow("Target:", self.target_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> dict:
        extensions = [e.strip() for e in self.ext_input.text().split(",") if e.strip()]
        condition: dict = {}
        if extensions:
            condition["extensions"] = extensions
        if self.pattern_input.text().strip():
            condition["filename_contains"] = self.pattern_input.text().strip()
        if self.min_size_spin.value() > 0:
            condition["min_size_mb"] = self.min_size_spin.value()
        if self.max_age_spin.value() > 0:
            condition["older_than_days"] = self.max_age_spin.value()

        action_map = {
            "Move": "move",
            "Rename": "rename",
            "Quarantine": "quarantine",
            "Delete to Recycle Bin": "delete",
            "Ignore": "ignore",
        }

        return {
            "name": self.name_input.text().strip(),
            "priority": self.priority_spin.value(),
            "condition_json": condition,
            "action_json": {
                "type": action_map.get(self.action_combo.currentText(), "move"),
                "target": self.target_input.text().strip(),
            },
        }


class FileRulesPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        header_row = QHBoxLayout()
        self._title = QLabel(t("file_rules"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        header_row.addWidget(self._title)
        header_row.addStretch()

        self.btn_add = QPushButton(t("add_rule"))
        self.btn_add.setObjectName("btnPrimary")
        header_row.addWidget(self.btn_add)

        root.addLayout(header_row)

        self.table = QTableWidget(0, 6)
        self._fr_headers = ["", "col_name", "", "col_action", "col_enabled", "col_time"]
        self.table.setHorizontalHeaderLabels(self._get_fr_labels())
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 250)
        self.table.setColumnWidth(3, 140)
        root.addWidget(self.table, stretch=1)

        bottom = QHBoxLayout()
        bottom.addStretch()
        self.btn_toggle = QPushButton(t("toggle"))
        bottom.addWidget(self.btn_toggle)
        self.btn_delete = QPushButton(t("delete"))
        self.btn_delete.setObjectName("btnDanger")
        bottom.addWidget(self.btn_delete)
        root.addLayout(bottom)

        self._drop_hint = QLabel(t("drop_files_hint"))
        self._drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_hint.setStyleSheet("color: #3c4a66; font-size: 11px; padding: 4px; border: none;")
        root.addWidget(self._drop_hint)

    def _get_fr_labels(self) -> list[str]:
        fixed = {0: "Priority", 2: "Conditions"}
        return [fixed.get(i, t(k)) if k else fixed.get(i, "") for i, k in enumerate(self._fr_headers)]

    def retranslate(self) -> None:
        self._title.setText(t("file_rules"))
        self.btn_add.setText(t("add_rule"))
        self.btn_toggle.setText(t("toggle"))
        self.btn_delete.setText(t("delete"))
        self._drop_hint.setText(t("drop_files_hint"))
        self.table.setHorizontalHeaderLabels(self._get_fr_labels())

    def set_rules(self, rules: list[dict]) -> None:
        self.table.setRowCount(0)
        for r in rules:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r.get("priority", 100))))
            self.table.setItem(row, 1, QTableWidgetItem(r.get("name", "")))
            cond = r.get("condition_json", {})
            self.table.setItem(row, 2, QTableWidgetItem(
                json.dumps(cond, ensure_ascii=False) if isinstance(cond, dict) else str(cond)
            ))
            act = r.get("action_json", {})
            self.table.setItem(row, 3, QTableWidgetItem(
                json.dumps(act, ensure_ascii=False) if isinstance(act, dict) else str(act)
            ))
            self.table.setItem(row, 4, QTableWidgetItem("Yes" if r.get("enabled") else "No"))
            self.table.setItem(row, 5, QTableWidgetItem(r.get("created_at", "")))


    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if not path:
                continue
            import os
            ext = os.path.splitext(path)[1].lower()
            dlg = AddFileRuleDialog(self)
            dlg.ext_input.setText(ext)
            dlg.target_input.setText(path if os.path.isdir(path) else os.path.dirname(path))
            dlg.exec()
