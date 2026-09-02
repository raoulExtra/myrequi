from __future__ import annotations

# R1.1: Add a numeric id to metacognitive_state while keeping state_key readable.
import argparse
import sqlite3
from pathlib import Path
from typing import Iterable

DEFAULT_DB = Path("continuity.db")

METACOGNITIVE_STATE_COLUMNS = (
    "state_key",
    "category",
    "value",
    "confidence",
    "provenance",
    "version",
    "updated_at",
)


def capture_trigger_sql(conn: sqlite3.Connection, table_name: str) -> list[str]:
    rows = conn.execute(
        """
        select sql
        from sqlite_master
        where type='trigger' and tbl_name=? and sql is not null
        order by name
        """,
        (table_name,),
    ).fetchall()
    return [row[0] for row in rows]


def create_new_metacognitive_state_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        create table if not exists metacognitive_state (
          id integer primary key autoincrement,
          state_key text not null unique,
          category text not null,
          value text not null,
          confidence real not null check(confidence between 0 and 1),
          provenance text not null,
          version integer not null default 1,
          updated_at text not null default current_timestamp
        )
        """
    )


def _swap_metacognitive_state_tables(conn: sqlite3.Connection) -> None:
    conn.execute("alter table metacognitive_state rename to metacognitive_state_legacy")
    conn.execute(
        """
        create table metacognitive_state (
          id integer primary key autoincrement,
          state_key text not null unique,
          category text not null,
          value text not null,
          confidence real not null check(confidence between 0 and 1),
          provenance text not null,
          version integer not null default 1,
          updated_at text not null default current_timestamp
        )
        """
    )


def _copy_rows(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        """
        select state_key, category, value, confidence, provenance, version, updated_at
        from metacognitive_state_legacy
        order by rowid
        """
    ).fetchall()
    conn.executemany(
        """
        insert into metacognitive_state(state_key, category, value, confidence, provenance, version, updated_at)
        values(?,?,?,?,?,?,?)
        """,
        rows,
    )
    return len(rows)


def migrate_metacognitive_state_id(conn: sqlite3.Connection) -> int:
    conn.execute("pragma foreign_keys = off")
    conn.execute("pragma legacy_alter_table = on")
    trigger_sql = capture_trigger_sql(conn, "metacognitive_state")
    conn.execute("drop trigger if exists metacognitive_state_audit")
    _swap_metacognitive_state_tables(conn)
    count = _copy_rows(conn)
    conn.execute("drop table metacognitive_state_legacy")
    for sql in trigger_sql:
        conn.execute(sql)
    conn.execute("pragma foreign_keys = on")
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Add numeric id to metacognitive_state while preserving state_key.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    conn = sqlite3.connect(args.db)
    try:
        if args.dry_run:
            cols = conn.execute("pragma table_info(metacognitive_state)").fetchall()
            print(cols)
            return 0
        count = migrate_metacognitive_state_id(conn)
        conn.commit()
        print({"db": str(args.db), "migrated_rows": count})
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
