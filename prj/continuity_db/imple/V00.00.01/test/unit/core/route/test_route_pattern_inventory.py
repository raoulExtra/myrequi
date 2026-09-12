import json
import re
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[8]
DB_PATH = REPO_ROOT / "continuity.db"
TEST_IDEAS_DOC = REPO_ROOT / "prj" / "continuity_db" / "docs" / "000_phase" / "core" / "route" / "000-PH-001-test-ideas-input-pattern.md"


def _enabled_routes():
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT route_name, input_pattern
            FROM command_routes
            WHERE enabled = 1
            ORDER BY route_name
            """
        ).fetchall()


def test_every_enabled_route_has_a_unique_name_and_pattern():
    routes = _enabled_routes()
    names = [row["route_name"] for row in routes]
    assert names
    assert len(names) == len(set(names))
    assert all(row["route_name"] and row["input_pattern"] for row in routes)


def test_every_enabled_route_is_listed_in_test_ideas_document():
    document = TEST_IDEAS_DOC.read_text(encoding="utf-8")
    missing = [
        row["route_name"]
        for row in _enabled_routes()
        if f"`{row['route_name']}`" not in document
    ]
    assert missing == []


def test_every_enabled_route_pattern_is_valid():
    invalid = []
    for row in _enabled_routes():
        pattern = row["input_pattern"]
        try:
            if pattern.lstrip().startswith("{"):
                json.loads(pattern)
            else:
                re.compile(pattern)
        except (json.JSONDecodeError, re.error) as error:
            invalid.append((row["route_name"], str(error)))
    assert invalid == []
