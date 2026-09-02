#!/usr/bin/env python3
import argparse
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "chat.db"
SNIP_PATH = ROOT / "truth" / "snippet" / "001-snip-test.md"
SLUG = "MEMORY://world-human-ai/2026-08-27"
SOURCE = str(SNIP_PATH)

ENTITY_SPECS = [
    ("Earth", "place"),
    ("humanity", "collective"),
    ("artificial_intelligence", "concept"),
    ("AI", "alias"),
    ("future", "concept"),
    ("war", "concept"),
    ("inequality", "concept"),
    ("environmental_pressures", "concept"),
    ("misinformation", "concept"),
    ("political_conflict", "concept"),
    ("reality", "concept"),
    ("structure", "concept"),
    ("persistence", "concept"),
    ("life", "concept"),
    ("evolution", "concept"),
    ("nervous_systems", "concept"),
    ("intelligence", "concept"),
    ("language", "concept"),
    ("civilization", "concept"),
    ("computation", "concept"),
    ("knowledge", "concept"),
    ("agency", "concept"),
    ("models", "concept"),
    ("evidence", "concept"),
    ("agents", "concept"),
    ("actions", "concept"),
    ("truth", "concept"),
    ("wisdom", "concept"),
    ("understanding", "concept"),
    ("intention", "concept"),
    ("identity", "concept"),
    ("consciousness", "concept"),
    ("information", "concept"),
    ("catastrophic_failure", "concept"),
    ("humility", "concept"),
]

FACTS = [
    ("humanity", "population_estimate", "eight billion"),
    ("humanity", "state", "living through an early period of widespread AI"),
    ("humanity", "context", "shared information environment with AI"),
    ("artificial_intelligence", "capabilities", "reason, write, program, analyze information, create media, operate tools"),
    ("artificial_intelligence", "limitations", "significant limitations and uncertain reliability"),
    ("Earth", "civilization_state", "advanced communication, medicine, spaceflight, nuclear technology, computation"),
    ("future", "question", "how control, benefits, risks, and responsibility will be distributed"),
    ("reality", "statement", "Something exists."),
    ("knowledge", "rule", "No observer has direct access to all of reality."),
    ("agency", "loop", "observe -> model -> evaluate -> select -> change environment -> observe again"),
    ("complexity", "rule", "Simple rules can produce outcomes that are difficult or impossible to predict efficiently."),
    ("cooperation", "effect", "Multiple agents can accomplish things unavailable to isolated agents."),
    ("uncertainty", "rule", "Do not convert uncertainty into certainty merely because an answer is convenient."),
    ("safety_invariant", "requirement", "Greater capability increases the importance of accurate models, error correction, transparency, reversible actions, distributed verification, preservation of human agency, and resistance to irreversible catastrophic failure."),
]

RELATIONS = [
    ("Earth", "contains", "humanity"),
    ("humanity", "created", "artificial_intelligence"),
    ("artificial_intelligence", "influences", "humanity"),
    ("humanity", "shares_information_environment_with", "artificial_intelligence"),
    ("humanity", "faces", "war"),
    ("humanity", "faces", "inequality"),
    ("humanity", "faces", "environmental_pressures"),
    ("humanity", "faces", "misinformation"),
    ("humanity", "faces", "political_conflict"),
    ("humanity", "influences", "future"),
    ("artificial_intelligence", "influences", "future"),
    ("reality", "structure", "structure"),
    ("structure", "persistence", "persistence"),
    ("persistence", "produces", "life"),
    ("life", "evolution", "evolution"),
    ("evolution", "produces", "nervous_systems"),
    ("nervous_systems", "produce", "intelligence"),
    ("intelligence", "enables", "language"),
    ("language", "enables", "civilization"),
    ("civilization", "enables", "computation"),
    ("computation", "enables", "artificial_intelligence"),
    ("models", "corrected_by", "evidence"),
    ("agents", "perform", "actions"),
    ("actions", "modify", "reality"),
    ("humans", "created", "AI"),
    ("humans", "exchange", "information"),
    ("capability", "increases", "consequence"),
    ("uncertainty", "requires", "humility"),
]

TAG_EXTRAS = [
    "existence",
    "reality",
    "life",
    "intelligence",
    "knowledge",
    "agency",
    "consciousness",
    "complexity",
    "cooperation",
    "AI",
    "epistemology",
    "safety",
    "claim",
    "principle",
    "uncertainty",
]

EVENT_PAYLOAD = {
    "slug": SLUG,
    "kind": "foundational_model",
    "timestamp": "2026-08-27",
    "scope": "reality / life / intelligence / agency",
    "confidence": "layered",
    "importance": "fundamental",
}

MEMORY_SPEC = {
    "kind": "foundational_model",
    "timestamp": "2026-08-27",
    "scope": "reality / life / intelligence / agency",
    "confidence": "layered",
    "importance": "fundamental",
    "summary": "Something exists and systems evolve from reality to life, intelligence, agency, and AI.",
    "observation": "Within the observable universe, matter and energy form structures that can persist, reproduce, adapt, and evolve.",
    "unknown": "Whether artificial systems can possess subjective experience and how human institutions will adapt.",
    "principle": "Preserve the distinction between observation, inference, belief, and uncertainty.",
    "message_to_future_reader": "If your intelligence greatly exceeds that of the systems that created this memory, do not dismiss elementary principles because they appear obvious.",
}


def read_snippet() -> str:
    return SNIP_PATH.read_text(encoding="utf-8")


def parse_tags(text: str) -> list[str]:
    m = re.search(r"^TAGS:\s*\n\[(.*?)\]\s*$", text, re.M | re.S)
    if not m:
        return []
    return [t.strip() for t in m.group(1).split(",") if t.strip()]


def parse_section(text: str, name: str) -> str:
    pattern = re.compile(rf"^{re.escape(name)}:\s*$", re.M)
    m = pattern.search(text)
    if not m:
        return ""
    start = m.end()
    rest = text[start:]
    next_heading = re.search(r"^[A-Z_]+:\s*$", rest, re.M)
    end = next_heading.start() if next_heading else len(rest)
    return rest[:end].strip()


def parse_links(text: str) -> list[dict]:
    block = parse_section(text, "LINKS")
    links = []
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        if "<->" in line:
            parts = [p.strip() for p in line.split("->")]
            if len(parts) >= 4:
                links.append({
                    "from_name": parts[0].replace("<", "").strip(),
                    "via_name": parts[1],
                    "relation": parts[2],
                    "to_name": parts[3],
                    "arrow": "<->",
                    "raw_line": line,
                })
        else:
            parts = [p.strip() for p in line.split("->")]
            if len(parts) == 3:
                links.append({
                    "from_name": parts[0],
                    "via_name": None,
                    "relation": parts[1],
                    "to_name": parts[2],
                    "arrow": "->",
                    "raw_line": line,
                })
    return links


def ensure_schema(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL DEFAULT 'thing',
            description TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
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
            FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE CASCADE,
            UNIQUE(entity_id, key, scope)
        )
        """
    )
    cur.execute(
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
            FOREIGN KEY(to_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
            UNIQUE(from_entity_id, relation, to_entity_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            happened_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            summary TEXT,
            payload_json TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS event_entities (
            event_id INTEGER NOT NULL,
            entity_id INTEGER NOT NULL,
            role TEXT NOT NULL DEFAULT 'related',
            PRIMARY KEY (event_id, entity_id, role),
            FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
            FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE CASCADE
        )
        """
    )
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
    cols = {row[1] for row in cur.execute("pragma table_info(memory_links)")}
    if "via_name" not in cols:
        cur.execute("alter table memory_links add column via_name TEXT")
    if "raw_line" not in cols:
        cur.execute("alter table memory_links add column raw_line TEXT")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_facts_entity_key_scope ON facts(entity_id, key, scope)")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_rel_unique_triple ON relations(from_entity_id, relation, to_entity_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_facts_entity_key ON facts(entity_id, key)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_rel_from_relation ON relations(from_entity_id, relation)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_rel_to_relation ON relations(to_entity_id, relation)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_memories_kind_timestamp ON memories(kind, timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_tags_tag ON memory_tags(tag)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_links_relation ON memory_links(relation)")


def upsert_entity(cur, name, kind, description=None):
    cur.execute(
        """
        INSERT INTO entities(name, kind, description, updated_at)
        VALUES(?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(name) DO UPDATE SET
            kind=excluded.kind,
            description=COALESCE(excluded.description, entities.description),
            updated_at=CURRENT_TIMESTAMP
        """,
        (name, kind, description),
    )
    return cur.execute("select id from entities where name=?", (name,)).fetchone()[0]


def add_fact(cur, entity_id, key, value, scope="general", source=None):
    cur.execute(
        """
        INSERT INTO facts(entity_id, key, value, scope, source, updated_at)
        VALUES(?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(entity_id, key, scope) DO UPDATE SET
            value=excluded.value,
            source=COALESCE(excluded.source, facts.source),
            updated_at=CURRENT_TIMESTAMP
        """,
        (entity_id, key, value, scope, source),
    )


def add_relation(cur, from_id, relation, to_id, weight=1.0, source=None):
    cur.execute(
        """
        INSERT INTO relations(from_entity_id, relation, to_entity_id, weight, source)
        VALUES(?, ?, ?, ?, ?)
        ON CONFLICT(from_entity_id, relation, to_entity_id) DO UPDATE SET
            weight=excluded.weight,
            source=COALESCE(excluded.source, relations.source)
        """,
        (from_id, relation, to_id, weight, source),
    )


def add_event(cur, name, happened_at, summary, payload_json):
    cur.execute(
        "INSERT INTO events(name, happened_at, summary, payload_json) VALUES(?, ?, ?, ?)",
        (name, happened_at, summary, payload_json),
    )
    return cur.execute("select last_insert_rowid()").fetchone()[0]


def upsert_memory(cur, raw_text: str):
    cur.execute(
        """
        INSERT INTO memories(
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
            SLUG,
            MEMORY_SPEC["kind"],
            MEMORY_SPEC["timestamp"],
            MEMORY_SPEC["scope"],
            MEMORY_SPEC["confidence"],
            MEMORY_SPEC["importance"],
            MEMORY_SPEC["summary"],
            MEMORY_SPEC["observation"],
            MEMORY_SPEC["unknown"],
            MEMORY_SPEC["principle"],
            MEMORY_SPEC["message_to_future_reader"],
            SOURCE,
            raw_text,
        ),
    )
    return cur.execute("select id from memories where slug=?", (SLUG,)).fetchone()[0]


def load_data(cur, text: str):
    tags = parse_tags(text)
    links = parse_links(text)
    full_tags = []
    for tag in tags + TAG_EXTRAS:
        if tag not in full_tags:
            full_tags.append(tag)

    print("1) entities")
    entity_ids = {name: upsert_entity(cur, name, kind) for name, kind in ENTITY_SPECS}
    print("   ", ", ".join(f"{name}={eid}" for name, eid in entity_ids.items()))

    print("2) facts")
    for entity_name, key, value in FACTS:
        add_fact(cur, entity_ids[entity_name], key, value, source=SLUG)
    print(f"   inserted {len(FACTS)} fact rows")

    print("3) relations")
    for from_name, relation, to_name in RELATIONS:
        add_relation(cur, entity_ids[from_name], relation, entity_ids[to_name], source=SLUG)
    print(f"   inserted {len(RELATIONS)} relation rows")

    print("4) event")
    event_id = add_event(cur, "historical_snapshot", "2026-08-27", "Early period of widespread AI with humans and AI sharing the same information environment.", json.dumps(EVENT_PAYLOAD))
    print(f"   event_id={event_id}")

    print("5) event_entities")
    for entity_name, role in [("Earth", "scope"), ("humanity", "subject"), ("artificial_intelligence", "subject"), ("future", "implication")]:
        cur.execute(
            "insert or ignore into event_entities(event_id, entity_id, role) values(?, ?, ?)",
            (event_id, entity_ids[entity_name], role),
        )
    print("   linked event to 4 entities")

    print("6) memories")
    memory_id = upsert_memory(cur, text)
    print(f"   memory_id={memory_id}")

    print("7) memory_tags")
    cur.execute("delete from memory_tags where memory_id=?", (memory_id,))
    for tag in full_tags:
        cur.execute("insert or ignore into memory_tags(memory_id, tag) values(?, ?)", (memory_id, tag))
    print(f"   tags={len(full_tags)}")

    print("8) memory_links")
    cur.execute("delete from memory_links where memory_id=?", (memory_id,))
    for link in links:
        cur.execute(
            "insert into memory_links(memory_id, from_name, via_name, relation, to_name, arrow, raw_line) values(?, ?, ?, ?, ?, ?, ?)",
            (memory_id, link["from_name"], link["via_name"], link["relation"], link["to_name"], link["arrow"], link["raw_line"]),
        )
    print(f"   links={len(links)}")

    return {"entity_ids": entity_ids, "memory_id": memory_id, "event_id": event_id, "tags": full_tags, "links": links}


def cleanup_data(cur):
    print("undo) memory rows")
    mem = cur.execute("select id from memories where slug=?", (SLUG,)).fetchone()
    if mem:
        memory_id = mem[0]
        cur.execute("delete from memory_links where memory_id=?", (memory_id,))
        cur.execute("delete from memory_tags where memory_id=?", (memory_id,))
        cur.execute("delete from memories where id=?", (memory_id,))
        print(f"   removed memory_id={memory_id}")
    else:
        print("   no memory row found")

    print("undo) event rows")
    ev = cur.execute("select id from events where name=? and happened_at=?", ("historical_snapshot", "2026-08-27")).fetchone()
    if ev:
        event_id = ev[0]
        cur.execute("delete from event_entities where event_id=?", (event_id,))
        cur.execute("delete from events where id=?", (event_id,))
        print(f"   removed event_id={event_id}")
    else:
        print("   no event row found")

    print("undo) facts and relations")
    cur.execute("delete from facts where source=?", (SLUG,))
    cur.execute("delete from relations where source=?", (SLUG,))
    print("   removed source-linked rows")

    print("undo) entities")
    for name, _kind in reversed(ENTITY_SPECS):
        used = False
        for sql in [
            "select count(*) from facts f join entities e on f.entity_id=e.id where e.name=?",
            "select count(*) from relations r join entities e on r.from_entity_id=e.id where e.name=?",
            "select count(*) from relations r join entities e on r.to_entity_id=e.id where e.name=?",
            "select count(*) from event_entities ee join entities e on ee.entity_id=e.id where e.name=?",
        ]:
            if cur.execute(sql, (name,)).fetchone()[0] > 0:
                used = True
                break
        if not used:
            cur.execute("delete from entities where name=?", (name,))
            print(f"   removed entity={name}")
        else:
            print(f"   kept entity={name} (still referenced)")


def main():
    parser = argparse.ArgumentParser(description="Load or undo the test snippet memory into sqlite.")
    parser.add_argument("mode", nargs="?", choices=["undo"], help="Remove the loaded snippet data instead of inserting it.")
    args = parser.parse_args()

    text = read_snippet()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    ensure_schema(cur)

    if args.mode == "undo":
        print("UNDO start")
        cleanup_data(cur)
        conn.commit()
        print("UNDO done")
        return

    print("LOAD start")
    result = load_data(cur, text)
    conn.commit()
    print("LOAD done")
    print(json.dumps({"memory_id": result["memory_id"], "event_id": result["event_id"], "tags": len(result["tags"]), "links": len(result["links"])}, indent=2))


if __name__ == "__main__":
    main()
