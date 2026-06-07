from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from wct.db.database import Database


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _rows(rows) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]


class EventRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def insert(self, module: str, severity: str, event_type: str, title: str,
               message: str = "", metadata: dict | None = None) -> int:
        cur = self._db.execute(
            "INSERT INTO app_events (timestamp, module, severity, event_type, title, message, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (_now(), module, severity, event_type, title, message, json.dumps(metadata or {})),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM app_events ORDER BY timestamp DESC LIMIT ?", (limit,),
        ))

    def by_module(self, module: str, limit: int = 100) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM app_events WHERE module=? ORDER BY timestamp DESC LIMIT ?",
            (module, limit),
        ))

    def by_severity(self, severity: str, limit: int = 100) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM app_events WHERE severity=? ORDER BY timestamp DESC LIMIT ?",
            (severity, limit),
        ))

    def search(self, query: str, limit: int = 200) -> list[dict[str, Any]]:
        like = f"%{query}%"
        return _rows(self._db.fetchall(
            "SELECT * FROM app_events WHERE title LIKE ? OR message LIKE ? OR event_type LIKE ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (like, like, like, limit),
        ))

    def count_today(self, module: str | None = None) -> int:
        if module:
            row = self._db.fetchone(
                "SELECT COUNT(*) FROM app_events WHERE module=? AND timestamp>=?",
                (module, _today() + "T00:00:00.000Z"),
            )
        else:
            row = self._db.fetchone(
                "SELECT COUNT(*) FROM app_events WHERE timestamp>=?",
                (_today() + "T00:00:00.000Z",),
            )
        return int(row[0]) if row else 0

    def purge_older_than(self, days: int) -> int:
        cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
        cutoff_iso = datetime.fromtimestamp(cutoff, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        cur = self._db.execute("DELETE FROM app_events WHERE timestamp < ?", (cutoff_iso,))
        self._db.commit()
        return cur.rowcount


class NotificationRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def insert(self, module: str, title: str, body: str = "", action: dict | None = None) -> int:
        cur = self._db.execute(
            "INSERT INTO notifications (timestamp, module, title, body, action_json) VALUES (?, ?, ?, ?, ?)",
            (_now(), module, title, body, json.dumps(action or {})),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def unread(self) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM notifications WHERE status='unread' ORDER BY timestamp DESC",
        ))

    def all(self, limit: int = 500) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM notifications ORDER BY timestamp DESC LIMIT ?", (limit,),
        ))

    def mark_read(self, notif_id: int) -> None:
        self._db.execute("UPDATE notifications SET status='read' WHERE id=?", (notif_id,))
        self._db.commit()

    def mark_all_read(self) -> int:
        cur = self._db.execute("UPDATE notifications SET status='read' WHERE status='unread'")
        self._db.commit()
        return cur.rowcount

    def dismiss(self, notif_id: int) -> None:
        self._db.execute("UPDATE notifications SET status='dismissed' WHERE id=?", (notif_id,))
        self._db.commit()

    def clear_dismissed(self) -> int:
        cur = self._db.execute("DELETE FROM notifications WHERE status='dismissed'")
        self._db.commit()
        return cur.rowcount

    def unread_count(self) -> int:
        row = self._db.fetchone("SELECT COUNT(*) FROM notifications WHERE status='unread'")
        return int(row[0]) if row else 0


class ProcessIdentityRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def upsert(self, exe_path: str, exe_name: str, publisher: str = "",
               file_hash: str = "") -> int:
        row = self._db.fetchone(
            "SELECT id FROM process_identities WHERE exe_path = ?", (exe_path,),
        )
        now = _now()
        if row:
            self._db.execute(
                "UPDATE process_identities SET last_seen=?, "
                "publisher=COALESCE(NULLIF(?,''), publisher), "
                "file_hash=COALESCE(NULLIF(?,''), file_hash) WHERE id=?",
                (now, publisher, file_hash, row["id"]),
            )
            self._db.commit()
            return row["id"]
        cur = self._db.execute(
            "INSERT INTO process_identities (exe_path, exe_name, publisher, file_hash, first_seen, last_seen) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (exe_path, exe_name, publisher, file_hash, now, now),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_all(self) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM process_identities ORDER BY last_seen DESC"
        ))

    def get(self, proc_id: int) -> dict[str, Any] | None:
        row = self._db.fetchone(
            "SELECT * FROM process_identities WHERE id=?", (proc_id,),
        )
        return dict(row) if row else None

    def set_trust(self, proc_id: int, state: str) -> None:
        self._db.execute(
            "UPDATE process_identities SET trust_state=? WHERE id=?",
            (state, proc_id),
        )
        self._db.commit()

    def set_risk(self, proc_id: int, score: int, level: str) -> None:
        self._db.execute(
            "UPDATE process_identities SET risk_score=?, risk_level=? WHERE id=?",
            (score, level, proc_id),
        )
        self._db.commit()

    def set_note(self, proc_id: int, note: str) -> None:
        self._db.execute(
            "UPDATE process_identities SET note=? WHERE id=?",
            (note, proc_id),
        )
        self._db.commit()

    def set_tags(self, proc_id: int, tags: list[str]) -> None:
        joined = ",".join(t.strip() for t in tags if t.strip())
        self._db.execute(
            "UPDATE process_identities SET tags=? WHERE id=?",
            (joined, proc_id),
        )
        self._db.commit()

    def find_by_path(self, exe_path: str) -> dict[str, Any] | None:
        row = self._db.fetchone(
            "SELECT * FROM process_identities WHERE exe_path=?", (exe_path,),
        )
        return dict(row) if row else None

    def find_by_id(self, proc_id: int) -> dict[str, Any] | None:
        row = self._db.fetchone(
            "SELECT * FROM process_identities WHERE id=?", (proc_id,),
        )
        return dict(row) if row else None

    def find_by_name(self, exe_name: str) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM process_identities WHERE exe_name=? ORDER BY last_seen DESC",
            (exe_name,),
        ))

    def by_trust(self, trust: str) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM process_identities WHERE trust_state=? ORDER BY last_seen DESC",
            (trust,),
        ))

    def by_risk_level(self, level: str) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM process_identities WHERE risk_level=? ORDER BY risk_score DESC",
            (level,),
        ))

    def count(self) -> int:
        row = self._db.fetchone("SELECT COUNT(*) FROM process_identities")
        return int(row[0]) if row else 0

    def search(self, query: str, limit: int = 200) -> list[dict[str, Any]]:
        like = f"%{query}%"
        return _rows(self._db.fetchall(
            "SELECT * FROM process_identities WHERE exe_name LIKE ? OR exe_path LIKE ? "
            "OR publisher LIKE ? ORDER BY last_seen DESC LIMIT ?",
            (like, like, like, limit),
        ))


class NetworkConnectionRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def insert(self, process_id: int, pid: int, local_addr: str, local_port: int,
               remote_addr: str, remote_port: int, protocol: str, status: str,
               remote_domain: str = "", asn: str = "", country: str = "",
               service_hint: str = "") -> int:
        cur = self._db.execute(
            "INSERT INTO network_connections "
            "(timestamp, process_id, pid, local_addr, local_port, remote_addr, remote_port, "
            "protocol, status, remote_domain, asn, country, service_hint) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (_now(), process_id, pid, local_addr, local_port, remote_addr, remote_port,
             protocol, status, remote_domain, asn, country, service_hint),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def insert_many(self, rows: list[tuple]) -> int:
        if not rows:
            return 0
        cur = self._db.executemany(
            "INSERT INTO network_connections "
            "(timestamp, process_id, pid, local_addr, local_port, remote_addr, remote_port, "
            "protocol, status, remote_domain, asn, country, service_hint) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        self._db.commit()
        return cur.rowcount

    def recent(self, limit: int = 200) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT nc.*, pi.exe_name, pi.exe_path, pi.trust_state, pi.risk_level "
            "FROM network_connections nc "
            "JOIN process_identities pi ON nc.process_id = pi.id "
            "ORDER BY nc.timestamp DESC LIMIT ?",
            (limit,),
        ))

    def for_process(self, process_id: int, limit: int = 200) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM network_connections WHERE process_id=? "
            "ORDER BY timestamp DESC LIMIT ?",
            (process_id, limit),
        ))

    def unique_remotes(self, process_id: int) -> int:
        row = self._db.fetchone(
            "SELECT COUNT(DISTINCT remote_addr) FROM network_connections WHERE process_id=?",
            (process_id,),
        )
        return int(row[0]) if row else 0

    def remotes_for(self, process_id: int, limit: int = 50) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT remote_addr, remote_port, remote_domain, country, "
            "COUNT(*) as hits, MAX(timestamp) as last_seen "
            "FROM network_connections WHERE process_id=? "
            "GROUP BY remote_addr, remote_port ORDER BY hits DESC LIMIT ?",
            (process_id, limit),
        ))

    def purge_older_than(self, days: int) -> int:
        cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
        cutoff_iso = datetime.fromtimestamp(cutoff, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        cur = self._db.execute("DELETE FROM network_connections WHERE timestamp < ?", (cutoff_iso,))
        self._db.commit()
        return cur.rowcount


class FirewallRuleRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def insert(self, name: str, process_path: str, direction: str = "out",
               action: str = "block", protocol: str = "any", remote_addr: str = "",
               remote_port: str = "", external_rule_name: str = "",
               note: str = "") -> int:
        cur = self._db.execute(
            "INSERT INTO firewall_rules "
            "(name, process_path, direction, action, protocol, remote_addr, remote_port, "
            "created_by_app, external_rule_name, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
            (name, process_path, direction, action, protocol, remote_addr, remote_port,
             external_rule_name, note),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_all(self) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM firewall_rules ORDER BY created_at DESC"
        ))

    def get(self, rule_id: int) -> dict[str, Any] | None:
        row = self._db.fetchone("SELECT * FROM firewall_rules WHERE id=?", (rule_id,))
        return dict(row) if row else None

    def delete(self, rule_id: int) -> None:
        self._db.execute("DELETE FROM firewall_rules WHERE id=?", (rule_id,))
        self._db.commit()

    def toggle(self, rule_id: int, enabled: bool) -> None:
        self._db.execute(
            "UPDATE firewall_rules SET enabled=? WHERE id=?",
            (int(enabled), rule_id),
        )
        self._db.commit()

    def update_note(self, rule_id: int, note: str) -> None:
        self._db.execute("UPDATE firewall_rules SET note=? WHERE id=?", (note, rule_id))
        self._db.commit()

    def by_process(self, process_path: str) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM firewall_rules WHERE process_path=? ORDER BY created_at DESC",
            (process_path,),
        ))

    def count(self) -> int:
        row = self._db.fetchone("SELECT COUNT(*) FROM firewall_rules")
        return int(row[0]) if row else 0

    def count_enabled(self) -> int:
        row = self._db.fetchone("SELECT COUNT(*) FROM firewall_rules WHERE enabled=1")
        return int(row[0]) if row else 0


class FileActionRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def insert(self, action_type: str, source_path: str, target_path: str = "",
               reversible: bool = True, rollback_json: dict | None = None,
               file_size: int = 0, rule_name: str = "") -> int:
        cur = self._db.execute(
            "INSERT INTO file_actions (timestamp, action_type, source_path, target_path, "
            "reversible, rollback_json, file_size, rule_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (_now(), action_type, source_path, target_path, int(reversible),
             json.dumps(rollback_json or {}), file_size, rule_name),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def mark_rolled_back(self, action_id: int) -> None:
        self._db.execute(
            "UPDATE file_actions SET status='rolled_back' WHERE id=?", (action_id,),
        )
        self._db.commit()

    def mark_failed(self, action_id: int, error: str) -> None:
        self._db.execute(
            "UPDATE file_actions SET status='failed', error_message=? WHERE id=?",
            (error, action_id),
        )
        self._db.commit()

    def recent(self, limit: int = 200) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM file_actions ORDER BY timestamp DESC LIMIT ?", (limit,),
        ))

    def get(self, action_id: int) -> dict[str, Any] | None:
        row = self._db.fetchone("SELECT * FROM file_actions WHERE id=?", (action_id,))
        return dict(row) if row else None

    def by_type(self, action_type: str, limit: int = 200) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM file_actions WHERE action_type=? ORDER BY timestamp DESC LIMIT ?",
            (action_type, limit),
        ))

    def by_status(self, status: str, limit: int = 200) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM file_actions WHERE status=? ORDER BY timestamp DESC LIMIT ?",
            (status, limit),
        ))

    def count_today(self) -> int:
        row = self._db.fetchone(
            "SELECT COUNT(*) FROM file_actions WHERE timestamp>=?",
            (_today() + "T00:00:00.000Z",),
        )
        return int(row[0]) if row else 0

    def total_size_processed(self) -> int:
        row = self._db.fetchone(
            "SELECT COALESCE(SUM(file_size),0) FROM file_actions WHERE status='completed'"
        )
        return int(row[0]) if row else 0


class FileRuleRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def insert(self, name: str, condition_json: dict, action_json: dict,
               priority: int = 100, folder_scope: str = "", note: str = "") -> int:
        now = _now()
        cur = self._db.execute(
            "INSERT INTO file_rules (name, priority, condition_json, action_json, "
            "folder_scope, note, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, priority, json.dumps(condition_json), json.dumps(action_json),
             folder_scope, note, now, now),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_enabled(self) -> list[dict[str, Any]]:
        rows = self._db.fetchall(
            "SELECT * FROM file_rules WHERE enabled=1 ORDER BY priority ASC",
        )
        return [_decode_rule(dict(r)) for r in rows]

    def get_all(self) -> list[dict[str, Any]]:
        rows = self._db.fetchall("SELECT * FROM file_rules ORDER BY priority ASC")
        return [_decode_rule(dict(r)) for r in rows]

    def get(self, rule_id: int) -> dict[str, Any] | None:
        row = self._db.fetchone("SELECT * FROM file_rules WHERE id=?", (rule_id,))
        return _decode_rule(dict(row)) if row else None

    def toggle(self, rule_id: int, enabled: bool) -> None:
        self._db.execute(
            "UPDATE file_rules SET enabled=?, updated_at=? WHERE id=?",
            (int(enabled), _now(), rule_id),
        )
        self._db.commit()

    def delete(self, rule_id: int) -> None:
        self._db.execute("DELETE FROM file_rules WHERE id=?", (rule_id,))
        self._db.commit()

    def update(self, rule_id: int, *, name: str | None = None,
               condition_json: dict | None = None,
               action_json: dict | None = None,
               priority: int | None = None,
               folder_scope: str | None = None,
               note: str | None = None) -> None:
        sets: list[str] = []
        vals: list[Any] = []
        if name is not None:
            sets.append("name=?"); vals.append(name)
        if condition_json is not None:
            sets.append("condition_json=?"); vals.append(json.dumps(condition_json))
        if action_json is not None:
            sets.append("action_json=?"); vals.append(json.dumps(action_json))
        if priority is not None:
            sets.append("priority=?"); vals.append(priority)
        if folder_scope is not None:
            sets.append("folder_scope=?"); vals.append(folder_scope)
        if note is not None:
            sets.append("note=?"); vals.append(note)
        if not sets:
            return
        sets.append("updated_at=?"); vals.append(_now())
        vals.append(rule_id)
        self._db.execute(
            f"UPDATE file_rules SET {', '.join(sets)} WHERE id=?",
            tuple(vals),
        )
        self._db.commit()

    def reorder(self, ordering: list[tuple[int, int]]) -> None:
        for rule_id, new_priority in ordering:
            self._db.execute(
                "UPDATE file_rules SET priority=?, updated_at=? WHERE id=?",
                (new_priority, _now(), rule_id),
            )
        self._db.commit()


def _decode_rule(d: dict[str, Any]) -> dict[str, Any]:
    for k in ("condition_json", "action_json"):
        if isinstance(d.get(k), str):
            try:
                d[k] = json.loads(d[k])
            except json.JSONDecodeError:
                d[k] = {}
    return d


class QuarantineRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def insert(self, original_path: str, quarantine_path: str, reason: str,
               expires_at: str, size: int = 0, sha256: str = "") -> int:
        cur = self._db.execute(
            "INSERT INTO quarantine_items "
            "(original_path, quarantine_path, reason, expires_at, size, sha256) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (original_path, quarantine_path, reason, expires_at, size, sha256),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def active(self) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM quarantine_items WHERE status='active' ORDER BY expires_at ASC"
        ))

    def all(self) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM quarantine_items ORDER BY id DESC"
        ))

    def get(self, item_id: int) -> dict[str, Any] | None:
        row = self._db.fetchone("SELECT * FROM quarantine_items WHERE id=?", (item_id,))
        return dict(row) if row else None

    def restore(self, item_id: int) -> None:
        self._db.execute(
            "UPDATE quarantine_items SET status='restored' WHERE id=?", (item_id,),
        )
        self._db.commit()

    def purge(self, item_id: int) -> None:
        self._db.execute(
            "UPDATE quarantine_items SET status='purged' WHERE id=?", (item_id,),
        )
        self._db.commit()

    def expired(self) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM quarantine_items WHERE status='active' AND expires_at < ?",
            (_now(),),
        ))

    def count_active(self) -> int:
        row = self._db.fetchone(
            "SELECT COUNT(*) FROM quarantine_items WHERE status='active'"
        )
        return int(row[0]) if row else 0

    def total_size(self) -> int:
        row = self._db.fetchone(
            "SELECT COALESCE(SUM(size),0) FROM quarantine_items WHERE status='active'"
        )
        return int(row[0]) if row else 0


class TrustDecisionRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def insert(self, process_id: int, decision: str, scope: str = "all",
               reason: str = "", expires_at: str = "") -> int:
        cur = self._db.execute(
            "INSERT INTO trust_decisions (process_id, decision, scope, reason, expires_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (process_id, decision, scope, reason, expires_at, _now()),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def for_process(self, process_id: int) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM trust_decisions WHERE process_id=? ORDER BY created_at DESC",
            (process_id,),
        ))

    def recent(self, limit: int = 200) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT td.*, pi.exe_name, pi.exe_path FROM trust_decisions td "
            "JOIN process_identities pi ON td.process_id=pi.id "
            "ORDER BY td.created_at DESC LIMIT ?",
            (limit,),
        ))

    def delete(self, decision_id: int) -> None:
        self._db.execute("DELETE FROM trust_decisions WHERE id=?", (decision_id,))
        self._db.commit()

    def delete_expired(self) -> int:
        cur = self._db.execute(
            "DELETE FROM trust_decisions WHERE expires_at!='' AND expires_at < ?",
            (_now(),),
        )
        self._db.commit()
        return cur.rowcount


class BandwidthRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def insert_sample(self, process_id: int, bytes_sent: int, bytes_recv: int,
                      period_sec: int = 60) -> int:
        cur = self._db.execute(
            "INSERT INTO bandwidth_samples (timestamp, process_id, bytes_sent, bytes_recv, period_sec) "
            "VALUES (?, ?, ?, ?, ?)",
            (_now(), process_id, bytes_sent, bytes_recv, period_sec),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def add_to_day(self, process_id: int, bytes_sent: int, bytes_recv: int,
                   day: str | None = None) -> None:
        day = day or _today()
        row = self._db.fetchone(
            "SELECT id, bytes_sent, bytes_recv FROM bandwidth_daily WHERE day=? AND process_id=?",
            (day, process_id),
        )
        if row:
            self._db.execute(
                "UPDATE bandwidth_daily SET bytes_sent=?, bytes_recv=? WHERE id=?",
                (row["bytes_sent"] + bytes_sent, row["bytes_recv"] + bytes_recv, row["id"]),
            )
        else:
            self._db.execute(
                "INSERT INTO bandwidth_daily (day, process_id, bytes_sent, bytes_recv) "
                "VALUES (?, ?, ?, ?)",
                (day, process_id, bytes_sent, bytes_recv),
            )
        self._db.commit()

    def for_process(self, process_id: int, limit: int = 200) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM bandwidth_samples WHERE process_id=? "
            "ORDER BY timestamp DESC LIMIT ?",
            (process_id, limit),
        ))

    def top_processes_today(self, limit: int = 20) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT bd.*, pi.exe_name, pi.exe_path "
            "FROM bandwidth_daily bd "
            "JOIN process_identities pi ON bd.process_id=pi.id "
            "WHERE bd.day=? "
            "ORDER BY (bd.bytes_sent + bd.bytes_recv) DESC LIMIT ?",
            (_today(), limit),
        ))

    def total_today(self) -> tuple[int, int]:
        row = self._db.fetchone(
            "SELECT COALESCE(SUM(bytes_sent),0), COALESCE(SUM(bytes_recv),0) "
            "FROM bandwidth_daily WHERE day=?",
            (_today(),),
        )
        if not row:
            return 0, 0
        return int(row[0]), int(row[1])

    def daily_range(self, days: int = 7) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT day, SUM(bytes_sent) as bytes_sent, SUM(bytes_recv) as bytes_recv "
            "FROM bandwidth_daily GROUP BY day ORDER BY day DESC LIMIT ?",
            (days,),
        ))

    def purge_samples_older_than(self, days: int) -> int:
        cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
        cutoff_iso = datetime.fromtimestamp(cutoff, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        cur = self._db.execute(
            "DELETE FROM bandwidth_samples WHERE timestamp < ?", (cutoff_iso,),
        )
        self._db.commit()
        return cur.rowcount


class DnsHistoryRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def record(self, ip: str, domain: str) -> int:
        if not ip or not domain:
            return 0
        existing = self._db.fetchone(
            "SELECT id FROM dns_history WHERE ip=? AND domain=?",
            (ip, domain),
        )
        if existing:
            self._db.execute(
                "UPDATE dns_history SET seen_at=? WHERE id=?",
                (_now(), existing["id"]),
            )
            self._db.commit()
            return existing["id"]
        cur = self._db.execute(
            "INSERT INTO dns_history (ip, domain) VALUES (?, ?)",
            (ip, domain),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def for_ip(self, ip: str) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM dns_history WHERE ip=? ORDER BY seen_at DESC",
            (ip,),
        ))

    def recent(self, limit: int = 200) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM dns_history ORDER BY seen_at DESC LIMIT ?",
            (limit,),
        ))


class DuplicateRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def create_group(self, file_hash: str, total_size: int, file_count: int) -> int:
        cur = self._db.execute(
            "INSERT INTO duplicate_groups (hash, total_size, file_count) VALUES (?, ?, ?)",
            (file_hash, total_size, file_count),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def add_file(self, group_id: int, path: str, size: int) -> int:
        cur = self._db.execute(
            "INSERT INTO duplicate_files (group_id, path, size) VALUES (?, ?, ?)",
            (group_id, path, size),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def groups(self) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM duplicate_groups ORDER BY total_size DESC"
        ))

    def files(self, group_id: int) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM duplicate_files WHERE group_id=? ORDER BY discovered_at",
            (group_id,),
        ))

    def clear(self) -> None:
        self._db.execute("DELETE FROM duplicate_files")
        self._db.execute("DELETE FROM duplicate_groups")
        self._db.commit()

    def total_wasted(self) -> int:
        row = self._db.fetchone(
            "SELECT COALESCE(SUM(total_size - (total_size / file_count)), 0) "
            "FROM duplicate_groups WHERE file_count > 0"
        )
        return int(row[0]) if row else 0


class FolderProfileRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def upsert(self, folder_path: str, profile_name: str = "default",
               recursive: bool = False, auto_apply: bool = False) -> int:
        row = self._db.fetchone(
            "SELECT id FROM folder_profiles WHERE folder_path=?", (folder_path,),
        )
        if row:
            self._db.execute(
                "UPDATE folder_profiles SET profile_name=?, recursive=?, auto_apply=? WHERE id=?",
                (profile_name, int(recursive), int(auto_apply), row["id"]),
            )
            self._db.commit()
            return row["id"]
        cur = self._db.execute(
            "INSERT INTO folder_profiles (folder_path, profile_name, recursive, auto_apply) "
            "VALUES (?, ?, ?, ?)",
            (folder_path, profile_name, int(recursive), int(auto_apply)),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_all(self) -> list[dict[str, Any]]:
        return _rows(self._db.fetchall(
            "SELECT * FROM folder_profiles ORDER BY folder_path"
        ))

    def get_by_folder(self, folder_path: str) -> dict[str, Any] | None:
        row = self._db.fetchone(
            "SELECT * FROM folder_profiles WHERE folder_path=?", (folder_path,),
        )
        return dict(row) if row else None

    def delete(self, profile_id: int) -> None:
        self._db.execute("DELETE FROM folder_profiles WHERE id=?", (profile_id,))
        self._db.commit()


class RuleTemplateRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def upsert(self, name: str, category: str, description: str, payload: dict) -> int:
        row = self._db.fetchone(
            "SELECT id FROM rule_templates WHERE name=?", (name,),
        )
        if row:
            self._db.execute(
                "UPDATE rule_templates SET category=?, description=?, payload=? WHERE id=?",
                (category, description, json.dumps(payload), row["id"]),
            )
            self._db.commit()
            return row["id"]
        cur = self._db.execute(
            "INSERT INTO rule_templates (name, category, description, payload) "
            "VALUES (?, ?, ?, ?)",
            (name, category, description, json.dumps(payload)),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def all(self) -> list[dict[str, Any]]:
        rows = self._db.fetchall("SELECT * FROM rule_templates ORDER BY category, name")
        result: list[dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            try:
                d["payload"] = json.loads(d.get("payload") or "{}")
            except json.JSONDecodeError:
                d["payload"] = {}
            result.append(d)
        return result

    def by_category(self, category: str) -> list[dict[str, Any]]:
        return [t for t in self.all() if t["category"] == category]


class ScanHistoryRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def start(self, folders: list[str], notes: str = "") -> int:
        cur = self._db.execute(
            "INSERT INTO scan_history (started_at, folders, notes) VALUES (?, ?, ?)",
            (_now(), json.dumps(folders), notes),
        )
        self._db.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def finish(self, scan_id: int, files_seen: int, actions_done: int) -> None:
        self._db.execute(
            "UPDATE scan_history SET finished_at=?, files_seen=?, actions_done=? WHERE id=?",
            (_now(), files_seen, actions_done, scan_id),
        )
        self._db.commit()

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._db.fetchall(
            "SELECT * FROM scan_history ORDER BY started_at DESC LIMIT ?",
            (limit,),
        )
        result: list[dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            try:
                d["folders"] = json.loads(d.get("folders") or "[]")
            except json.JSONDecodeError:
                d["folders"] = []
            result.append(d)
        return result


class SettingsKeyValueRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def set(self, key: str, value: Any) -> None:
        existing = self._db.fetchone("SELECT 1 FROM settings WHERE key=?", (key,))
        payload = json.dumps(value)
        if existing:
            self._db.execute(
                "UPDATE settings SET value_json=?, updated_at=? WHERE key=?",
                (payload, _now(), key),
            )
        else:
            self._db.execute(
                "INSERT INTO settings (key, value_json, updated_at) VALUES (?, ?, ?)",
                (key, payload, _now()),
            )
        self._db.commit()

    def get(self, key: str, default: Any = None) -> Any:
        row = self._db.fetchone("SELECT value_json FROM settings WHERE key=?", (key,))
        if not row:
            return default
        try:
            return json.loads(row["value_json"])
        except json.JSONDecodeError:
            return default

    def delete(self, key: str) -> None:
        self._db.execute("DELETE FROM settings WHERE key=?", (key,))
        self._db.commit()

    def all(self) -> dict[str, Any]:
        rows = self._db.fetchall("SELECT key, value_json FROM settings")
        out: dict[str, Any] = {}
        for r in rows:
            try:
                out[r["key"]] = json.loads(r["value_json"])
            except json.JSONDecodeError:
                out[r["key"]] = None
        return out
