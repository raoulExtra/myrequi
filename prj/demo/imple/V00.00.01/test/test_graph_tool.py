from __future__ import annotations

import ast
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

import graph_tool
from graph_tool import compare_graph, export_graph, init_db, list_graphs, load_graph, parse_cli, run_algorithm
import py_from_ast
import java_from_ast


class GraphToolTests(unittest.TestCase):
    def test_parse_cli_supports_init_load_list_export_compare(self):
        parsed = parse_cli(["--load", "001-graph.json"])
        self.assertEqual(parsed["db"], Path("assets/graph.db"))
        self.assertEqual(parsed["load"], Path("001-graph.json"))
        self.assertIsNone(parsed["list"])

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

        parsed = parse_cli(["--db", "graphs.db", "--py", "--id", "1"])
        self.assertTrue(parsed["py"])

        parsed = parse_cli(["--db", "graphs.db", "--rs", "--id", "1"])
        self.assertTrue(parsed["rs"])

        parsed = parse_cli(["--db", "graphs.db", "--name", "001-graph", "--id", "1"])
        self.assertEqual(parsed["name"], "001-graph")

        parsed = parse_cli(["--db", "graphs.db", "-gviz", "--id", "1"])
        self.assertEqual(parsed["gviz"], Path("assets/graph"))

        parsed = parse_cli(["--db", "graphs.db", "--algo", "beam", "--start", "1", "--beam-width", "2", "--filter-min-weight", "2", "--id", "1"])
        self.assertEqual(parsed["beam_width"], 2)
        self.assertEqual(parsed["filter_min_weight"], 2.0)

    def test_rust_graph_schema_is_rich_enough(self):
        schema_file = ROOT / "rust_from_ast_tool" / "rust_graph_schema.json"
        self.assertTrue(schema_file.exists())
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        kinds = {row["kind"] for row in schema["node_kinds"]}
        for required in {"Module", "File", "Use", "Struct", "Enum", "Trait", "Impl", "Function", "Match", "Let", "If", "For", "While", "Block", "StructExpr", "TypePath", "Comment", "DocComment"}:
            self.assertIn(required, kinds)
        labels = set(schema["edge_labels"])
        for required in {"body", "params", "args", "fields", "variants", "return_type", "value", "target", "pattern", "segments"}:
            self.assertIn(required, labels)

    def test_main_supports_rust_source_graph(self):
        graph_file = ROOT / "rust_from_ast_tool" / "src" / "main.rs.graph.detailed.json"
        self.assertTrue(graph_file.exists())
        graph = json.loads(graph_file.read_text(encoding="utf-8"))
        self.assertEqual(graph["source_file"], "src/main.rs")
        kinds = {node["label"] for node in graph["nodes"]}
        self.assertIn("Module", kinds)
        self.assertIn("Impl", kinds)
        self.assertIn("Function", kinds)
        self.assertIn("Section", kinds)
        self.assertIn("Subsection", kinds)
        self.assertGreaterEqual(len(graph["nodes"]), 120)
        self.assertGreaterEqual(len(graph["edges"]), 180)

    def test_main_supports_rust_comments_and_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "graphs.db"
            graph_file = tmp / "042-rust-ast-comments-graph.json"
            graph_data = {
                "name": "rust-comments-demo",
                "nodes": [
                    {"id": 1, "label": "Module", "text": "Module"},
                    {"id": 2, "label": "DocComment", "text": "Adds two numbers."},
                    {"id": 3, "label": "Function", "text": "add"},
                    {"id": 4, "label": "Param", "text": "a: i32"},
                    {"id": 5, "label": "Param", "text": "b: i32"},
                    {"id": 6, "label": "Comment", "text": "sum the inputs"},
                    {"id": 7, "label": "Return", "text": "Return"},
                    {"id": 8, "label": "BinaryExpr", "text": "+"},
                    {"id": 9, "label": "Name", "text": "a"},
                    {"id": 10, "label": "Add", "text": "+"},
                    {"id": 11, "label": "Name", "text": "b"},
                ],
                "edges": [
                    {"from": 1, "to": 2, "label": "body", "order": 1},
                    {"from": 1, "to": 3, "label": "body", "order": 2},
                    {"from": 3, "to": 4, "label": "params", "order": 1},
                    {"from": 3, "to": 5, "label": "params", "order": 2},
                    {"from": 3, "to": 6, "label": "body", "order": 1},
                    {"from": 3, "to": 7, "label": "body", "order": 2},
                    {"from": 7, "to": 8, "label": "value", "order": 1},
                    {"from": 8, "to": 9, "label": "left", "order": 1},
                    {"from": 8, "to": 10, "label": "op", "order": 1},
                    {"from": 8, "to": 11, "label": "right", "order": 1},
                ],
            }
            graph_file.write_text(json.dumps(graph_data), encoding="utf-8")
            init_db(db_path)
            load_graph(db_path, graph_file)
            old_cwd = Path.cwd()
            try:
                os.chdir(tmp)
                self.assertEqual(graph_tool.main(["--db", str(db_path), "--rs", "--id", "42"]), 0)
            finally:
                os.chdir(old_cwd)
            out_file = tmp / "compare.rs"
            self.assertTrue(out_file.exists())
            self.assertEqual(
                out_file.read_text(encoding="utf-8"),
                "/// Adds two numbers.\nfn add(a: i32, b: i32) {\n    // sum the inputs\n    return a + b;\n}\n",
            )

    def test_init_load_list_export_and_compare(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "graphs.db"
            graph_file = tmp / "001-graph.json"
            graph_data = {
                "name": "demo-graph",
                "nodes": [
                    {"id": 1, "label": "Node 1", "color": "red", "style": "filled", "weight": 1.0, "weight_int": 1, "text": "first"},
                    {"id": 2, "label": "Node 2", "color": "blue", "style": "dashed", "weight": 2.0, "weight_int": 2, "text": "second"},
                    {"id": 3, "label": "Node 3", "color": "green", "style": "bold", "weight": 3.0, "weight_int": 3, "text": "third"},
                ],
                "edges": [
                    {"from": 1, "to": 2, "label": "1 to 2", "color": "purple", "style": "dotted", "weight": 1},
                    {"from": 2, "to": 3, "label": "2 to 3", "color": "orange", "style": "solid", "weight": 2},
                    {"from": 3, "to": 1, "label": "3 to 1", "color": "black", "style": "bold", "weight": 3},
                ],
            }
            graph_file.write_text(json.dumps(graph_data), encoding="utf-8")

            init_db(db_path)
            report = load_graph(db_path, graph_file)
            self.assertEqual(report["graph_id"], 1)
            self.assertEqual(report["graph_name"], "demo-graph")
            self.assertEqual(report["nodes_loaded"], 3)
            self.assertEqual(report["edges_loaded"], 3)
            self.assertEqual(report["warnings"], [])

            listing = list_graphs(db_path)
            self.assertEqual(len(listing), 1)
            self.assertEqual(listing[0]["graph_id"], 1)
            self.assertEqual(listing[0]["graph_name"], "demo-graph")
            self.assertEqual(listing[0]["nodes"], 3)
            self.assertEqual(listing[0]["edges"], 3)

            with sqlite3.connect(db_path) as con:
                attr = con.execute(
                    "select attribute from node_attributes where graph_id = ? and node_id = ?",
                    (1, "1"),
                ).fetchone()
                self.assertEqual(attr[0], "first")
                row = con.execute(
                    "select color, style, weight, weight_int from graph_nodes where graph_id = ? and node_id = ?",
                    (1, "1"),
                ).fetchone()
                self.assertEqual(row[0], "red")
                self.assertEqual(row[1], "filled")
                self.assertEqual(row[2], 1.0)
                self.assertEqual(row[3], 1)

            out_file = tmp / "out.json"
            export_report = export_graph(db_path, 1, out_file)
            self.assertEqual(export_report["graph_id"], 1)
            self.assertTrue(out_file.exists())
            self.assertEqual(json.loads(out_file.read_text(encoding="utf-8")), {k: v for k, v in graph_data.items() if k != 'name'})

            old_cwd = Path.cwd()
            try:
                os.chdir(tmp)
                self.assertEqual(graph_tool.main(["--db", str(db_path), "--export", "--id", "1"]), 0)
            finally:
                os.chdir(old_cwd)
            self.assertEqual(json.loads((tmp / "out.json").read_text(encoding="utf-8")), {k: v for k, v in graph_data.items() if k != 'name'})

            old_cwd = Path.cwd()
            try:
                os.chdir(tmp)
                self.assertEqual(graph_tool.main(["--db", str(db_path), "--export", "--name", "demo-graph"]), 0)
            finally:
                os.chdir(old_cwd)
            self.assertEqual(json.loads((tmp / "out.json").read_text(encoding="utf-8")), {k: v for k, v in graph_data.items() if k != 'name'})


            compare_report = compare_graph(db_path, 1, graph_file)
            self.assertTrue(compare_report["equal"])

            old_cwd = Path.cwd()
            try:
                os.chdir(tmp)
                self.assertEqual(graph_tool.main(["--db", str(db_path), "-gviz", "--id", "1"]), 0)
            finally:
                os.chdir(old_cwd)
            dot_file = tmp / "assets" / "graph.dot"
            svg_file = tmp / "assets" / "graph.svg"
            self.assertTrue(dot_file.exists())
            self.assertTrue(svg_file.exists())
            self.assertIn("digraph G", dot_file.read_text(encoding="utf-8"))
            dot_text = dot_file.read_text(encoding="utf-8")
            svg_text = svg_file.read_text(encoding="utf-8")
            self.assertIn("Node 1", dot_text)
            self.assertIn("label=\"Node 1\\nfirst\"", dot_text)
            self.assertIn("tooltip=\"weight_int=1 | weight=1\"", dot_text)
            self.assertIn("color=\"red\"", dot_text)
            self.assertIn("style=\"filled\"", dot_text)
            self.assertIn("color=\"purple\"", dot_text)
            self.assertIn("style=\"dotted\"", dot_text)
            self.assertIn("<svg", svg_text)

            algo_report = run_algorithm(db_path, 1, "A*", 1)
            self.assertEqual(algo_report["graph_id"], 1)
            self.assertEqual(algo_report["path"], [1, 2, 3])
            self.assertEqual(algo_report["start"], 1)
            self.assertEqual(algo_report["goal"], 3)

            algo_report2 = run_algorithm(db_path, 1, "A*", 1, 3)
            self.assertEqual(algo_report2["goal"], 3)

    def test_color_style_fields_have_length_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "graphs.db"
            graph_file = tmp / "001-graph.json"
            graph_data = {
                "name": "styled-graph",
                "nodes": [
                    {"id": 1, "label": "Node 1", "color": "x" * 257, "weight": 1.0},
                ],
                "edges": [],
            }
            graph_file.write_text(json.dumps(graph_data), encoding="utf-8")
            init_db(db_path)
            with self.assertRaises(SystemExit):
                load_graph(db_path, graph_file)

    def test_py_from_ast_module_builds_typical_ast(self):
        graph_file = REPO_ROOT / "prj/demo/examples/030-py-ast-assign-graph.json"
        self.assertTrue(graph_file.exists())
        graph_data = json.loads(graph_file.read_text(encoding="utf-8"))
        tree = py_from_ast.graph_to_ast(graph_data)
        self.assertIsInstance(tree, ast.Module)
        rendered = ast.dump(tree, include_attributes=False)
        self.assertIn("Assign", rendered)
        self.assertIn("Name(id='x', ctx=Store())", rendered)
        self.assertIn("Constant(value=1)", rendered)

        source = py_from_ast.to_dump(graph_data)
        self.assertIn("Module(", source)

    def test_py_from_ast_module_handles_graph_syntax_counterpart(self):
        graph_file = REPO_ROOT / "prj/demo/examples/033-graph_tool-module-ast-graph.json"
        self.assertTrue(graph_file.exists())
        graph_data = json.loads(graph_file.read_text(encoding="utf-8"))
        tree = py_from_ast.graph_to_ast(graph_data)
        self.assertIsInstance(tree, ast.Module)
        rendered = ast.dump(tree, include_attributes=False)
        self.assertIn("FunctionDef(name='init_db'", rendered)
        self.assertIn("FunctionDef(name='main'", rendered)
        self.assertIn("Return(value=Constant(value='graph list'))", rendered)

    def test_py_from_ast_respects_explicit_edge_order(self):
        graph_data = {
            "nodes": [
                {"id": 1, "label": "Module", "text": "Module"},
                {"id": 2, "label": "Expr", "text": "Expr"},
                {"id": 3, "label": "Constant", "text": "first"},
                {"id": 4, "label": "Expr", "text": "Expr"},
                {"id": 5, "label": "Constant", "text": "second"},
            ],
            "edges": [
                {"from": 1, "to": 4, "label": "body", "order": 2},
                {"from": 4, "to": 5, "label": "value", "order": 1},
                {"from": 1, "to": 2, "label": "body", "order": 1},
                {"from": 2, "to": 3, "label": "value", "order": 1},
            ],
        }
        tree = py_from_ast.graph_to_ast(graph_data)
        rendered = ast.dump(tree, include_attributes=False)
        self.assertTrue(rendered.index("Constant(value='first')") < rendered.index("Constant(value='second')"))

    def test_py_from_ast_supports_import_and_try(self):
        graph_data = {
            "nodes": [
                {"id": 1, "label": "Module", "text": "Module"},
                {"id": 2, "label": "Import", "text": "Import"},
                {"id": 3, "label": "alias", "name": "sys", "text": "sys"},
                {"id": 4, "label": "ImportFrom", "module": "pathlib", "level": 0, "text": "pathlib"},
                {"id": 5, "label": "alias", "name": "Path", "text": "Path"},
                {"id": 6, "label": "Try", "text": "Try"},
                {"id": 7, "label": "Expr", "text": "Expr"},
                {"id": 8, "label": "Call", "text": "Call"},
                {"id": 9, "label": "Name", "text": "print"},
                {"id": 10, "label": "Load", "text": "Load"},
                {"id": 11, "label": "Constant", "text": "ok"},
                {"id": 12, "label": "ExceptHandler", "name": "exc", "text": "ExceptHandler"},
                {"id": 13, "label": "Name", "text": "Exception"},
                {"id": 14, "label": "Load", "text": "Load"},
                {"id": 15, "label": "Expr", "text": "Expr"},
                {"id": 16, "label": "Call", "text": "Call"},
                {"id": 17, "label": "Name", "text": "print"},
                {"id": 18, "label": "Load", "text": "Load"},
                {"id": 19, "label": "Constant", "text": "bad"},
                {"id": 20, "label": "Expr", "text": "Expr"},
                {"id": 21, "label": "Call", "text": "Call"},
                {"id": 22, "label": "Name", "text": "print"},
                {"id": 23, "label": "Load", "text": "Load"},
                {"id": 24, "label": "Constant", "text": "done"},
            ],
            "edges": [
                {"from": 1, "to": 2, "label": "body", "order": 1},
                {"from": 2, "to": 3, "label": "names", "order": 1},
                {"from": 1, "to": 4, "label": "body", "order": 2},
                {"from": 4, "to": 5, "label": "names", "order": 1},
                {"from": 1, "to": 6, "label": "body", "order": 3},
                {"from": 6, "to": 7, "label": "body", "order": 1},
                {"from": 7, "to": 8, "label": "value", "order": 1},
                {"from": 8, "to": 9, "label": "func", "order": 1},
                {"from": 9, "to": 10, "label": "ctx", "order": 1},
                {"from": 8, "to": 11, "label": "args", "order": 1},
                {"from": 6, "to": 12, "label": "handlers", "order": 1},
                {"from": 12, "to": 13, "label": "type", "order": 1},
                {"from": 13, "to": 14, "label": "ctx", "order": 1},
                {"from": 12, "to": 15, "label": "body", "order": 1},
                {"from": 15, "to": 16, "label": "value", "order": 1},
                {"from": 16, "to": 17, "label": "func", "order": 1},
                {"from": 17, "to": 18, "label": "ctx", "order": 1},
                {"from": 16, "to": 19, "label": "args", "order": 1},
                {"from": 6, "to": 20, "label": "finalbody", "order": 1},
                {"from": 20, "to": 21, "label": "value", "order": 1},
                {"from": 21, "to": 22, "label": "func", "order": 1},
                {"from": 22, "to": 23, "label": "ctx", "order": 1},
                {"from": 21, "to": 24, "label": "args", "order": 1},
            ],
        }
        tree = py_from_ast.graph_to_ast(graph_data)
        rendered = ast.dump(tree, include_attributes=False)
        self.assertIn("Import(names=[alias(name='sys')])", rendered)
        self.assertIn("ImportFrom(module='pathlib', names=[alias(name='Path')], level=0)", rendered)
        self.assertIn("Try(", rendered)
        self.assertIn("ExceptHandler(type=Name(id='Exception', ctx=Load()), name='exc'", rendered)

    def test_py_from_ast_supports_control_flow_and_literals(self):
        graph_data = {
            "nodes": [
                {"id": 1, "label": "Module", "text": "Module"},
                {"id": 2, "label": "Expr", "text": "Expr"},
                {"id": 3, "label": "List", "text": "List"},
                {"id": 4, "label": "Constant", "text": "1"},
                {"id": 5, "label": "Constant", "text": "2"},
                {"id": 6, "label": "Expr", "text": "Expr"},
                {"id": 7, "label": "Tuple", "text": "Tuple"},
                {"id": 8, "label": "Constant", "text": "a"},
                {"id": 9, "label": "Constant", "text": "b"},
                {"id": 10, "label": "Expr", "text": "Expr"},
                {"id": 11, "label": "Dict", "text": "Dict"},
                {"id": 12, "label": "Constant", "text": "k"},
                {"id": 13, "label": "Constant", "text": "v"},
                {"id": 14, "label": "Expr", "text": "Expr"},
                {"id": 15, "label": "Set", "text": "Set"},
                {"id": 16, "label": "Constant", "text": "x"},
                {"id": 17, "label": "For", "text": "For"},
                {"id": 18, "label": "Name", "text": "item"},
                {"id": 19, "label": "Store", "text": "Store"},
                {"id": 20, "label": "Name", "text": "items"},
                {"id": 21, "label": "Load", "text": "Load"},
                {"id": 22, "label": "Pass", "text": "Pass"},
                {"id": 23, "label": "While", "text": "While"},
                {"id": 24, "label": "Name", "text": "ready"},
                {"id": 25, "label": "Load", "text": "Load"},
                {"id": 26, "label": "Break", "text": "Break"},
                {"id": 27, "label": "Match", "text": "Match"},
                {"id": 28, "label": "Name", "text": "kind"},
                {"id": 29, "label": "Load", "text": "Load"},
                {"id": 30, "label": "match_case", "text": "match_case"},
                {"id": 31, "label": "MatchValue", "text": "MatchValue"},
                {"id": 32, "label": "Constant", "text": "a"},
                {"id": 33, "label": "Expr", "text": "Expr"},
                {"id": 34, "label": "Constant", "text": "alpha"},
                {"id": 35, "label": "Expr", "text": "Expr"},
                {"id": 36, "label": "IfExp", "text": "IfExp"},
                {"id": 37, "label": "Name", "text": "flag"},
                {"id": 38, "label": "Load", "text": "Load"},
                {"id": 39, "label": "Constant", "text": "yes"},
                {"id": 40, "label": "Constant", "text": "no"},
                {"id": 41, "label": "Expr", "text": "Expr"},
                {"id": 42, "label": "Lambda", "text": "Lambda"},
                {"id": 43, "label": "arguments", "text": "arguments"},
                {"id": 44, "label": "arg", "text": "x"},
                {"id": 45, "label": "BinOp", "text": "BinOp"},
                {"id": 46, "label": "Name", "text": "x"},
                {"id": 47, "label": "Load", "text": "Load"},
                {"id": 48, "label": "Add", "text": "Add"},
                {"id": 49, "label": "Constant", "text": "1"},
                {"id": 50, "label": "Expr", "text": "Expr"},
                {"id": 51, "label": "ListComp", "text": "ListComp"},
                {"id": 52, "label": "Name", "text": "x"},
                {"id": 53, "label": "Load", "text": "Load"},
                {"id": 54, "label": "comprehension", "text": "comprehension"},
                {"id": 55, "label": "Name", "text": "xs"},
                {"id": 56, "label": "Load", "text": "Load"},
            ],
            "edges": [
                {"from": 1, "to": 2, "label": "body", "order": 1},
                {"from": 2, "to": 3, "label": "value", "order": 1},
                {"from": 3, "to": 4, "label": "elts", "order": 1},
                {"from": 3, "to": 5, "label": "elts", "order": 2},
                {"from": 1, "to": 6, "label": "body", "order": 2},
                {"from": 6, "to": 7, "label": "value", "order": 1},
                {"from": 7, "to": 8, "label": "elts", "order": 1},
                {"from": 7, "to": 9, "label": "elts", "order": 2},
                {"from": 1, "to": 10, "label": "body", "order": 3},
                {"from": 10, "to": 11, "label": "value", "order": 1},
                {"from": 11, "to": 12, "label": "keys", "order": 1},
                {"from": 11, "to": 13, "label": "values", "order": 1},
                {"from": 1, "to": 14, "label": "body", "order": 4},
                {"from": 14, "to": 15, "label": "value", "order": 1},
                {"from": 15, "to": 16, "label": "elts", "order": 1},
                {"from": 1, "to": 17, "label": "body", "order": 5},
                {"from": 17, "to": 18, "label": "target", "order": 1},
                {"from": 18, "to": 19, "label": "ctx", "order": 1},
                {"from": 17, "to": 20, "label": "iter", "order": 1},
                {"from": 20, "to": 21, "label": "ctx", "order": 1},
                {"from": 17, "to": 22, "label": "body", "order": 1},
                {"from": 1, "to": 23, "label": "body", "order": 6},
                {"from": 23, "to": 24, "label": "test", "order": 1},
                {"from": 24, "to": 25, "label": "ctx", "order": 1},
                {"from": 23, "to": 26, "label": "body", "order": 1},
                {"from": 1, "to": 27, "label": "body", "order": 7},
                {"from": 27, "to": 28, "label": "subject", "order": 1},
                {"from": 28, "to": 29, "label": "ctx", "order": 1},
                {"from": 27, "to": 30, "label": "cases", "order": 1},
                {"from": 30, "to": 31, "label": "pattern", "order": 1},
                {"from": 31, "to": 32, "label": "value", "order": 1},
                {"from": 30, "to": 33, "label": "body", "order": 1},
                {"from": 33, "to": 34, "label": "value", "order": 1},
                {"from": 1, "to": 35, "label": "body", "order": 8},
                {"from": 35, "to": 36, "label": "value", "order": 1},
                {"from": 36, "to": 37, "label": "test", "order": 1},
                {"from": 37, "to": 38, "label": "ctx", "order": 1},
                {"from": 36, "to": 39, "label": "body", "order": 1},
                {"from": 36, "to": 40, "label": "orelse", "order": 1},
                {"from": 1, "to": 41, "label": "body", "order": 9},
                {"from": 41, "to": 42, "label": "value", "order": 1},
                {"from": 42, "to": 43, "label": "args", "order": 1},
                {"from": 43, "to": 44, "label": "args", "order": 1},
                {"from": 42, "to": 45, "label": "body", "order": 1},
                {"from": 45, "to": 46, "label": "left", "order": 1},
                {"from": 46, "to": 47, "label": "ctx", "order": 1},
                {"from": 45, "to": 48, "label": "op", "order": 1},
                {"from": 45, "to": 49, "label": "right", "order": 1},
                {"from": 1, "to": 50, "label": "body", "order": 10},
                {"from": 50, "to": 51, "label": "value", "order": 1},
                {"from": 51, "to": 52, "label": "elt", "order": 1},
                {"from": 52, "to": 53, "label": "ctx", "order": 1},
                {"from": 51, "to": 54, "label": "generators", "order": 1},
                {"from": 54, "to": 55, "label": "iter", "order": 1},
                {"from": 55, "to": 56, "label": "ctx", "order": 1},
            ],
        }
        tree = py_from_ast.graph_to_ast(graph_data)
        rendered = ast.dump(tree, include_attributes=False)
        self.assertIn("List(elts=[Constant(value=1), Constant(value=2)], ctx=Load())", rendered)
        self.assertIn("Tuple(elts=[Constant(value='a'), Constant(value='b')], ctx=Load())", rendered)
        self.assertIn("Dict(keys=[Constant(value='k')], values=[Constant(value='v')])", rendered)
        self.assertIn("Set(elts=[Constant(value='x')])", rendered)
        self.assertIn("For(target=Name(id='item', ctx=Store())", rendered)
        self.assertIn("While(test=Name(id='ready', ctx=Load())", rendered)
        self.assertIn("Match(subject=Name(id='kind', ctx=Load())", rendered)
        self.assertIn("IfExp(test=Name(id='flag', ctx=Load())", rendered)
        self.assertIn("Lambda(args=arguments(args=[arg(arg='x')]), body=BinOp(", rendered)
        self.assertIn("ListComp(elt=Name(id='x', ctx=Load()), generators=[comprehension(", rendered)

    def test_py_from_ast_supports_async_yield_and_annotations(self):
        graph_data = {
            "nodes": [
                {"id": 1, "label": "Module", "text": "Module"},
                {"id": 2, "label": "AsyncFunctionDef", "text": "fetch"},
                {"id": 3, "label": "arguments", "text": "arguments"},
                {"id": 4, "label": "arg", "text": "url"},
                {"id": 5, "label": "Expr", "text": "Expr"},
                {"id": 6, "label": "Await", "text": "Await"},
                {"id": 7, "label": "Call", "text": "Call"},
                {"id": 8, "label": "Name", "text": "download"},
                {"id": 9, "label": "Load", "text": "Load"},
                {"id": 10, "label": "Name", "text": "url"},
                {"id": 11, "label": "Load", "text": "Load"},
                {"id": 12, "label": "AnnAssign", "text": "AnnAssign"},
                {"id": 13, "label": "Name", "text": "count"},
                {"id": 14, "label": "Store", "text": "Store"},
                {"id": 15, "label": "Name", "text": "int"},
                {"id": 16, "label": "Load", "text": "Load"},
                {"id": 17, "label": "Constant", "text": "1"},
                {"id": 18, "label": "Assert", "text": "Assert"},
                {"id": 19, "label": "Name", "text": "ready"},
                {"id": 20, "label": "Load", "text": "Load"},
                {"id": 21, "label": "Constant", "text": "bad"},
                {"id": 22, "label": "Delete", "text": "Delete"},
                {"id": 23, "label": "Name", "text": "temp"},
                {"id": 24, "label": "Del", "text": "Del"},
                {"id": 25, "label": "Expr", "text": "Expr"},
                {"id": 26, "label": "YieldFrom", "text": "YieldFrom"},
                {"id": 27, "label": "Name", "text": "stream"},
                {"id": 28, "label": "Load", "text": "Load"},
            ],
            "edges": [
                {"from": 1, "to": 2, "label": "body", "order": 1},
                {"from": 2, "to": 3, "label": "args", "order": 1},
                {"from": 3, "to": 4, "label": "args", "order": 1},
                {"from": 2, "to": 5, "label": "body", "order": 1},
                {"from": 5, "to": 6, "label": "value", "order": 1},
                {"from": 6, "to": 7, "label": "value", "order": 1},
                {"from": 7, "to": 8, "label": "func", "order": 1},
                {"from": 8, "to": 9, "label": "ctx", "order": 1},
                {"from": 7, "to": 10, "label": "args", "order": 1},
                {"from": 10, "to": 11, "label": "ctx", "order": 1},
                {"from": 2, "to": 12, "label": "body", "order": 2},
                {"from": 12, "to": 13, "label": "target", "order": 1},
                {"from": 13, "to": 14, "label": "ctx", "order": 1},
                {"from": 12, "to": 15, "label": "annotation", "order": 1},
                {"from": 15, "to": 16, "label": "ctx", "order": 1},
                {"from": 12, "to": 17, "label": "value", "order": 1},
                {"from": 2, "to": 18, "label": "body", "order": 3},
                {"from": 18, "to": 19, "label": "test", "order": 1},
                {"from": 19, "to": 20, "label": "ctx", "order": 1},
                {"from": 18, "to": 21, "label": "msg", "order": 1},
                {"from": 2, "to": 22, "label": "body", "order": 4},
                {"from": 22, "to": 23, "label": "targets", "order": 1},
                {"from": 23, "to": 24, "label": "ctx", "order": 1},
                {"from": 2, "to": 25, "label": "body", "order": 5},
                {"from": 25, "to": 26, "label": "value", "order": 1},
                {"from": 26, "to": 27, "label": "value", "order": 1},
                {"from": 27, "to": 28, "label": "ctx", "order": 1},
            ],
        }
        tree = py_from_ast.graph_to_ast(graph_data)
        rendered = ast.dump(tree, include_attributes=False)
        self.assertIn("AsyncFunctionDef(name='fetch'", rendered)
        self.assertIn("Await(value=Call(func=Name(id='download', ctx=Load())", rendered)
        self.assertIn("AnnAssign(target=Name(id='count', ctx=Store())", rendered)
        self.assertIn("Assert(test=Name(id='ready', ctx=Load())", rendered)
        self.assertIn("Delete(targets=[Name(id='temp', ctx=Del())])", rendered)
        self.assertIn("YieldFrom(value=Name(id='stream', ctx=Load()))", rendered)

    def test_main_supports_py_for_ast_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "graphs.db"
            graph_file = REPO_ROOT / "prj/demo/examples/030-py-ast-assign-graph.json"
            init_db(db_path)
            load_graph(db_path, graph_file)
            old_cwd = Path.cwd()
            try:
                os.chdir(tmp)
                self.assertEqual(graph_tool.main(["--db", str(db_path), "--py", "--id", "30"]), 0)
            finally:
                os.chdir(old_cwd)
            out_file = tmp / "compare.py"
            self.assertTrue(out_file.exists())
            self.assertEqual(out_file.read_text(encoding="utf-8").strip(), "x = 1")

    def test_java_from_ast_module_builds_class_and_method(self):
        graph_data = {
            "nodes": [
                {"id": 1, "label": "CompilationUnit", "text": "CompilationUnit"},
                {"id": 2, "label": "ClassDeclaration", "text": "Hello"},
                {"id": 3, "label": "FieldDeclaration", "text": "FieldDeclaration"},
                {"id": 4, "label": "BasicType", "name": "int", "text": "int"},
                {"id": 5, "label": "VariableDeclarator", "name": "x", "text": "x"},
                {"id": 6, "label": "Literal", "value": "1", "text": "1"},
                {"id": 7, "label": "MethodDeclaration", "text": "getX"},
                {"id": 8, "label": "BasicType", "name": "int", "text": "int"},
                {"id": 9, "label": "BlockStatement", "text": "BlockStatement"},
                {"id": 10, "label": "ReturnStatement", "text": "ReturnStatement"},
                {"id": 11, "label": "MemberReference", "member": "x", "text": "x"},
            ],
            "edges": [
                {"from": 1, "to": 2, "label": "types", "order": 1},
                {"from": 2, "to": 3, "label": "body", "order": 1},
                {"from": 3, "to": 4, "label": "type", "order": 1},
                {"from": 3, "to": 5, "label": "declarators", "order": 1},
                {"from": 5, "to": 6, "label": "initializer", "order": 1},
                {"from": 2, "to": 7, "label": "body", "order": 2},
                {"from": 7, "to": 8, "label": "return_type", "order": 1},
                {"from": 7, "to": 9, "label": "body", "order": 1},
                {"from": 9, "to": 10, "label": "statements", "order": 1},
                {"from": 10, "to": 11, "label": "expression", "order": 1},
            ],
        }
        tree = java_from_ast.graph_to_ast(graph_data)
        self.assertEqual(type(tree).__name__, "CompilationUnit")
        source = java_from_ast.to_source(graph_data)
        self.assertIn("class Hello", source)
        self.assertIn("int x = 1;", source)
        self.assertIn("return x;", source)

    def test_java_from_ast_respects_explicit_edge_order(self):
        graph_data = {
            "nodes": [
                {"id": 1, "label": "CompilationUnit", "text": "CompilationUnit"},
                {"id": 2, "label": "ClassDeclaration", "text": "Hello"},
                {"id": 3, "label": "MethodDeclaration", "text": "demo"},
                {"id": 4, "label": "BasicType", "name": "void", "text": "void"},
                {"id": 5, "label": "BlockStatement", "text": "BlockStatement"},
                {"id": 6, "label": "StatementExpression", "text": "StatementExpression"},
                {"id": 7, "label": "MethodInvocation", "member": "first", "text": "first"},
                {"id": 8, "label": "StatementExpression", "text": "StatementExpression"},
                {"id": 9, "label": "MethodInvocation", "member": "second", "text": "second"},
            ],
            "edges": [
                {"from": 1, "to": 2, "label": "types", "order": 1},
                {"from": 2, "to": 3, "label": "body", "order": 1},
                {"from": 3, "to": 4, "label": "return_type", "order": 1},
                {"from": 3, "to": 5, "label": "body", "order": 1},
                {"from": 5, "to": 8, "label": "statements", "order": 2},
                {"from": 5, "to": 6, "label": "statements", "order": 1},
                {"from": 6, "to": 7, "label": "expression", "order": 1},
                {"from": 8, "to": 9, "label": "expression", "order": 1},
            ],
        }
        source = java_from_ast.to_source(graph_data)
        self.assertTrue(source.index("first()") < source.index("second()"))

    def test_main_supports_rs_for_ast_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "graphs.db"
            graph_file = REPO_ROOT / "prj/demo/examples/040-rust-ast-func-graph.json"
            expected_file = REPO_ROOT / "prj/demo/examples/040-rust-ast-func.rs"
            init_db(db_path)
            load_graph(db_path, graph_file)
            old_cwd = Path.cwd()
            try:
                os.chdir(tmp)
                self.assertEqual(graph_tool.main(["--db", str(db_path), "--rs", "--id", "40"]), 0)
            finally:
                os.chdir(old_cwd)
            out_file = tmp / "compare.rs"
            self.assertTrue(out_file.exists())
            self.assertEqual(out_file.read_text(encoding="utf-8"), expected_file.read_text(encoding="utf-8"))

    def test_main_supports_rs_for_struct_impl_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "graphs.db"
            graph_file = REPO_ROOT / "prj/demo/examples/041-rust-ast-struct-impl-graph.json"
            expected_file = REPO_ROOT / "prj/demo/examples/041-rust-ast-struct-impl.rs"
            init_db(db_path)
            load_graph(db_path, graph_file)
            old_cwd = Path.cwd()
            try:
                os.chdir(tmp)
                self.assertEqual(graph_tool.main(["--db", str(db_path), "--rs", "--id", "41"]), 0)
            finally:
                os.chdir(old_cwd)
            out_file = tmp / "compare.rs"
            self.assertTrue(out_file.exists())
            self.assertEqual(out_file.read_text(encoding="utf-8"), expected_file.read_text(encoding="utf-8"))

    def test_beam_search_with_filter_on_larger_graph(self):
        graph_file = REPO_ROOT / "prj/demo/examples/020-work-plans-graph.json"
        self.assertTrue(graph_file.exists())
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            db_path = tmp / "graphs.db"
            init_db(db_path)
            report = load_graph(db_path, graph_file)
            self.assertEqual(report["graph_id"], 20)
            result = run_algorithm(
                db_path,
                20,
                "beam",
                1,
                25,
                beam_width=2,
                filter_min_weight=2,
            )
            self.assertEqual(result["graph_id"], 20)
            self.assertEqual(result["start"], 1)
            self.assertEqual(result["goal"], 25)
            self.assertEqual(result["path"], [1, 2, 25])
            self.assertEqual(result["cost"], 5.0)
            self.assertEqual(result["beam_width"], 2)
            self.assertEqual(result["filter_min_weight"], 2.0)

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
