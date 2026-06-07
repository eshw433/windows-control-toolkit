from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wct.core.i18n import t


class AddRuleDialog(QDialog):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("add_rule"))
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Rule name")
        layout.addRow("Name:", self.name_input)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("C:\\path\\to\\app.exe")
        layout.addRow("App Path:", self.path_input)

        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["Outbound", "Inbound", "Both"])
        layout.addRow("Direction:", self.direction_combo)

        self.action_combo = QComboBox()
        self.action_combo.addItems(["Block", "Allow"])
        layout.addRow("Action:", self.action_combo)

        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["Any", "TCP", "UDP"])
        layout.addRow("Protocol:", self.protocol_combo)

        self.remote_addr_input = QLineEdit()
        self.remote_addr_input.setPlaceholderText("Optional: IP or range")
        layout.addRow("Remote Addr:", self.remote_addr_input)

        self.remote_port_input = QLineEdit()
        self.remote_port_input.setPlaceholderText("Optional: port")
        layout.addRow("Remote Port:", self.remote_port_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> dict:
        direction_map = {"Outbound": "out", "Inbound": "in", "Both": "both"}
        return {
            "name": self.name_input.text().strip(),
            "process_path": self.path_input.text().strip(),
            "direction": direction_map.get(self.direction_combo.currentText(), "out"),
            "action": self.action_combo.currentText().lower(),
            "protocol": self.protocol_combo.currentText().lower(),
            "remote_addr": self.remote_addr_input.text().strip(),
            "remote_port": self.remote_port_input.text().strip(),
        }


class FirewallRulesPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        header_row = QHBoxLayout()
        self._title = QLabel(t("firewall_rules"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        header_row.addWidget(self._title)
        header_row.addStretch()

        self.btn_add_rule = QPushButton(t("add_rule"))
        self.btn_add_rule.setObjectName("btnPrimary")
        header_row.addWidget(self.btn_add_rule)

        root.addLayout(header_row)

        self.table = QTableWidget(0, 8)
        self._fw_headers = ["col_name", "", "col_direction", "col_action", "col_protocol", "", "col_enabled", "col_time"]
        self.table.setHorizontalHeaderLabels(self._get_fw_labels())
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(1, 220)
        root.addWidget(self.table, stretch=1)

        bottom = QHBoxLayout()
        bottom.addStretch()
        self.btn_toggle = QPushButton(t("toggle"))
        bottom.addWidget(self.btn_toggle)
        self.btn_delete = QPushButton(t("delete"))
        self.btn_delete.setObjectName("btnDanger")
        bottom.addWidget(self.btn_delete)
        root.addLayout(bottom)

    def _get_fw_labels(self) -> list[str]:
        fixed = {1: "App Path", 5: "Remote"}
        return [fixed.get(i, t(k)) if k else fixed.get(i, "") for i, k in enumerate(self._fw_headers)]

    def retranslate(self) -> None:
        self._title.setText(t("firewall_rules"))
        self.btn_add_rule.setText(t("add_rule"))
        self.btn_toggle.setText(t("toggle"))
        self.btn_delete.setText(t("delete"))
        self.table.setHorizontalHeaderLabels(self._get_fw_labels())

    def set_rules(self, rules: list[dict]) -> None:
        self.table.setRowCount(0)
        for r in rules:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r.get("name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(r.get("process_path", "")))
            self.table.setItem(row, 2, QTableWidgetItem(r.get("direction", "")))

            action_item = QTableWidgetItem(r.get("action", ""))
            if r.get("action") == "block":
                action_item.setForeground(Qt.GlobalColor.red)
            else:
                action_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 3, action_item)

            self.table.setItem(row, 4, QTableWidgetItem(r.get("protocol", "")))
            remote = f"{r.get('remote_addr', '')}:{r.get('remote_port', '')}".strip(":")
            self.table.setItem(row, 5, QTableWidgetItem(remote))
            self.table.setItem(row, 6, QTableWidgetItem("Yes" if r.get("enabled") else "No"))
            self.table.setItem(row, 7, QTableWidgetItem(r.get("created_at", "")))
