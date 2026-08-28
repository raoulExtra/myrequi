#!/usr/bin/env python3
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "chat.db"

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        kind TEXT NOT NULL DEFAULT 'thing',
        description TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id INTEGER NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        scope TEXT NOT NULL DEFAULT 'general',
        source TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS relations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_entity_id INTEGER NOT NULL,
        relation TEXT NOT NULL,
        to_entity_id INTEGER NOT NULL,
        weight REAL NOT NULL DEFAULT 1.0,
        source TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(from_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
        FOREIGN KEY(to_entity_id) REFERENCES entities(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        happened_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        summary TEXT,
        payload_json TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS event_entities (
        event_id INTEGER NOT NULL,
        entity_id INTEGER NOT NULL,
        role TEXT NOT NULL DEFAULT 'related',
        PRIMARY KEY (event_id, entity_id, role),
        FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
        FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE CASCADE
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_facts_entity_key ON facts(entity_id, key)",
    "CREATE INDEX IF NOT EXISTS idx_rel_from_relation ON relations(from_entity_id, relation)",
    "CREATE INDEX IF NOT EXISTS idx_rel_to_relation ON relations(to_entity_id, relation)",
    "CREATE INDEX IF NOT EXISTS idx_event_entities_entity ON event_entities(entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_events_happened_at ON events(happened_at)",
]


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    for stmt in SCHEMA:
        cur.execute(stmt)
    conn.commit()

    tables = [
        row[0]
        for row in cur.execute(
            "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name"
        )
    ]
    print({"db": str(DB_PATH), "tables": tables})


if __name__ == "__main__":
    main()
