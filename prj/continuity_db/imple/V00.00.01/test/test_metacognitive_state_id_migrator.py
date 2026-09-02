from __future__ import annotations

import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from metacognitive_state_id_migrator import migrate_metacognitive_state_id, create_new_metacognitive_state_table


class MetacognitiveStateIdMigratorTests(unittest.TestCase):
    def test_migrate_adds_numeric_id_and_keeps_state_key_unique(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "demo.db"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    """
                    create table metacognitive_state(
                      state_key text primary key,
                      category text not null,
                      value text not null,
                      confidence real not null,
                      provenance text not null,
                      version integer not null default 1,
                      updated_at text not null default current_timestamp
                    )
                    """
                )
                conn.execute("insert into metacognitive_state(state_key, category, value, confidence, provenance, version) values('primary_goal', 'goals', 'Learn', 0.9, 'seed', 1)")
                conn.execute("insert into metacognitive_state(state_key, category, value, confidence, provenance, version) values('current_focus', 'attention', 'Read', 0.8, 'seed', 1)")
                conn.commit()

                changed = migrate_metacognitive_state_id(conn)
                conn.commit()

                self.assertEqual(changed, 2)
                info = conn.execute("pragma table_info(metacognitive_state)").fetchall()
                self.assertEqual(info[0][1], 'id')
                self.assertEqual(info[0][5], 1)
                self.assertEqual(info[1][1], 'state_key')
                rows = conn.execute("select id, state_key, value from metacognitive_state order by id").fetchall()
                self.assertEqual(rows[0][0], 1)
                self.assertEqual(rows[0][1], 'primary_goal')
                self.assertEqual(rows[1][0], 2)
                self.assertEqual(rows[1][1], 'current_focus')
            finally:
                conn.close()

    def test_migrate_preserves_triggers(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "demo.db"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    """
                    create table metacognitive_state(
                      state_key text primary key,
                      category text not null,
                      value text not null,
                      confidence real not null,
                      provenance text not null,
                      version integer not null default 1,
                      updated_at text not null default current_timestamp
                    )
                    """
                )
                conn.execute("create table audit(msg text)")
                conn.execute(
                    """
                    create trigger metacognitive_state_audit after insert on metacognitive_state
                    begin
                      insert into audit(msg) values(new.state_key);
                    end;
                    """
                )
                conn.execute("insert into metacognitive_state(state_key, category, value, confidence, provenance, version) values('primary_goal', 'goals', 'Learn', 0.9, 'seed', 1)")
                conn.commit()

                migrate_metacognitive_state_id(conn)
                conn.execute("insert into metacognitive_state(state_key, category, value, confidence, provenance, version) values('new_focus', 'attention', 'Think', 0.8, 'seed', 1)")
                conn.commit()

                audit = conn.execute("select msg from audit order by rowid").fetchall()
                self.assertEqual([row[0] for row in audit], ['primary_goal', 'new_focus'])
            finally:
                conn.close()

    def test_migrate_works_on_real_db_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "continuity.db"
            shutil.copy2(REPO_ROOT / "continuity.db", db_path)
            conn = sqlite3.connect(db_path)
            try:
                migrated = migrate_metacognitive_state_id(conn)
                conn.commit()
                self.assertGreater(migrated, 0)
                info = conn.execute("pragma table_info(metacognitive_state)").fetchall()
                self.assertEqual(info[0][1], 'id')
                self.assertEqual(info[0][5], 1)
                self.assertEqual(info[1][1], 'state_key')
                rows = conn.execute("select id, state_key from metacognitive_state order by id limit 3").fetchall()
                self.assertGreaterEqual(len(rows), 1)
                self.assertEqual(rows[0][0], 1)
            finally:
                conn.close()

    def test_create_new_metacognitive_state_table_has_id_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "demo.db"
            conn = sqlite3.connect(db_path)
            try:
                create_new_metacognitive_state_table(conn)
                info = conn.execute("pragma table_info(metacognitive_state)").fetchall()
                self.assertEqual(info[0][1], 'id')
                self.assertEqual(info[0][5], 1)
                self.assertEqual(info[1][1], 'state_key')
                self.assertEqual(info[1][3], 1)
            finally:
                conn.close()


if __name__ == '__main__':
    unittest.main()
