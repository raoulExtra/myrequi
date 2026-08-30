#!/usr/bin/env python3
"""Build a first Layer 1 view from attribs + concepts.

The view is a materialized snapshot, not a live SQL VIEW.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB = Path("thinker/thinker.db")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS views (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          level INTEGER NOT NULL,
          view_type TEXT NOT NULL,
          name TEXT NOT NULL UNIQUE,
          source_ids TEXT,
          json_content TEXT NOT NULL,
          created_at TEXT NOT NULL
        )
        """
    )


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_layer1_snapshot(conn: sqlite3.Connection) -> dict[str, Any]:
    tables = [
        r[0]
        for r in conn.execute(
            """
            SELECT name
            FROM attribs
            WHERE level = 1 AND name LIKE 'db.table.%' AND json_content LIKE '%db_table%'
            ORDER BY name
            """
        ).fetchall()
    ]

    json_paths = [
        r[0]
        for r in conn.execute(
            """
            SELECT name
            FROM attribs
            WHERE level = 1 AND json_content LIKE '%json_path%'
            ORDER BY name
            """
        ).fetchall()
    ]

    top_concepts = conn.execute(
        """
        SELECT name, type, simplicity
        FROM concepts
        WHERE level = 1
        ORDER BY COALESCE(simplicity, 0) DESC, name
        LIMIT 12
        """
    ).fetchall()

    prefix_count = conn.execute(
        "SELECT count(*) FROM concepts WHERE type = 'prefix'"
    ).fetchone()[0]

    concept_count = conn.execute(
        "SELECT count(*) FROM concepts WHERE level = 1"
    ).fetchone()[0]

    return {
        "layer": 1,
        "view_type": "layer1_concept_index",
        "summary": (
            "Layer 1 index over atomic concepts and schema paths, "
            "highlighting the simplest reusable terms."
        ),
        "counts": {
            "concepts": concept_count,
            "prefixes": prefix_count,
            "tables": len(tables),
            "json_paths": len(json_paths),
        },
        "tables": tables,
        "json_paths": json_paths[:40],
        "top_concepts": [
            {"name": name, "type": typ, "simplicity": simp}
            for name, typ, simp in top_concepts
        ],
    }


def upsert_view(conn: sqlite3.Connection, name: str, payload: dict[str, Any], source_ids: list[int]) -> None:
    conn.execute(
        """
        INSERT INTO views (level, view_type, name, source_ids, json_content, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
          level = excluded.level,
          view_type = excluded.view_type,
          source_ids = excluded.source_ids,
          json_content = excluded.json_content,
          created_at = excluded.created_at
        """,
        (
            payload["layer"],
            payload["view_type"],
            name,
            json.dumps(source_ids),
            json.dumps(payload, ensure_ascii=False),
            now_utc(),
        ),
    )
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--name", default="layer1_concept_index")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        ensure_tables(conn)
        payload = fetch_layer1_snapshot(conn)
        source_ids = [
            r[0]
            for r in conn.execute(
                "SELECT id FROM attribs WHERE level = 1 ORDER BY id"
            ).fetchall()
        ]
        upsert_view(conn, args.name, payload, source_ids)
        print(json.dumps({"db": str(args.db), "view": args.name}, ensure_ascii=False))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
