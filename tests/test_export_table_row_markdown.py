import sqlite3
import tempfile
import unittest
from pathlib import Path

from thinker.export_table_row_markdown import (
    export_table_row_markdown,
    markdown_asset_path,
    primary_key_values,
    row_to_markdown,
)


class ExportTableRowMarkdownTests(unittest.TestCase):
    def test_markdown_asset_path_uses_assets_table_folder(self):
        path = markdown_asset_path(Path("assets"), "metacognitive_state", "primary_goal")
        self.assertEqual(path, Path("assets/metacognitive_state/primary_goal-metacognitive_state.md"))

    def test_row_to_markdown_includes_fields(self):
        md = row_to_markdown(
            "items",
            {"id": 7, "name": "alpha", "value": "beta"},
        )
        self.assertIn("# items row 7", md)
        self.assertIn("- id: 7", md)
        self.assertIn("- name: alpha", md)
        self.assertIn("- value: beta", md)

    def test_export_table_row_markdown_writes_file_for_integer_pk(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "demo.db"
            assets_root = tmp / "assets"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("create table items(id integer primary key, name text, value text)")
                conn.execute("insert into items(id, name, value) values(1, 'alpha', 'beta')")
                conn.commit()
            finally:
                conn.close()

            out_path = export_table_row_markdown(db_path, "items", 1, assets_root=assets_root)
            self.assertEqual(out_path, assets_root / "items" / "1-items.md")
            self.assertTrue(out_path.exists())
            text = out_path.read_text(encoding="utf-8")
            self.assertIn("# items row 1", text)
            self.assertIn("- name: alpha", text)

    def test_export_table_row_markdown_uses_text_primary_key(self):
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

            out_path = export_table_row_markdown(db_path, "metacognitive_state", "primary_goal", assets_root=assets_root)
            self.assertEqual(out_path, assets_root / "metacognitive_state" / "primary_goal-metacognitive_state.md")
            text = out_path.read_text(encoding="utf-8")
            self.assertIn("# metacognitive_state row primary_goal", text)
            self.assertIn("- category: goals", text)
            self.assertIn("- value: Learn", text)

    def test_primary_key_values_handles_composite_pk(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "demo.db"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("create table links(left_id integer, right_id integer, label text, primary key(left_id, right_id))")
                conn.execute("insert into links(left_id, right_id, label) values(2, 3, 'pair')")
                conn.commit()
                row = conn.execute("select * from links").fetchone()
                values = primary_key_values(conn, "links", row)
            finally:
                conn.close()
            self.assertEqual(values, [2, 3])


if __name__ == "__main__":
    unittest.main()
