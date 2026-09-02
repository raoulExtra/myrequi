from __future__ import annotations

# R1.10: These tests verify table-row-to-Markdown asset export behavior.
import json
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from table_row_markdown import export_source_markdown, main, markdown_asset_path, primary_key_columns, row_to_markdown, source_exists


class TableRowMarkdownExporterTests(unittest.TestCase):
    def test_markdown_asset_path_uses_assets_source_folder(self):
        path = markdown_asset_path(Path("assets"), "metacognitive_state", "primary_goal")
        self.assertEqual(path, Path("assets/metacognitive_state/primary_goal-metacognitive_state.md"))

    def test_source_exists_reads_table_and_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "demo.db"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("create table items(id integer primary key, name text)")
                conn.execute("create view item_names as select name from items")
                conn.commit()
                self.assertTrue(source_exists(conn, "items"))
                self.assertTrue(source_exists(conn, "item_names"))
                self.assertFalse(source_exists(conn, "missing"))
            finally:
                conn.close()

    def test_primary_key_columns_reads_single_pk(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "demo.db"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("create table items(id integer primary key, name text)")
                conn.commit()
                self.assertEqual(primary_key_columns(conn, "items"), ["id"])
            finally:
                conn.close()

    def test_row_to_markdown_includes_fields(self):
        md = row_to_markdown(
            "items",
            {"id": 7, "name": "alpha", "value": "beta"},
        )
        self.assertIn("# items row 7", md)
        self.assertIn("- id: 7", md)
        self.assertIn("- name: alpha", md)
        self.assertIn("- value: beta", md)

    def test_export_source_markdown_writes_files_for_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "demo.db"
            assets_root = tmp / "assets"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("create table items(id integer primary key, name text, value text)")
                conn.execute("insert into items(id, name, value) values(1, 'alpha', 'beta')")
                conn.execute("insert into items(id, name, value) values(2, 'gamma', 'delta')")
                conn.commit()
            finally:
                conn.close()

            out_paths = export_source_markdown(db_path, "items", assets_root=assets_root)
            self.assertEqual(len(out_paths), 2)
            self.assertEqual(out_paths[0], assets_root / "items" / "0001-items.md")
            self.assertEqual(out_paths[1], assets_root / "items" / "0002-items.md")
            self.assertTrue(out_paths[0].exists())
            self.assertTrue(out_paths[1].exists())
            self.assertIn("# items row 1", out_paths[0].read_text(encoding="utf-8"))

    def test_export_source_markdown_clears_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "demo.db"
            assets_root = tmp / "assets"
            target_dir = assets_root / "items"
            target_dir.mkdir(parents=True)
            stale = target_dir / "stale-items.md"
            stale.write_text("old", encoding="utf-8")
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("create table items(id integer primary key, name text, value text)")
                conn.execute("insert into items(id, name, value) values(1, 'alpha', 'beta')")
                conn.commit()
            finally:
                conn.close()

            out_paths = export_source_markdown(db_path, "items", assets_root=assets_root)
            self.assertFalse(stale.exists())
            self.assertEqual(out_paths, [assets_root / "items" / "0001-items.md"])

    def test_export_source_markdown_writes_files_for_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "demo.db"
            assets_root = tmp / "assets"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("create table metacognitive_state(state_key text primary key, category text, value text)")
                conn.execute("insert into metacognitive_state(state_key, category, value) values('primary_goal', 'goals', 'Learn')")
                conn.execute("create view state_view as select state_key, value from metacognitive_state")
                conn.commit()
            finally:
                conn.close()

            out_paths = export_source_markdown(db_path, "state_view", assets_root=assets_root)
            self.assertEqual(len(out_paths), 1)
            self.assertEqual(out_paths[0].name, "primary_goal-state_view.md")
            text = out_paths[0].read_text(encoding="utf-8")
            self.assertIn("# state_view row primary_goal", text)
            self.assertIn("- value: Learn", text)

    def test_main_prints_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "demo.db"
            assets_root = tmp / "assets"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("create table metacognitive_state(state_key text primary key, category text, value text)")
                conn.execute("insert into metacognitive_state(state_key, category, value) values('primary_goal', 'goals', 'Learn')")
                conn.commit()
            finally:
                conn.close()

            buf = StringIO()
            with redirect_stdout(buf):
                exit_code = main([
                    "--db", str(db_path),
                    "--assets-root", str(assets_root),
                    "--source", "metacognitive_state",
                    "--json",
                ])
            self.assertEqual(exit_code, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["source"], "metacognitive_state")
            self.assertEqual(payload["asset_paths"], [str(assets_root / "metacognitive_state" / "primary_goal-metacognitive_state.md")])


if __name__ == "__main__":
    unittest.main()
