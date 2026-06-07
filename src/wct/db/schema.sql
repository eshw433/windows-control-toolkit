PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS app_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    module      TEXT    NOT NULL,
    severity    TEXT    NOT NULL DEFAULT 'info',
    event_type  TEXT    NOT NULL,
    title       TEXT    NOT NULL,
    message     TEXT    NOT NULL DEFAULT '',
    metadata    TEXT    NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    status      TEXT    NOT NULL DEFAULT 'unread',
    module      TEXT    NOT NULL,
    title       TEXT    NOT NULL,
    body        TEXT    NOT NULL DEFAULT '',
    action_json TEXT    NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS settings (
    key         TEXT    PRIMARY KEY,
    value_json  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS process_identities (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    exe_path    TEXT    NOT NULL UNIQUE,
    exe_name    TEXT    NOT NULL,
    publisher   TEXT    NOT NULL DEFAULT '',
    file_hash   TEXT    NOT NULL DEFAULT '',
    first_seen  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    last_seen   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    trust_state TEXT    NOT NULL DEFAULT 'unknown',
    risk_score  INTEGER NOT NULL DEFAULT 0,
    risk_level  TEXT    NOT NULL DEFAULT 'low',
    note        TEXT    NOT NULL DEFAULT '',
    tags        TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS network_connections (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    process_id  INTEGER NOT NULL REFERENCES process_identities(id),
    pid         INTEGER NOT NULL,
    local_addr  TEXT    NOT NULL DEFAULT '',
    local_port  INTEGER NOT NULL DEFAULT 0,
    remote_addr TEXT    NOT NULL DEFAULT '',
    remote_port INTEGER NOT NULL DEFAULT 0,
    protocol    TEXT    NOT NULL DEFAULT 'tcp',
    status      TEXT    NOT NULL DEFAULT '',
    remote_domain TEXT  NOT NULL DEFAULT '',
    asn         TEXT    NOT NULL DEFAULT '',
    country     TEXT    NOT NULL DEFAULT '',
    service_hint TEXT   NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS firewall_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,
    process_path    TEXT    NOT NULL,
    direction       TEXT    NOT NULL DEFAULT 'out',
    action          TEXT    NOT NULL DEFAULT 'block',
    protocol        TEXT    NOT NULL DEFAULT 'any',
    remote_addr     TEXT    NOT NULL DEFAULT '',
    remote_port     TEXT    NOT NULL DEFAULT '',
    enabled         INTEGER NOT NULL DEFAULT 1,
    created_by_app  INTEGER NOT NULL DEFAULT 1,
    external_rule_name TEXT NOT NULL DEFAULT '',
    note            TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS trust_decisions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    process_id  INTEGER NOT NULL REFERENCES process_identities(id),
    decision    TEXT    NOT NULL,
    scope       TEXT    NOT NULL DEFAULT 'all',
    reason      TEXT    NOT NULL DEFAULT '',
    expires_at  TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS bandwidth_samples (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    process_id   INTEGER NOT NULL REFERENCES process_identities(id),
    bytes_sent   INTEGER NOT NULL DEFAULT 0,
    bytes_recv   INTEGER NOT NULL DEFAULT 0,
    period_sec   INTEGER NOT NULL DEFAULT 60
);

CREATE TABLE IF NOT EXISTS bandwidth_daily (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    day          TEXT    NOT NULL,
    process_id   INTEGER NOT NULL REFERENCES process_identities(id),
    bytes_sent   INTEGER NOT NULL DEFAULT 0,
    bytes_recv   INTEGER NOT NULL DEFAULT 0,
    UNIQUE(day, process_id)
);

CREATE TABLE IF NOT EXISTS dns_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ip         TEXT    NOT NULL,
    domain     TEXT    NOT NULL,
    seen_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS file_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    current_path  TEXT    NOT NULL,
    original_path TEXT    NOT NULL,
    size          INTEGER NOT NULL DEFAULT 0,
    extension     TEXT    NOT NULL DEFAULT '',
    sha256        TEXT    NOT NULL DEFAULT '',
    first_seen    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    last_seen     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    status        TEXT    NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS file_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    enabled         INTEGER NOT NULL DEFAULT 1,
    priority        INTEGER NOT NULL DEFAULT 100,
    condition_json  TEXT    NOT NULL DEFAULT '{}',
    action_json     TEXT    NOT NULL DEFAULT '{}',
    folder_scope    TEXT    NOT NULL DEFAULT '',
    note            TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS file_actions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    action_type   TEXT    NOT NULL,
    source_path   TEXT    NOT NULL,
    target_path   TEXT    NOT NULL DEFAULT '',
    status        TEXT    NOT NULL DEFAULT 'completed',
    reversible    INTEGER NOT NULL DEFAULT 1,
    rollback_json TEXT    NOT NULL DEFAULT '{}',
    error_message TEXT    NOT NULL DEFAULT '',
    file_size     INTEGER NOT NULL DEFAULT 0,
    rule_name     TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS duplicate_groups (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    hash        TEXT    NOT NULL,
    total_size  INTEGER NOT NULL DEFAULT 0,
    file_count  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS duplicate_files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id        INTEGER NOT NULL REFERENCES duplicate_groups(id) ON DELETE CASCADE,
    path            TEXT    NOT NULL,
    size            INTEGER NOT NULL DEFAULT 0,
    discovered_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS quarantine_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    original_path   TEXT    NOT NULL,
    quarantine_path TEXT    NOT NULL,
    reason          TEXT    NOT NULL DEFAULT '',
    expires_at      TEXT    NOT NULL,
    size            INTEGER NOT NULL DEFAULT 0,
    sha256          TEXT    NOT NULL DEFAULT '',
    status          TEXT    NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS folder_profiles (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_path   TEXT    NOT NULL UNIQUE,
    profile_name  TEXT    NOT NULL DEFAULT 'default',
    recursive     INTEGER NOT NULL DEFAULT 0,
    auto_apply    INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS rule_templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    category    TEXT    NOT NULL DEFAULT '',
    description TEXT    NOT NULL DEFAULT '',
    payload     TEXT    NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS scan_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at    TEXT    NOT NULL,
    finished_at   TEXT    NOT NULL DEFAULT '',
    folders       TEXT    NOT NULL DEFAULT '[]',
    files_seen    INTEGER NOT NULL DEFAULT 0,
    actions_done  INTEGER NOT NULL DEFAULT 0,
    notes         TEXT    NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_net_conn_process   ON network_connections(process_id);
CREATE INDEX IF NOT EXISTS idx_net_conn_ts        ON network_connections(timestamp);
CREATE INDEX IF NOT EXISTS idx_net_conn_remote    ON network_connections(remote_addr, remote_port);
CREATE INDEX IF NOT EXISTS idx_file_actions_ts    ON file_actions(timestamp);
CREATE INDEX IF NOT EXISTS idx_file_items_sha     ON file_items(sha256);
CREATE INDEX IF NOT EXISTS idx_app_events_ts      ON app_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_bandwidth_ts       ON bandwidth_samples(timestamp);
CREATE INDEX IF NOT EXISTS idx_bandwidth_proc     ON bandwidth_samples(process_id);
CREATE INDEX IF NOT EXISTS idx_bandwidth_daily_day ON bandwidth_daily(day);
CREATE INDEX IF NOT EXISTS idx_dns_history_ip     ON dns_history(ip);
CREATE INDEX IF NOT EXISTS idx_quarantine_status  ON quarantine_items(status);
CREATE INDEX IF NOT EXISTS idx_duplicate_files_grp ON duplicate_files(group_id);
CREATE INDEX IF NOT EXISTS idx_trust_proc          ON trust_decisions(process_id);
