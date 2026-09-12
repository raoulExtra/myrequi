import sqlite3
import tempfile
import unittest
from pathlib import Path

from chat_trace_poller import _auto_delivery_enabled


class ChatTracePollerTests(unittest.TestCase):
    def test_auto_delivery_flag_is_read_dynamically(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "continuity.db"
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE TABLE feature_flags (feature_key TEXT PRIMARY KEY, enabled INTEGER)")
                conn.execute("INSERT INTO feature_flags VALUES ('chat_trace_auto', 0)")
                conn.commit()

            self.assertFalse(_auto_delivery_enabled(db_path))
            with sqlite3.connect(db_path) as conn:
                conn.execute("UPDATE feature_flags SET enabled=1 WHERE feature_key='chat_trace_auto'")
                conn.commit()
            self.assertTrue(_auto_delivery_enabled(db_path))


if __name__ == "__main__":
    unittest.main()
