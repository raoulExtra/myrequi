#!/usr/bin/env python3
"""Import a JSON seed and store a unique minimal attribute list in SQLite.

This script stores recursively discovered attribute paths in `attribs`.
It reads JSON documents from both `seeds` and `jsons` tables, plus DB schema.
For the current seed layer, all stored entries are level 1.

Examples:
  concepts
  concepts.record_type
  concepts.meta.purpose
  db.table.seeds
  db.table.seeds.name
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB = Path("thinker/thinker.db")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS attribs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          level INTEGER NOT NULL,
          name VARCHAR(256) NOT NULL,
          json_content TEXT NOT NULL,
          UNIQUE(level, name)
        )
        """
    )


def load_json_from_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_documents(conn: sqlite3.Connection, seed_name: str | None = None) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []

    if seed_name:
        row = conn.execute(
            "SELECT json_content FROM seeds WHERE name = ? ORDER BY id DESC LIMIT 1",
            (seed_name,),
        ).fetchone()
        if not row:
            raise SystemExit(f"seed not found: {seed_name}")
        docs.append(json.loads(row[0]))
        return docs

    for table in ("seeds", "jsons"):
        rows = conn.execute(f"SELECT json_content FROM {table} ORDER BY id").fetchall()
        for (content,) in rows:
            docs.append(json.loads(content))

    return docs


def iter_json_attribs(data: dict[str, Any]):
    seen: set[str] = set()

    def emit(path: str, value: Any):
        if path and path not in seen:
            seen.add(path)
            yield {
                "level": 1,
                "name": path,
                "json_content": {
                    "kind": "json_path",
                    "path": path,
                    "value_type": type(value).__name__,
                },
            }

    def walk(value: Any, path: str):
        yield from emit(path, value)

        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else key
                yield from walk(child, child_path)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, (dict, list)):
                    yield from walk(item, path)

    if isinstance(data.get('table'), str):
        base = data['table']
        for key, value in data.items():
            if key == 'table':
                continue
            yield from walk(value, f'{base}.{key}')
    else:
        for top_key, value in data.items():
            yield from walk(value, top_key)


def iter_db_attribs(conn: sqlite3.Connection):
    tables = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()

    for (table_name,) in tables:
        yield {
            "level": 1,
            "name": f"db.table.{table_name}",
            "json_content": {
                "kind": "db_table",
                "table": table_name,
            },
        }

        columns = conn.execute(f"PRAGMA table_info({table_name!r})").fetchall()
        for col in columns:
            # PRAGMA table_info columns: cid, name, type, notnull, dflt_value, pk
            yield {
                "level": 2,
                "name": f"db.table.{table_name}.{col[1]}",
                "json_content": {
                    "kind": "db_column",
                    "table": table_name,
                    "column": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "default": col[4],
                    "pk": bool(col[5]),
                },
            }


def upsert_attribs(conn: sqlite3.Connection, attribs: list[dict[str, Any]]) -> int:
    count = 0
    for item in attribs:
        conn.execute(
            """
            INSERT INTO attribs (level, name, json_content)
            VALUES (?, ?, ?)
            ON CONFLICT(level, name) DO UPDATE SET
              json_content = excluded.json_content
            """,
            (item["level"], item["name"], json.dumps(item["json_content"], ensure_ascii=False)),
        )
        count += 1
    conn.commit()
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--json-file", type=Path)
    parser.add_argument("--seed-name", default="layer_1_seed")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        ensure_tables(conn)

        conn.execute('DELETE FROM attribs')
        attribs = []
        if args.json_file:
            attribs.extend(iter_json_attribs(load_json_from_file(args.json_file)))
        else:
            seed_name = None if args.seed_name == 'layer_1_seed' else args.seed_name
            for data in load_json_documents(conn, seed_name):
                attribs.extend(iter_json_attribs(data))
        attribs.extend(iter_db_attribs(conn))
        n = upsert_attribs(conn, attribs)
        print(json.dumps({"db": str(args.db), "stored": n}, ensure_ascii=False))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
