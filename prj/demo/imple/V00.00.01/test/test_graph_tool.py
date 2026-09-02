from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import graph_tool
from graph_tool import compare_graph, export_graph, init_db, list_graphs, load_graph, parse_cli, run_algorithm


class GraphToolTests(unittest.TestCase):
    def test_parse_cli_supports_init_load_list_export_compare(self):
        parsed = parse_cli(["--db", "graphs.db", "--load", "001-graph.json"])
        self.assertEqual(parsed["db"], Path("graphs.db"))
        self.assertEqual(parsed["load"], Path("001-graph.json"))
        self.assertIsNone(parsed["list"])

        parsed = parse_cli(["--db", "graphs.db", "--list"])
        self.assertEqual(parsed["db"], Path("graphs.db"))
        self.assertTrue(parsed["list"])
        self.assertIsNone(parsed["id"])

        parsed = parse_cli(["--db", "graphs.db", "--list", "--id", "1"])
        self.assertEqual(parsed["id"], 1)

        parsed = parse_cli(["--db", "graphs.db", "--export"])
        self.assertEqual(parsed["export"], Path("out.json"))

        parsed = parse_cli(["--db", "graphs.db", "--compare", "file.json", "--id", "1"])
        self.assertEqual(parsed["compare"], Path("file.json"))
        self.assertEqual(parsed["id"], 1)

        parsed = parse_cli(["--db", "graphs.db", "--algo", "A*", "--start", "1", "--id", "1"])
        self.assertEqual(parsed["algo"], "A*")
        self.assertEqual(parsed["start"], "1")
        self.assertEqual(parsed["id"], 1)

        parsed = parse_cli(["--db", "graphs.db", "--algo", "A*", "--start", "1", "--goal", "3", "--id", "1"])
        self.assertEqual(parsed["goal"], "3")

    def test_init_load_list_export_and_compare(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "graphs.db"
            graph_file = tmp / "001-graph.json"
            graph_data = {
                "nodes": [
                    {"id": 1, "label": "Node 1", "weight": 1.0, "weight_int": 1, "text": "first"},
                    {"id": 2, "label": "Node 2", "weight": 2.0, "weight_int": 2, "text": "second"},
                    {"id": 3, "label": "Node 3", "weight": 3.0, "weight_int": 3, "text": "third"},
                ],
                "edges": [
                    {"from": 1, "to": 2, "label": "1 to 2", "weight": 1},
                    {"from": 2, "to": 3, "label": "2 to 3", "weight": 2},
                    {"from": 3, "to": 1, "label": "3 to 1", "weight": 3},
                ],
            }
            graph_file.write_text(json.dumps(graph_data), encoding="utf-8")

            init_db(db_path)
            report = load_graph(db_path, graph_file)
            self.assertEqual(report["graph_id"], 1)
            self.assertEqual(report["nodes_loaded"], 3)
            self.assertEqual(report["edges_loaded"], 3)
            self.assertEqual(report["warnings"], [])

            listing = list_graphs(db_path)
            self.assertEqual(len(listing), 1)
            self.assertEqual(listing[0]["graph_id"], 1)
            self.assertEqual(listing[0]["nodes"], 3)
            self.assertEqual(listing[0]["edges"], 3)

            with sqlite3.connect(db_path) as con:
                attr = con.execute(
                    "select attribute from node_attributes where graph_id = ? and node_id = ?",
                    (1, "1"),
                ).fetchone()
                self.assertEqual(attr[0], "first")
                row = con.execute(
                    "select weight, weight_int from graph_nodes where graph_id = ? and node_id = ?",
                    (1, "1"),
                ).fetchone()
                self.assertEqual(row[0], 1.0)
                self.assertEqual(row[1], 1)

            out_file = tmp / "out.json"
            export_report = export_graph(db_path, 1, out_file)
            self.assertEqual(export_report["graph_id"], 1)
            self.assertTrue(out_file.exists())
            self.assertEqual(json.loads(out_file.read_text(encoding="utf-8")), graph_data)

            old_cwd = Path.cwd()
            try:
                os.chdir(tmp)
                self.assertEqual(graph_tool.main(["--db", str(db_path), "--export", "--id", "1"]), 0)
            finally:
                os.chdir(old_cwd)
            self.assertEqual(json.loads((tmp / "out.json").read_text(encoding="utf-8")), graph_data)

            compare_report = compare_graph(db_path, 1, graph_file)
            self.assertTrue(compare_report["equal"])

            algo_report = run_algorithm(db_path, 1, "A*", 1)
            self.assertEqual(algo_report["graph_id"], 1)
            self.assertEqual(algo_report["path"], [1, 2, 3])
            self.assertEqual(algo_report["start"], 1)
            self.assertEqual(algo_report["goal"], 3)

            algo_report2 = run_algorithm(db_path, 1, "A*", 1, 3)
            self.assertEqual(algo_report2["goal"], 3)

    def test_load_warns_on_missing_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "graphs.db"
            graph_file = tmp / "001-graph.json"
            graph_file.write_text(
                json.dumps(
                    {
                        "nodes": [{"id": 1, "label": "Node 1", "weight": 1}],
                        "edges": [{"from": 1, "to": 2, "weight": 1}],
                    }
                ),
                encoding="utf-8",
            )

            init_db(db_path)
            report = load_graph(db_path, graph_file)
            self.assertIn("missing node", " ".join(report["warnings"]))


if __name__ == "__main__":
    unittest.main()
