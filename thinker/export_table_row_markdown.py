from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB = Path("continuity.db")
DEFAULT_ASSETS_ROOT = Path("prj/continuity_db/assets")


def source_exists(conn: sqlite3.Connection, source: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?",
        (source,),
    ).fetchone()
    return row is not None


def primary_key_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cols = conn.execute(f"PRAGMA table_info({table!r})").fetchall()
    pk_cols = [(row[5], row[1]) for row in cols if row[5]]
    return [name for _, name in sorted(pk_cols, key=lambda item: item[0])]


def primary_key_values(conn: sqlite3.Connection, table: str, row: sqlite3.Row | tuple[Any, ...]) -> list[Any]:
    columns = primary_key_columns(conn, table)
    if not columns:
        raise ValueError(f"table has no primary key: {table}")
    if isinstance(row, sqlite3.Row):
        return [row[col] for col in columns]
    all_cols = [col[1] for col in conn.execute(f"PRAGMA table_info({table!r})").fetchall()]
    row_map = dict(zip(all_cols, row))
    return [row_map[col] for col in columns]


def _identifier_text(identifier: Any) -> str:
    return str(identifier)


def markdown_asset_path(assets_root: Path, source: str, identifier: str | int) -> Path:
    return assets_root / source / f"{_identifier_text(identifier)}-{source}.md"


def row_to_markdown(source: str, row: dict[str, Any]) -> str:
    identifier = row.get("id") or row.get("state_key") or row.get("name") or row.get("key") or row.get("rowid") or "row"
    lines = [f"# {source} row {identifier}", ""]
    for key, value in row.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


def export_table_row_markdown(
    db_path: str | Path,
    source: str,
    identifier: Any,
    assets_root: str | Path = DEFAULT_ASSETS_ROOT,
) -> Path:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if not source_exists(conn, source):
            raise SystemExit(f"source not found: {source}")

        pk_cols = primary_key_columns(conn, source)
        if not pk_cols:
            raise SystemExit(f"source has no primary key: {source}")

        if len(pk_cols) == 1:
            where = f"{pk_cols[0]}=?"
            params = (identifier,)
        else:
            if not isinstance(identifier, (tuple, list)):
                raise ValueError("composite primary key requires a tuple or list identifier")
            if len(identifier) != len(pk_cols):
                raise ValueError("identifier length does not match primary key columns")
            where = " AND ".join(f"{col}=?" for col in pk_cols)
            params = tuple(identifier)

        row = conn.execute(f"SELECT * FROM {source} WHERE {where}", params).fetchone()
        if row is None:
            raise SystemExit(f"row not found: {source} {identifier}")

        content = row_to_markdown(source, dict(row))
        out_path = markdown_asset_path(Path(assets_root), source, identifier)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        return out_path
    finally:
        conn.close()
