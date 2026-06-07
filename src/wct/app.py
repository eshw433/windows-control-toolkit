from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox

from loguru import logger

from wct.config.paths import AppPaths
from wct.config.settings import AppSettings
from wct.core.event_bus import EventBus
from wct.core.commands import CommandHistory
from wct.core.scheduler import Scheduler
from wct.db.database import Database
from wct.db.repositories import (
    BandwidthRepository,
    DnsHistoryRepository,
    DuplicateRepository,
    EventRepository,
    FileActionRepository,
    FileRuleRepository,
    FirewallRuleRepository,
    FolderProfileRepository,
    NetworkConnectionRepository,
    NotificationRepository,
    ProcessIdentityRepository,
    QuarantineRepository,
    RuleTemplateRepository,
    ScanHistoryRepository,
    SettingsKeyValueRepository,
    TrustDecisionRepository,
)
from wct.modules.network.service import NetworkService
from wct.modules.network.firewall_adapter import FirewallAdapter, is_admin
from wct.modules.network.bandwidth_service import BandwidthService
from wct.modules.files.service import FileService
from wct.modules.files.dedupe_pro import find_duplicates_pro, remove_duplicates
from wct.modules.files.size_analyzer import analyze
from wct.modules.files.templates import BUILTIN_TEMPLATES, apply_to_rule_repo
from wct.core.tray import TrayService
from wct.ui.main_window import MainWindow
from wct.ui.pages.firewall_rules_page import AddRuleDialog
from wct.ui.pages.file_rules_page import AddFileRuleDialog


class Application:
    """Top-level application object that owns all subsystems."""

    def __init__(self) -> None:
        # Config
        self.settings = AppSettings.load()

        # Database
        self.db = Database()
        self.db.open()

        # Repositories
        self.events_repo = EventRepository(self.db)
        self.notifications_repo = NotificationRepository(self.db)
        self.process_repo = ProcessIdentityRepository(self.db)
        self.connections_repo = NetworkConnectionRepository(self.db)
        self.firewall_repo = FirewallRuleRepository(self.db)
        self.file_actions_repo = FileActionRepository(self.db)
        self.file_rules_repo = FileRuleRepository(self.db)
        self.quarantine_repo = QuarantineRepository(self.db)
        self.bandwidth_repo = BandwidthRepository(self.db)
        self.trust_repo = TrustDecisionRepository(self.db)
        self.dns_repo = DnsHistoryRepository(self.db)
        self.dup_repo = DuplicateRepository(self.db)
        self.folder_profile_repo = FolderProfileRepository(self.db)
        self.template_repo = RuleTemplateRepository(self.db)
        self.scan_repo = ScanHistoryRepository(self.db)
        self.kv_repo = SettingsKeyValueRepository(self.db)

        # Core services
        self.command_history = CommandHistory()
        self.scheduler = Scheduler()

        # UI
        self.window = MainWindow(self.settings)

        self.tray = TrayService(self)

        # Wire scheduler page with the scheduler instance
        self.window.scheduler_page.set_scheduler(self.scheduler)

        # Module services
        self.bandwidth_service = BandwidthService(
            self.bandwidth_repo, self.events_repo, self.process_repo,
        )
        self.network_service = NetworkService(
            settings=self.settings,
            process_repo=self.process_repo,
            conn_repo=self.connections_repo,
            events_repo=self.events_repo,
            notif_repo=self.notifications_repo,
        )

        self.file_service = FileService(
            settings=self.settings,
            file_rules_repo=self.file_rules_repo,
            file_actions_repo=self.file_actions_repo,
            quarantine_repo=self.quarantine_repo,
            events_repo=self.events_repo,
            notif_repo=self.notifications_repo,
        )

        # Wire initial data into UI
        self._load_initial_data()

        # Connect UI signals
        self._connect_signals()

        # Start background services
        self.network_service.start()
        self.file_service.start_monitoring()
        self.bandwidth_service.start()

        # Log app event
        self.events_repo.insert(
            module="system",
            severity="info",
            event_type="app_start",
            title="Application started",
        )
        logger.info("Application initialised")

    # -- initial data load ---------------------------------------------------

    def _load_initial_data(self) -> None:
        events = self.events_repo.recent(limit=50)
        self.window.dashboard_page.set_events(events)

        fw_rules = self.firewall_repo.get_all()
        self.window.firewall_page.set_rules(fw_rules)

        file_rules = self.file_rules_repo.get_all()
        self.window.file_rules_page.set_rules(file_rules)

        actions = self.file_actions_repo.recent(limit=100)
        self.window.history_page.set_actions(actions)

        notifs = self.notifications_repo.unread()
        self.window.notifications_page.set_notifications(notifs)

        self._refresh_quarantine()
        self._refresh_trust()
        self._refresh_risk()

    # -- signal wiring -------------------------------------------------------

    def _connect_signals(self) -> None:
        w = self.window

        # Network worker -> network page
        self.network_service.worker.connections_ready.connect(
            w.network_page.set_connections
        )

        # Network page buttons
        w.network_page.btn_pause.clicked.connect(self._toggle_net_pause)
        w.network_page.btn_block.clicked.connect(self._block_selected_app)
        w.network_page.btn_allow.clicked.connect(self._allow_selected_app)
        w.network_page.table.currentCellChanged.connect(self._on_net_row_changed)

        # Firewall page buttons
        w.firewall_page.btn_add_rule.clicked.connect(self._add_firewall_rule)
        w.firewall_page.btn_delete.clicked.connect(self._delete_firewall_rule)
        w.firewall_page.btn_toggle.clicked.connect(self._toggle_firewall_rule)

        # Downloads page
        w.downloads_page.btn_scan.clicked.connect(self._scan_downloads)
        w.downloads_page.btn_apply_all.clicked.connect(self._apply_all_file_actions)
        w.downloads_page.btn_apply_selected.clicked.connect(self._apply_selected_file_actions)
        self.file_service.scan_complete.connect(w.downloads_page.set_planned_actions)

        # File rules page
        w.file_rules_page.btn_add.clicked.connect(self._add_file_rule)
        w.file_rules_page.btn_delete.clicked.connect(self._delete_file_rule)
        w.file_rules_page.btn_toggle.clicked.connect(self._toggle_file_rule)

        # History page
        w.history_page.btn_rollback.clicked.connect(self._rollback_selected)

        # Dashboard quick actions
        w.dashboard_page.btn_preview_org.clicked.connect(self._scan_downloads)
        w.dashboard_page.btn_run_cleanup.clicked.connect(self._apply_all_file_actions)

        # Notifications
        w.notifications_page.btn_mark_all_read.clicked.connect(self._mark_all_read)

        # Bandwidth page
        self.bandwidth_service.tick.connect(self._on_bandwidth_tick)
        w.bandwidth_page.btn_reset.clicked.connect(self._reset_bandwidth)

        # Quarantine page
        w.quarantine_page.btn_restore.clicked.connect(self._quarantine_restore)
        w.quarantine_page.btn_purge.clicked.connect(self._quarantine_purge)
        w.quarantine_page.btn_clean_expired.clicked.connect(self._quarantine_clean_expired)

        # Duplicates page
        w.duplicates_page.btn_scan.clicked.connect(self._duplicates_scan)
        w.duplicates_page.btn_clean.clicked.connect(self._duplicates_clean)

        # Disk hogs page
        w.disk_hogs_page.btn_scan.clicked.connect(self._disk_hogs_scan)

        # Trust page
        w.trust_page.btn_remove.clicked.connect(self._trust_remove_selected)

        # Risk page
        w.risk_page.btn_block.clicked.connect(self._risk_block_selected)
        w.risk_page.btn_trust.clicked.connect(self._risk_trust_selected)

        # Dashboard live CPU/RAM feed via scheduler
        self.scheduler.register("dashboard_sysinfo", self._push_dashboard_sysinfo, 3000)
        self.scheduler.get("dashboard_sysinfo").start()

    # -- network handlers ----------------------------------------------------

    _net_paused = False

    def _toggle_net_pause(self) -> None:
        from wct.core.i18n import t
        if self._net_paused:
            self.network_service.resume()
            self.window.network_page.btn_pause.setText(t("pause"))
        else:
            self.network_service.pause()
            self.window.network_page.btn_pause.setText(t("resume"))
        self._net_paused = not self._net_paused

    def _on_net_row_changed(self, row: int, _col: int, _prev_row: int, _prev_col: int) -> None:
        table = self.window.network_page.table
        if row < 0:
            return
        app = table.item(row, 0)
        pid = table.item(row, 1)
        trust = table.item(row, 2)
        ip = table.item(row, 3)
        domain = table.item(row, 6)
        text = (
            f"App: {app.text() if app else ''}\n"
            f"PID: {pid.text() if pid else ''}\n"
            f"Trust: {trust.text() if trust else ''}\n"
            f"Remote IP: {ip.text() if ip else ''}\n"
            f"Domain: {domain.text() if domain else ''}\n"
        )
        self.window.network_page.show_details(text)

    def _block_selected_app(self) -> None:
        row = self.window.network_page.table.currentRow()
        if row < 0:
            return
        app_name = self.window.network_page.table.item(row, 0)
        if not app_name:
            return
        proc = self.process_repo.find_by_path(
            self._get_exe_path_from_row(row) or ""
        )
        if proc:
            self.process_repo.set_trust(proc["id"], "blocked")
            self._refresh_network_data()
        self.window.set_status(f"Blocked: {app_name.text()}")

    def _allow_selected_app(self) -> None:
        row = self.window.network_page.table.currentRow()
        if row < 0:
            return
        app_name = self.window.network_page.table.item(row, 0)
        if not app_name:
            return
        proc = self.process_repo.find_by_path(
            self._get_exe_path_from_row(row) or ""
        )
        if proc:
            self.process_repo.set_trust(proc["id"], "allowed")
            self._refresh_network_data()
        self.window.set_status(f"Allowed: {app_name.text()}")

    def _get_exe_path_from_row(self, row: int) -> str | None:
        table = self.window.network_page.table
        name_item = table.item(row, 0)
        if name_item:
            proc = self.process_repo.find_by_path(name_item.text())
            if not proc:
                procs = self.process_repo.get_all()
                for p in procs:
                    if p["exe_name"] == name_item.text():
                        return p["exe_path"]
        return None

    def _refresh_network_data(self) -> None:
        recent = self.connections_repo.recent(limit=200)
        self.window.network_page.set_connections(recent)

    # -- firewall handlers ---------------------------------------------------

    def _add_firewall_rule(self) -> None:
        dlg = AddRuleDialog(self.window)
        if dlg.exec():
            data = dlg.get_data()
            if not data.get("name") or not data.get("process_path"):
                return
            rule_id = self.firewall_repo.insert(**data)
            ext_name = FirewallAdapter.generate_rule_name(
                data["action"], data["direction"], data["process_path"], rule_id,
            )
            if is_admin():
                ok = FirewallAdapter.create_rule(
                    name=ext_name,
                    exe_path=data["process_path"],
                    direction=data["direction"],
                    action=data["action"],
                    protocol=data["protocol"],
                    remote_addr=data.get("remote_addr", ""),
                    remote_port=data.get("remote_port", ""),
                )
                if ok:
                    self.window.set_status(f"Firewall rule created: {data['name']}")
                else:
                    self.window.set_status("Failed to create Windows Firewall rule")
            else:
                self.window.set_status("Rule saved locally (admin required to apply to Windows Firewall)")

            self.window.firewall_page.set_rules(self.firewall_repo.get_all())

    def _delete_firewall_rule(self) -> None:
        row = self.window.firewall_page.table.currentRow()
        if row < 0:
            return
        rules = self.firewall_repo.get_all()
        if row < len(rules):
            rule = rules[row]
            if rule.get("external_rule_name") and is_admin():
                FirewallAdapter.delete_rule(rule["external_rule_name"])
            self.firewall_repo.delete(rule["id"])
            self.window.firewall_page.set_rules(self.firewall_repo.get_all())
            self.window.set_status(f"Rule deleted: {rule['name']}")

    def _toggle_firewall_rule(self) -> None:
        row = self.window.firewall_page.table.currentRow()
        if row < 0:
            return
        rules = self.firewall_repo.get_all()
        if row < len(rules):
            rule = rules[row]
            new_state = not bool(rule.get("enabled"))
            self.firewall_repo.toggle(rule["id"], new_state)
            self.window.firewall_page.set_rules(self.firewall_repo.get_all())

    # -- file handlers -------------------------------------------------------

    def _scan_downloads(self) -> None:
        from wct.core.i18n import t
        self.window.downloads_page.set_status(t("scanning"), "#f39c12")
        folder = self.window.downloads_page.get_selected_folder()
        folders = [folder] if folder else None
        results = self.file_service.scan_now(folders)
        self.window.downloads_page.set_status(f"{len(results)} files", "#27ae60")
        self.window.set_status(f"Scan complete: {len(results)} files found")

    def _apply_all_file_actions(self) -> None:
        count = self.file_service.apply_all()
        self.window.downloads_page.set_status(f"Applied {count} actions", "#27ae60")
        self.window.downloads_page.set_planned_actions([])
        self._refresh_history()
        self.window.set_status(f"Applied {count} file actions")

    def _apply_selected_file_actions(self) -> None:
        rows = set(idx.row() for idx in self.window.downloads_page.table.selectedIndexes())
        if not rows:
            return
        count = self.file_service.apply_selected(sorted(rows))
        self._scan_downloads()
        self._refresh_history()
        self.window.set_status(f"Applied {count} selected actions")

    def _add_file_rule(self) -> None:
        dlg = AddFileRuleDialog(self.window)
        if dlg.exec():
            data = dlg.get_data()
            if not data.get("name"):
                return
            self.file_rules_repo.insert(
                name=data["name"],
                condition_json=data["condition_json"],
                action_json=data["action_json"],
                priority=data.get("priority", 100),
            )
            self.file_service.reload_rules()
            self.window.file_rules_page.set_rules(self.file_rules_repo.get_all())
            self.window.set_status(f"File rule added: {data['name']}")

    def _delete_file_rule(self) -> None:
        row = self.window.file_rules_page.table.currentRow()
        if row < 0:
            return
        rules = self.file_rules_repo.get_all()
        if row < len(rules):
            self.file_rules_repo.delete(rules[row]["id"])
            self.file_service.reload_rules()
            self.window.file_rules_page.set_rules(self.file_rules_repo.get_all())

    def _toggle_file_rule(self) -> None:
        row = self.window.file_rules_page.table.currentRow()
        if row < 0:
            return
        rules = self.file_rules_repo.get_all()
        if row < len(rules):
            rule = rules[row]
            self.file_rules_repo.toggle(rule["id"], not bool(rule.get("enabled")))
            self.file_service.reload_rules()
            self.window.file_rules_page.set_rules(self.file_rules_repo.get_all())

    # -- history handlers ----------------------------------------------------

    def _rollback_selected(self) -> None:
        row = self.window.history_page.table.currentRow()
        if row < 0:
            return
        actions = self.file_actions_repo.recent(limit=200)
        if row < len(actions):
            action = actions[row]
            ok = self.file_service.rollback_action(action["id"])
            if ok:
                self.window.set_status("Rollback successful")
            else:
                self.window.set_status("Rollback failed")
            self._refresh_history()

    def _refresh_history(self) -> None:
        actions = self.file_actions_repo.recent(limit=100)
        self.window.history_page.set_actions(actions)

    # -- notifications -------------------------------------------------------

    def _mark_all_read(self) -> None:
        for n in self.notifications_repo.unread():
            self.notifications_repo.mark_read(n["id"])
        self.window.notifications_page.set_notifications([])
        self.window.set_status("All notifications marked as read")

    # -- bandwidth handlers --------------------------------------------------

    def _on_bandwidth_tick(self, payload: dict) -> None:
        page = self.window.bandwidth_page
        page.update_totals(
            sent=int(payload.get("total_sent", 0)),
            recv=int(payload.get("total_recv", 0)),
            rate_sent=float(payload.get("rate_sent", 0.0)),
            rate_recv=float(payload.get("rate_recv", 0.0)),
        )
        page.update_rows(payload.get("rows", []))

    def _reset_bandwidth(self) -> None:
        self.bandwidth_service.reset()
        self.window.bandwidth_page.clear_charts()
        self.window.set_status("Bandwidth counters reset")

    # -- quarantine handlers -------------------------------------------------

    def _refresh_quarantine(self) -> None:
        rows = self.quarantine_repo.all()
        self.window.quarantine_page.update_rows(rows)

    def _quarantine_restore(self) -> None:
        ids = self.window.quarantine_page.selected_ids()
        for qid in ids:
            self.file_service.restore_quarantine(qid)
        self._refresh_quarantine()
        self._refresh_history()
        self.window.set_status(f"Restored {len(ids)} item(s)")

    def _quarantine_purge(self) -> None:
        ids = self.window.quarantine_page.selected_ids()
        for qid in ids:
            self.file_service.purge_quarantine(qid)
        self._refresh_quarantine()
        self.window.set_status(f"Purged {len(ids)} item(s)")

    def _quarantine_clean_expired(self) -> None:
        removed = self.file_service.purge_expired_quarantine()
        self._refresh_quarantine()
        self.window.set_status(f"Cleaned {removed} expired item(s)")

    # -- duplicates / hogs handlers ------------------------------------------

    def _duplicates_scan(self) -> None:
        from pathlib import Path
        folder = self.window.duplicates_page.selected_folder()
        if not folder:
            self.window.set_status("Choose a folder first")
            return
        groups = find_duplicates_pro(Path(folder), recursive=True, min_size=4096)
        payload = [
            {
                "digest": g.digest,
                "size": g.size_each,
                "wasted": g.wasted_bytes,
                "paths": [str(p) for p in g.paths],
            }
            for g in groups
        ]
        self.window.duplicates_page.set_groups(payload)
        self.window.set_status(f"Found {len(groups)} duplicate groups")

    def _duplicates_clean(self) -> None:
        from pathlib import Path
        folder = self.window.duplicates_page.selected_folder()
        if not folder:
            return
        groups = find_duplicates_pro(Path(folder), recursive=True, min_size=4096)
        result = remove_duplicates(
            groups,
            strategy=self.window.duplicates_page.selected_strategy(),
            dry_run=self.window.duplicates_page.is_dry_run(),
        )
        self.window.set_status(
            f"Cleanup: {len(result['removed'])} removed, freed {result['freed']} bytes (dry_run={result['dry_run']})"
        )

    def _disk_hogs_scan(self) -> None:
        from pathlib import Path
        folder = self.window.disk_hogs_page.selected_folder()
        if not folder:
            self.window.set_status("Choose a folder first")
            return
        report = analyze(Path(folder), recursive=True)
        entries = report["largest"]
        mode = self.window.disk_hogs_page.selected_mode()
        if mode == "oldest":
            entries = report["oldest"]
        elif mode == "stale":
            entries = report["stale"]
        elif mode == "huge":
            entries = report["huge"]
        elif mode == "zero":
            entries = report["zero_byte"]
        rows = [
            {
                "path": str(e.path),
                "size": e.size,
                "mtime": e.mtime,
                "extension": e.extension,
                "category": e.category,
            }
            for e in entries
        ]
        self.window.disk_hogs_page.set_summary(
            total_files=report["total_files"],
            total_size=report["total_size"],
            huge=len(report["huge"]),
            stale=len(report["stale"]),
        )
        self.window.disk_hogs_page.set_entries(rows)
        self.window.set_status(f"Analyzed {report['total_files']} files")

    # -- trust handlers ------------------------------------------------------

    def _refresh_trust(self) -> None:
        rows = self.trust_repo.recent(limit=300)
        for r in rows:
            proc = self.process_repo.find_by_id(r.get("process_id", 0))
            if proc:
                r["exe_name"] = proc.get("exe_name", "")
                r["exe_path"] = proc.get("exe_path", "")
        self.window.trust_page.update_rows(rows)

    def _trust_remove_selected(self) -> None:
        ids = self.window.trust_page.selected_ids()
        for tid in ids:
            self.trust_repo.delete(tid)
        self._refresh_trust()
        self.window.set_status(f"Removed {len(ids)} trust decision(s)")

    # -- risk handlers -------------------------------------------------------

    def _refresh_risk(self) -> None:
        procs = self.process_repo.get_all()
        for p in procs:
            if p.get("risk_score", 0) == 0:
                p["risk_level"] = "low"
        self.window.risk_page.update_rows(procs)

    def _risk_block_selected(self) -> None:
        row = self.window.risk_page.table.currentRow()
        if row < 0:
            return
        item = self.window.risk_page.table.item(row, 1)
        if not item:
            return
        proc = self.process_repo.find_by_path(item.text())
        if proc:
            self.process_repo.set_trust(proc["id"], "blocked")
            self.trust_repo.insert(proc["id"], "blocked", scope="any",
                                   reason="Set via Risk page")
        self._refresh_risk()
        self._refresh_trust()

    def _risk_trust_selected(self) -> None:
        row = self.window.risk_page.table.currentRow()
        if row < 0:
            return
        item = self.window.risk_page.table.item(row, 1)
        if not item:
            return
        proc = self.process_repo.find_by_path(item.text())
        if proc:
            self.process_repo.set_trust(proc["id"], "allowed")
            self.trust_repo.insert(proc["id"], "allowed", scope="any",
                                   reason="Set via Risk page")
        self._refresh_risk()
        self._refresh_trust()

    def _push_dashboard_sysinfo(self) -> None:
        from wct.core.sysinfo import memory_usage_percent
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=None)  # non-blocking
            ram = memory_usage_percent()
            self.window.dashboard_page.push_cpu_sample(cpu)
            self.window.dashboard_page.push_ram_sample(ram)
        except Exception:
            pass

    # -- lifecycle -----------------------------------------------------------

    def _on_welcome_done(self) -> None:
        if hasattr(self, "_welcome"):
            self._welcome.close()
        if hasattr(self.kv_repo, "set"):
            self.kv_repo.set("first_run_done", "1")

    def show(self) -> None:
        self.window.show()

    def shutdown(self) -> None:
        self.network_service.stop()
        self.file_service.stop_monitoring()
        self.bandwidth_service.stop()
        self.scheduler.stop_all()
        self.tray.shutdown()
        self.events_repo.insert(
            module="system",
            severity="info",
            event_type="app_stop",
            title="Application stopped",
        )
        self.db.close()
        logger.info("Application shutdown complete")
