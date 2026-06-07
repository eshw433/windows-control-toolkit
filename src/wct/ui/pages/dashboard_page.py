from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wct.core.i18n import t
from wct.ui.widgets.stat_card import StatCard
from wct.ui.widgets.sparkline import Sparkline


class DashboardPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._cpu_history: list[float] = []
        self._ram_history: list[float] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        self._header = QLabel(t("dashboard"))
        self._header.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        root.addWidget(self._header)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.card_net_apps = StatCard(t("active_apps"), "0", "#00d2ff")
        self.card_blocked = StatCard(t("blocked_today"), "0", "#e74c3c")
        self.card_new_apps = StatCard(t("new_detected"), "0", "#f39c12")
        self.card_files_sorted = StatCard(t("files_sorted"), "0", "#27ae60")

        for card in [self.card_net_apps, self.card_blocked, self.card_new_apps, self.card_files_sorted]:
            cards_layout.addWidget(card)

        root.addLayout(cards_layout)

        actions_frame = QFrame()
        actions_frame.setStyleSheet(
            "background-color: #16213e; border: 1px solid #0f3460; border-radius: 10px; padding: 12px;"
        )
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setSpacing(8)

        self._qa_label = QLabel(t("quick_actions"))
        self._qa_label.setStyleSheet("font-weight: 600; color: #8892b0; border: none;")
        actions_layout.addWidget(self._qa_label)
        actions_layout.addStretch()

        self.btn_preview_org = QPushButton(t("preview_org"))
        self.btn_preview_org.setObjectName("btnPrimary")
        actions_layout.addWidget(self.btn_preview_org)

        self.btn_run_cleanup = QPushButton(t("run_cleanup"))
        actions_layout.addWidget(self.btn_run_cleanup)

        root.addWidget(actions_frame)

        # Historical charts row
        charts_frame = QFrame()
        charts_frame.setStyleSheet(
            "background-color: #16213e; border: 1px solid #0f3460; border-radius: 10px; padding: 12px;"
        )
        charts_layout = QHBoxLayout(charts_frame)
        charts_layout.setSpacing(24)

        cpu_box = QVBoxLayout()
        self._cpu_chart_lbl = QLabel("CPU %")
        self._cpu_chart_lbl.setStyleSheet("color: #8892b0; font-size: 11px; border: none;")
        cpu_box.addWidget(self._cpu_chart_lbl)
        self._cpu_spark = Sparkline(color="#5cd0ff", fill=True, baseline=True)
        self._cpu_spark.setMinimumHeight(60)
        cpu_box.addWidget(self._cpu_spark)
        charts_layout.addLayout(cpu_box)

        ram_box = QVBoxLayout()
        self._ram_chart_lbl = QLabel("RAM %")
        self._ram_chart_lbl.setStyleSheet("color: #8892b0; font-size: 11px; border: none;")
        ram_box.addWidget(self._ram_chart_lbl)
        self._ram_spark = Sparkline(color="#4dd599", fill=True, baseline=True)
        self._ram_spark.setMinimumHeight(60)
        ram_box.addWidget(self._ram_spark)
        charts_layout.addLayout(ram_box)

        root.addWidget(charts_frame)

        self._events_label = QLabel(t("recent_events"))
        self._events_label.setStyleSheet("font-size: 15px; font-weight: 600; color: #e0e0e0;")
        root.addWidget(self._events_label)

        self.events_table = QTableWidget(0, 5)
        self.events_table.setHorizontalHeaderLabels([t("col_time"), "Module", "Severity", "Type", "Message"])
        self.events_table.setAlternatingRowColors(True)
        self.events_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.events_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.events_table.horizontalHeader().setStretchLastSection(True)
        self.events_table.verticalHeader().setVisible(False)
        self.events_table.setMinimumHeight(200)
        root.addWidget(self.events_table, stretch=1)

    def retranslate(self) -> None:
        self._header.setText(t("dashboard"))
        self.card_net_apps.set_label(t("active_apps"))
        self.card_blocked.set_label(t("blocked_today"))
        self.card_new_apps.set_label(t("new_detected"))
        self.card_files_sorted.set_label(t("files_sorted"))
        self._qa_label.setText(t("quick_actions"))
        self.btn_preview_org.setText(t("preview_org"))
        self.btn_run_cleanup.setText(t("run_cleanup"))
        self._events_label.setText(t("recent_events"))
        self.events_table.setHorizontalHeaderLabels([t("col_time"), "Module", "Severity", "Type", "Message"])

    def update_stats(self, *, net_apps: int = 0, blocked: int = 0, new_apps: int = 0,
                     files_sorted: int = 0) -> None:
        self.card_net_apps.set_value(str(net_apps))
        self.card_blocked.set_value(str(blocked))
        self.card_new_apps.set_value(str(new_apps))
        self.card_files_sorted.set_value(str(files_sorted))

    def set_events(self, events: list[dict]) -> None:
        self.events_table.setRowCount(0)
        for ev in events:
            row = self.events_table.rowCount()
            self.events_table.insertRow(row)
            self.events_table.setItem(row, 0, QTableWidgetItem(ev.get("timestamp", "")))
            self.events_table.setItem(row, 1, QTableWidgetItem(ev.get("module", "")))
            self.events_table.setItem(row, 2, QTableWidgetItem(ev.get("severity", "")))
            self.events_table.setItem(row, 3, QTableWidgetItem(ev.get("event_type", "")))
            self.events_table.setItem(row, 4, QTableWidgetItem(ev.get("title", "")))

    def push_cpu_sample(self, value: float) -> None:
        self._cpu_spark.append(value, max_points=60)
        self._cpu_chart_lbl.setText(f"CPU %  (avg {self._cpu_spark.average():.1f}%)")

    def push_ram_sample(self, value: float) -> None:
        self._ram_spark.append(value, max_points=60)
        self._ram_chart_lbl.setText(f"RAM %  (avg {self._ram_spark.average():.1f}%)")
