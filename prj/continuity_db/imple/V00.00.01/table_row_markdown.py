from __future__ import annotations

# R1.10: This exporter module turns table or view rows into Markdown asset files.
import argparse
import json
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


def markdown_asset_path(assets_root: Path, source: str, identifier: str) -> Path:
    return assets_root / source / f"{str(identifier).zfill(4)}-{source}.md"


def row_to_markdown(source: str, row: dict[str, Any]) -> str:
    identifier = row.get("id") or row.get("state_key") or row.get("name") or row.get("key") or row.get("rowid") or "row"
    lines = [f"# {source} row {identifier}", ""]
    for key, value in row.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


def _table_row_identifier(conn: sqlite3.Connection, source: str, row: sqlite3.Row, fallback_index: int) -> str:
    pk_cols = primary_key_columns(conn, source)
    if pk_cols:
        values = [row[col] for col in pk_cols]
        return "-".join(str(value).zfill(4) if str(value).isdigit() else str(value) for value in values)

    for key in ("id", "state_key", "name", "key"):
        if key in row.keys():
            value = row[key]
            if value is not None:
                return str(value).zfill(4) if str(value).isdigit() else str(value)

    keys = row.keys()
    if keys:
        first_value = row[keys[0]]
        if first_value is not None:
            return str(first_value).zfill(4) if str(first_value).isdigit() else str(first_value)
    return str(fallback_index).zfill(4)


def export_source_markdown(
    db_path: str | Path,
    source: str,
    assets_root: str | Path = DEFAULT_ASSETS_ROOT,
) -> list[Path]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    target_dir = Path(assets_root) / source
    try:
        if not source_exists(conn, source):
            raise SystemExit(f"source not found: {source}")
        if target_dir.exists():
            for path in target_dir.glob("*.md"):
                path.unlink()
        rows = conn.execute(f"SELECT * FROM {source}").fetchall()
        out_paths: list[Path] = []
        for index, row in enumerate(rows, start=1):
            row_dict = dict(row)
            identifier = _table_row_identifier(conn, source, row, index)
            content = row_to_markdown(source, row_dict)
            out_path = markdown_asset_path(Path(assets_root), source, identifier)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content, encoding="utf-8")
            out_paths.append(out_path)
        return out_paths
    finally:
        conn.close()


# R1.10: The CLI entrypoint exports every row from one table or view into the asset filespace.
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export all rows from a table or view to Markdown asset files.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--assets-root", type=Path, default=DEFAULT_ASSETS_ROOT)
    parser.add_argument("--source", required=True, help="Table or view name to export.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    out_paths = export_source_markdown(args.db, args.source, assets_root=args.assets_root)
    payload = {"db": str(args.db), "source": args.source, "asset_paths": [str(path) for path in out_paths]}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for path in out_paths:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
