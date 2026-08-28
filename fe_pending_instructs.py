#!/usr/bin/env python3
import argparse
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "chat.db"


def expand_vars(text, vars_map):
    pattern = re.compile(r"\{([A-Za-z0-9_.-]+)\}")
    return pattern.sub(lambda m: vars_map.get(m.group(1), m.group(0)), text)


def fe_pending_instructs(mode=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    vars_map = {name: value for name, value in cur.execute("select name, value from variables").fetchall()}
    rows = cur.execute("select id, content, status from instruct where status='pending' order by id").fetchall()
    pending = [expand_vars(row[1], vars_map) for row in rows]

    if mode == "done" and rows:
        ids = ",".join(str(row[0]) for row in rows)
        cur.execute(f"update instruct set status='done' where id in ({ids})")
        conn.commit()

    if mode in ("pending", "1", 1):
        cur.execute("update instruct set status='pending' where id=1")
        conn.commit()
        row = cur.execute("select id, content, status from instruct where id=1").fetchone()
        return [expand_vars(row[1], vars_map)]

    return pending


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("arg1", nargs="?", default=None)
    parser.add_argument("arg2", nargs="?", default=None)
    args = parser.parse_args()

    mode = args.arg1
    if args.arg2 is not None:
        if args.arg1 == "1" and args.arg2 == "pending":
            mode = "pending"
        else:
            mode = args.arg2

    print(json.dumps(fe_pending_instructs(mode)))
