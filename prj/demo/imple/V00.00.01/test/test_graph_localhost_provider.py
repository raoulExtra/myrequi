from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.request import urlopen
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import graph_tool
import graph_localhost_provider


class GraphLocalhostProviderTests(unittest.TestCase):
    def test_parse_cli(self):
        parsed = graph_localhost_provider.parse_cli(["--id", "1", "--host", "0.0.0.0", "--port", "9000"])
        self.assertEqual(parsed["db"], Path("assets/graph.db"))
        self.assertIsNone(parsed["file"])
        self.assertEqual(parsed["id"], 1)
        self.assertEqual(parsed["host"], "0.0.0.0")
        self.assertEqual(parsed["port"], 9000)

        parsed = graph_localhost_provider.parse_cli(["--db", "graphs.db", "--file", "graph.json", "--host", "127.0.0.1"])
        self.assertEqual(parsed["file"], Path("graph.json"))
        self.assertEqual(parsed["db"], Path("graphs.db"))

    def test_serve_graph_on_localhost(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "graphs.db"
            graph_file = tmp / "001-graph.json"
            graph_file.write_text(
                json.dumps(
                    {
                        "name": "g1",
                        "nodes": [
                            {"id": 1, "label": "Node 1", "color": "red", "style": "filled", "text": "first"},
                            {"id": 2, "label": "Node 2", "color": "blue", "style": "dashed", "text": "second"},
                        ],
                        "edges": [
                            {"from": 1, "to": 2, "label": "link", "color": "purple", "style": "dotted"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            graph_tool.init_db(db_path)
            load_report = graph_tool.load_graph(db_path, graph_file)
            server, thread = graph_localhost_provider.serve_graph(db_path, load_report["graph_id"], host="127.0.0.1", port=0)
            try:
                host, port = server.server_address
                root = urlopen(f"http://{host}:{port}/").read().decode("utf-8")
                dot = urlopen(f"http://{host}:{port}/graph.dot").read().decode("utf-8")
                self.assertIn("<svg", root)
                self.assertIn("Node 1", root)
                self.assertIn("digraph G", dot)
                self.assertIn("color=\"red\"", dot)
                self.assertIn("style=\"filled\"", dot)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_serve_graph_file_on_localhost(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            graph_file = tmp / "graph.json"
            graph_file.write_text(
                json.dumps(
                    {
                        "name": "direct-file",
                        "nodes": [
                            {"id": 1, "label": "A", "color": "red", "style": "filled"},
                            {"id": 2, "label": "B", "color": "blue", "style": "dashed"},
                        ],
                        "edges": [
                            {"from": 1, "to": 2, "label": "to", "color": "green", "style": "dotted"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            server, thread = graph_localhost_provider.serve_graph_file(graph_file, host="127.0.0.1", port=0)
            try:
                host, port = server.server_address
                root = urlopen(f"http://{host}:{port}/").read().decode("utf-8")
                self.assertIn("<svg", root)
                self.assertIn("A", root)
                self.assertIn('fill="red"', root)
                self.assertIn('stroke="red"', root)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_serve_dot_file_on_localhost(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            dot_file = tmp / "graph.dot"
            dot_file.write_text('digraph G { a -> b; }\n', encoding='utf-8')
            server, thread = graph_localhost_provider.serve_dot_file(dot_file, host="127.0.0.1", port=0)
            try:
                host, port = server.server_address
                root = urlopen(f"http://{host}:{port}/").read()
                self.assertTrue(root.startswith(b"\x89PNG"))
                self.assertGreater(len(root), 20)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
