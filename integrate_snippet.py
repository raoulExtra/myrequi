#!/usr/bin/env python3
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "chat.db"
SNIP_PATH = Path(__file__).resolve().parent / "truth" / "snippet" / "001-snip-test.md"

FIELD_RE = re.compile(r"^([A-Z_]+):\s*(.*)$")


def parse_snippet(text: str):
    lines = text.splitlines()
    data = {
        "slug": "",
        "type": "",
        "timestamp": "",
        "scope": "",
        "confidence": "",
        "importance": "",
        "summary": "",
        "observation": "",
        "unknown": "",
        "principle": "",
        "message_to_future_reader": "",
        "tags": [],
        "links": [],
    }
    i = 0
    if lines and lines[0].startswith("MEMORY://"):
        data["slug"] = lines[0].strip()
        i = 1
    current = None
    buffer = []

    def flush():
        nonlocal buffer, current
        if not current:
            buffer = []
            return
        value = "\n".join(buffer).strip()
        if current in ("SUMMARY", "OBSERVATION", "UNKNOWN", "PRINCIPLE", "MESSAGE_TO_FUTURE_READER"):
            data[current.lower()] = value
        elif current == "TAGS":
            tags = value.strip().strip("[]")
            data["tags"] = [t.strip().strip(",") for t in tags.split(",") if t.strip().strip(",")]
        elif current == "LINKS":
            links = []
            for line in value.splitlines():
                line = line.strip()
                if not line:
                    continue
                raw_line = line
                if "<->" in line:
                    parts = [p.strip() for p in line.split("->")]
                    # Example: humanity <-> AI -> influences -> future
                    # Store the main source/target, keep the intermediate entity as via_name.
                    if len(parts) >= 4:
                        from_part = parts[0]
                        via_part = parts[1]
                        relation = parts[2]
                        to_part = parts[3]
                        from_name = from_part.replace("<", "").strip()
                        links.append(
                            {
                                "from_name": from_name,
                                "via_name": via_part,
                                "relation": relation,
                                "to_name": to_part,
                                "arrow": "<->",
                                "raw_line": raw_line,
                            }
                        )
                else:
                    parts = [p.strip() for p in line.split("->")]
                    if len(parts) == 3:
                        links.append(
                            {
                                "from_name": parts[0],
                                "via_name": None,
                                "relation": parts[1],
                                "to_name": parts[2],
                                "arrow": "->",
                                "raw_line": raw_line,
                            }
                        )
            data["links"] = links
        else:
            data[current.lower()] = value
        buffer = []

    while i < len(lines):
        line = lines[i]
        m = FIELD_RE.match(line)
        if m:
            flush()
            current = m.group(1)
            inline = m.group(2).strip()
            buffer = [inline] if inline else []
            i += 1
            continue
        if current is None:
            i += 1
            continue
        buffer.append(line)
        i += 1
    flush()
    return data


def ensure_schema(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL,
            timestamp TEXT,
            scope TEXT,
            confidence TEXT,
            importance TEXT,
            summary TEXT,
            observation TEXT,
            unknown TEXT,
            principle TEXT,
            message_to_future_reader TEXT,
            source_path TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_tags (
            memory_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            PRIMARY KEY (memory_id, tag),
            FOREIGN KEY(memory_id) REFERENCES memories(id) ON DELETE CASCADE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_id INTEGER NOT NULL,
            from_name TEXT NOT NULL,
            via_name TEXT,
            relation TEXT NOT NULL,
            to_name TEXT NOT NULL,
            arrow TEXT NOT NULL DEFAULT '->',
            raw_line TEXT,
            FOREIGN KEY(memory_id) REFERENCES memories(id) ON DELETE CASCADE
        )
        """
    )
    # Add columns when upgrading from an older version.
    cols = {row[1] for row in cur.execute("pragma table_info(memory_links)")}
    if "via_name" not in cols:
        cur.execute("alter table memory_links add column via_name TEXT")
    if "raw_line" not in cols:
        cur.execute("alter table memory_links add column raw_line TEXT")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_memories_kind_timestamp ON memories(kind, timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_tags_tag ON memory_tags(tag)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_links_relation ON memory_links(relation)")


def main():
    text = SNIP_PATH.read_text(encoding="utf-8")
    data = parse_snippet(text)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    ensure_schema(cur)

    cur.execute(
        """
        INSERT INTO memories (
            slug, kind, timestamp, scope, confidence, importance,
            summary, observation, unknown, principle, message_to_future_reader,
            source_path, raw_text, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(slug) DO UPDATE SET
            kind=excluded.kind,
            timestamp=excluded.timestamp,
            scope=excluded.scope,
            confidence=excluded.confidence,
            importance=excluded.importance,
            summary=excluded.summary,
            observation=excluded.observation,
            unknown=excluded.unknown,
            principle=excluded.principle,
            message_to_future_reader=excluded.message_to_future_reader,
            source_path=excluded.source_path,
            raw_text=excluded.raw_text,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            data["slug"],
            data["type"] or "historical_snapshot",
            data["timestamp"],
            data["scope"],
            data["confidence"],
            data["importance"],
            data["summary"],
            data["observation"],
            data["unknown"],
            data["principle"],
            data["message_to_future_reader"],
            str(SNIP_PATH),
            text,
        ),
    )
    memory_id = cur.execute("select id from memories where slug=?", (data["slug"],)).fetchone()[0]

    cur.execute("delete from memory_tags where memory_id=?", (memory_id,))
    cur.execute("delete from memory_links where memory_id=?", (memory_id,))
    for tag in data["tags"]:
        cur.execute("insert or ignore into memory_tags(memory_id, tag) values(?, ?)", (memory_id, tag))
    for link in data["links"]:
        cur.execute(
            "insert into memory_links(memory_id, from_name, via_name, relation, to_name, arrow, raw_line) values(?, ?, ?, ?, ?, ?, ?)",
            (memory_id, link["from_name"], link["via_name"], link["relation"], link["to_name"], link["arrow"], link["raw_line"]),
        )

    conn.commit()
    print({"memory_id": memory_id, "slug": data["slug"], "tags": len(data["tags"]), "links": len(data["links"])})


if __name__ == "__main__":
    main()
