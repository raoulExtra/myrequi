from __future__ import annotations

import ast
import json
import math
import re
import sqlite3
import subprocess
import sys
import tempfile
from heapq import heappop, heappush
from pathlib import Path

try:
    import py_from_ast
except ModuleNotFoundError:  # pragma: no cover - test/import fallback
    py_from_ast = None

RUST_AST_TOOL_MANIFEST = Path(__file__).resolve().parent / "rust_from_ast_tool" / "Cargo.toml"

__version__ = "V00.00.01"
DEFAULT_DB_PATH = Path("assets/graph.db")

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS graphs (
    graph_id INTEGER PRIMARY KEY,
    graph_name TEXT,
    source_file TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS graph_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    graph_id INTEGER NOT NULL,
    node_id TEXT NOT NULL,
    label TEXT,
    color TEXT,
    style TEXT,
    weight REAL NOT NULL,
    weight_int INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(graph_id, node_id),
    FOREIGN KEY(graph_id) REFERENCES graphs(graph_id)
);

CREATE TABLE IF NOT EXISTS node_attributes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    graph_id INTEGER NOT NULL,
    node_id TEXT NOT NULL,
    attribute TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(graph_id, node_id),
    FOREIGN KEY(graph_id) REFERENCES graphs(graph_id)
);

CREATE TABLE IF NOT EXISTS graph_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    graph_id INTEGER NOT NULL,
    from_node_id TEXT NOT NULL,
    to_node_id TEXT NOT NULL,
    label TEXT,
    color TEXT,
    style TEXT,
    weight REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(graph_id) REFERENCES graphs(graph_id)
);
"""


def init_db(db_path: str | Path) -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        con.executescript(SCHEMA_SQL)
        columns = {row[1] for row in con.execute("PRAGMA table_info(graph_nodes)")}
        if "weight_int" not in columns:
            con.execute("ALTER TABLE graph_nodes ADD COLUMN weight_int INTEGER")
        for col in ("color", "style"):
            if col not in columns:
                con.execute(f"ALTER TABLE graph_nodes ADD COLUMN {col} TEXT")
        graph_columns = {row[1] for row in con.execute("PRAGMA table_info(graphs)")}
        if "graph_name" not in graph_columns:
            con.execute("ALTER TABLE graphs ADD COLUMN graph_name TEXT")
        edge_columns = {row[1] for row in con.execute("PRAGMA table_info(graph_edges)")}
        for col in ("color", "style"):
            if col not in edge_columns:
                con.execute(f"ALTER TABLE graph_edges ADD COLUMN {col} TEXT")
    return path


def _read_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, data: dict) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def _graph_id_from_source(path: str | Path) -> int:
    stem = Path(path).stem
    match = re.match(r"^(\d+)", stem)
    if not match:
        raise SystemExit(f"cannot infer graph id from file name: {path}")
    return int(match.group(1))


def _graph_ids_from_name(db_path: str | Path, graph_name: str) -> list[int]:
    name = str(graph_name)
    variants = {name, Path(name).stem}
    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA foreign_keys = ON")
        rows = con.execute("SELECT graph_id, graph_name, source_file FROM graphs ORDER BY graph_id").fetchall()
    matches = []
    for graph_id, stored_name, source_file in rows:
        source_variants = {source_file, Path(source_file).stem} if source_file else set()
        if name == stored_name or name in source_variants or Path(name).stem == stored_name or variants & source_variants:
            matches.append(graph_id)
    return matches


def _resolve_graph_id(db_path: str | Path, graph_id: int | None = None, graph_name: str | None = None) -> int:
    if graph_id is not None and graph_name is not None:
        matches = _graph_ids_from_name(db_path, graph_name)
        if not matches:
            raise SystemExit(f"graph named {graph_name!r} not found")
        if graph_id not in matches:
            raise SystemExit(f"graph id {graph_id} does not match graph name {graph_name!r}")
        return graph_id
    if graph_id is not None:
        return graph_id
    if graph_name is not None:
        matches = _graph_ids_from_name(db_path, graph_name)
        if not matches:
            raise SystemExit(f"graph named {graph_name!r} not found")
        if len(matches) > 1:
            raise SystemExit(f"graph name {graph_name!r} is ambiguous")
        return matches[0]
    raise SystemExit("--id or --name is required")


def _scalar_weight(value: object, default: float | None = None) -> float:
    if value is None:
        if default is None:
            raise SystemExit("missing weight")
        return float(default)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    raise SystemExit("weights must be numeric")


def _optional_varchar256(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SystemExit(f"{field_name} must be text")
    if len(value) > 256:
        raise SystemExit(f"{field_name} must be at most 256 characters")
    return value


def _normalize_number(value: float | int | None) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _node_sort_key(value: str) -> tuple[int, int | str]:
    if value.isdigit():
        return (0, int(value))
    return (1, value)


def _beam_sort_key(path_keys: list[str], cost: float, goal_key: str) -> tuple:
    completed = 0 if path_keys and path_keys[-1] == goal_key else 1
    return (
        completed,
        cost,
        len(path_keys),
        tuple(_node_sort_key(key) for key in path_keys),
    )


def _db_graph_data(db_path: str | Path, graph_id: int) -> dict:
    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA foreign_keys = ON")
        graph = con.execute(
            "SELECT graph_id, graph_name, source_file FROM graphs WHERE graph_id = ?",
            (graph_id,),
        ).fetchone()
        if graph is None:
            raise SystemExit(f"graph {graph_id} not found")
        nodes = con.execute(
            """
            SELECT n.node_id, n.label, n.color, n.style, n.weight, n.weight_int, a.attribute
            FROM graph_nodes n
            LEFT JOIN node_attributes a
              ON a.graph_id = n.graph_id AND a.node_id = n.node_id
            WHERE n.graph_id = ?
            ORDER BY CAST(n.node_id AS INTEGER), n.node_id
            """,
            (graph_id,),
        ).fetchall()
        edges = con.execute(
            """
            SELECT from_node_id, to_node_id, label, color, style, weight
            FROM graph_edges
            WHERE graph_id = ?
            ORDER BY id
            """,
            (graph_id,),
        ).fetchall()
    return {
        "graph_id": graph[0],
        "graph_name": graph[1],
        "source_file": graph[2],
        "nodes": [
            {
                "id": int(row[0]) if str(row[0]).isdigit() else row[0],
                **({"label": row[1]} if row[1] is not None else {}),
                **({"color": row[2]} if row[2] is not None else {}),
                **({"style": row[3]} if row[3] is not None else {}),
                "weight": _normalize_number(row[4]),
                **({"weight_int": row[5]} if row[5] is not None else {}),
                **({"text": row[6]} if row[6] is not None else {}),
            }
            for row in nodes
        ],
        "edges": [
            {
                "from": int(row[0]) if str(row[0]).isdigit() else row[0],
                "to": int(row[1]) if str(row[1]).isdigit() else row[1],
                **({"label": row[2]} if row[2] is not None else {}),
                **({"color": row[3]} if row[3] is not None else {}),
                **({"style": row[4]} if row[4] is not None else {}),
                "weight": _normalize_number(row[5]),
            }
            for row in edges
        ],
    }


def _compare_graph_data(left: dict, right: dict) -> dict:
    left_ok = left.get("nodes") == right.get("nodes") and left.get("edges") == right.get("edges")
    return {
        "equal": left_ok,
        "left": left,
        "right": right,
    }


def _dot_quote(value: object) -> str:
    return json.dumps(str(value))


def _graph_to_dot(graph: dict) -> str:
    lines = [
        "digraph G {",
        "  graph [rankdir=LR, splines=true, nodesep=0.45, ranksep=0.6];",
        "  node [shape=box, fontname=Helvetica, margin=0.08];",
        "  edge [fontname=Helvetica];",
    ]
    for node in graph.get("nodes", []):
        node_id = _dot_quote(node["id"])
        title = str(node.get("label") or node.get("id"))
        parts = [title]
        if node.get("text"):
            parts.append(str(node["text"]))
        label = "\n".join(parts)
        attrs = [f"label={_dot_quote(label)}"]
        tooltip_parts = []
        if node.get("weight_int") is not None:
            tooltip_parts.append(f"weight_int={node['weight_int']}")
        if node.get("weight") is not None:
            tooltip_parts.append(f"weight={node['weight']}")
        if tooltip_parts:
            attrs.append(f"tooltip={_dot_quote(' | '.join(tooltip_parts))}")
        if node.get("color") is not None:
            attrs.append(f"color={_dot_quote(node['color'])}")
        if node.get("style") is not None:
            attrs.append(f"style={_dot_quote(node['style'])}")
        lines.append(f"  {node_id} [{', '.join(attrs)}];")
    for edge in graph.get("edges", []):
        attrs = []
        if edge.get("label") is not None:
            attrs.append(f"label={_dot_quote(edge['label'])}")
        if edge.get("color") is not None:
            attrs.append(f"color={_dot_quote(edge['color'])}")
        if edge.get("style") is not None:
            attrs.append(f"style={_dot_quote(edge['style'])}")
        if edge.get("weight") is not None and edge.get("weight") != 1:
            attrs.append(f"weight={_dot_quote(edge['weight'])}")
        attr_text = f" [{', '.join(attrs)}]" if attrs else ""
        lines.append(f"  {_dot_quote(edge['from'])} -> {_dot_quote(edge['to'])}{attr_text};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def load_graph(db_path: str | Path, graph_file: str | Path) -> dict:
    db_path = init_db(db_path)
    graph_file = Path(graph_file)
    graph_id = _graph_id_from_source(graph_file)
    data = _read_json(graph_file)
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    graph_name = data.get("name")
    if graph_name is not None and not isinstance(graph_name, str):
        raise SystemExit("graph JSON name must be text")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise SystemExit("graph JSON must contain 'nodes' and 'edges' arrays")

    node_ids = {str(node.get("id")) for node in nodes if isinstance(node, dict) and "id" in node}
    warnings: list[str] = []

    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("DELETE FROM graph_edges WHERE graph_id = ?", (graph_id,))
        con.execute("DELETE FROM node_attributes WHERE graph_id = ?", (graph_id,))
        con.execute("DELETE FROM graph_nodes WHERE graph_id = ?", (graph_id,))
        con.execute("DELETE FROM graphs WHERE graph_id = ?", (graph_id,))
        con.execute("INSERT INTO graphs (graph_id, graph_name, source_file) VALUES (?, ?, ?)", (graph_id, graph_name, graph_file.name))

        nodes_loaded = 0
        for node in nodes:
            if not isinstance(node, dict) or "id" not in node:
                raise SystemExit("each node must be an object with an id")
            node_id = str(node["id"])
            label = node.get("label")
            color = _optional_varchar256(node.get("color"), "node color")
            style = _optional_varchar256(node.get("style"), "node style")
            weight = _scalar_weight(node.get("weight"), default=0.0)
            weight_int = node.get("weight_int")
            if weight_int is not None and not (isinstance(weight_int, int) and not isinstance(weight_int, bool)):
                raise SystemExit("node integer weight must be an integer")
            con.execute(
                "INSERT INTO graph_nodes (graph_id, node_id, label, color, style, weight, weight_int) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (graph_id, node_id, label, color, style, weight, weight_int),
            )
            attribute = node.get("text", node.get("attribute"))
            if attribute is not None:
                if not isinstance(attribute, str):
                    raise SystemExit("node text must be text")
                con.execute(
                    "INSERT OR REPLACE INTO node_attributes (graph_id, node_id, attribute) VALUES (?, ?, ?)",
                    (graph_id, node_id, attribute),
                )
            nodes_loaded += 1

        edges_loaded = 0
        for edge in edges:
            if not isinstance(edge, dict) or "from" not in edge or "to" not in edge:
                raise SystemExit("each edge must be an object with from and to")
            from_node = str(edge["from"])
            to_node = str(edge["to"])
            if from_node not in node_ids:
                warnings.append(f"missing node for edge from {from_node}")
            if to_node not in node_ids:
                warnings.append(f"missing node for edge to {to_node}")
            label = edge.get("label")
            color = _optional_varchar256(edge.get("color"), "edge color")
            style = _optional_varchar256(edge.get("style"), "edge style")
            weight = _scalar_weight(edge.get("weight"), default=1)
            con.execute(
                "INSERT INTO graph_edges (graph_id, from_node_id, to_node_id, label, color, style, weight) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (graph_id, from_node, to_node, label, color, style, weight),
            )
            edges_loaded += 1

    return {
        "graph_id": graph_id,
        "db_path": str(db_path),
        "graph_name": graph_name,
        "source_file": graph_file.name,
        "nodes_loaded": nodes_loaded,
        "edges_loaded": edges_loaded,
        "warnings": warnings,
    }


def export_graph(db_path: str | Path, graph_id: int, out_file: str | Path = "out.json") -> dict:
    graph = _db_graph_data(db_path, graph_id)
    path = _write_json(out_file, {"nodes": graph["nodes"], "edges": graph["edges"]})
    return {"graph_id": graph_id, "output_file": str(path), "nodes": len(graph["nodes"]), "edges": len(graph["edges"])}


def export_graphviz(db_path: str | Path, graph_id: int, out_base: str | Path = "out") -> dict:
    graph = _db_graph_data(db_path, graph_id)
    base = Path(out_base)
    dot_path = base.with_suffix(".dot")
    svg_path = base.with_suffix(".svg")
    dot_path.parent.mkdir(parents=True, exist_ok=True)
    dot_text = _graph_to_dot(graph)
    dot_path.write_text(dot_text, encoding="utf-8")
    try:
        subprocess.run(["dot", "-Tsvg", str(dot_path), "-o", str(svg_path)], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - external tool failure
        raise SystemExit(exc.stderr.strip() or exc.stdout.strip() or "graphviz dot failed") from exc
    return {
        "graph_id": graph_id,
        "dot_file": str(dot_path),
        "svg_file": str(svg_path),
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
    }


def export_rust_from_ast(db_path: str | Path, graph_id: int, out_file: str | Path = "compare.rs") -> dict:
    graph = _db_graph_data(db_path, graph_id)
    if not RUST_AST_TOOL_MANIFEST.exists():
        raise SystemExit(f"rust AST tool manifest missing: {RUST_AST_TOOL_MANIFEST}")
    out_path = Path(out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        graph_file = tmp / "graph.json"
        graph_file.write_text(json.dumps({"nodes": graph["nodes"], "edges": graph["edges"]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            subprocess.run(
                ["cargo", "run", "--quiet", "--manifest-path", str(RUST_AST_TOOL_MANIFEST), "--", str(graph_file), str(out_path)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:  # pragma: no cover - external tool failure
            message = exc.stderr.strip() or exc.stdout.strip() or "rust AST tool failed"
            raise SystemExit(message) from exc
    return {"graph_id": graph_id, "output_file": str(out_path), "nodes": len(graph["nodes"]), "edges": len(graph["edges"])}


def compare_graph(db_path: str | Path, graph_id: int, json_file: str | Path) -> dict:
    graph = _db_graph_data(db_path, graph_id)
    source = _read_json(json_file)
    if not isinstance(source, dict):
        raise SystemExit("comparison JSON must be an object")
    left = {"nodes": graph["nodes"], "edges": graph["edges"]}
    right = {"nodes": source.get("nodes", []), "edges": source.get("edges", [])}
    report = _compare_graph_data(left, right)
    report["graph_id"] = graph_id
    report["json_file"] = str(json_file)
    return report


def run_algorithm(
    db_path: str | Path,
    graph_id: int,
    algo: str,
    start: object,
    goal: object | None = None,
    beam_width: int = 3,
    filter_min_weight: float | None = None,
) -> dict:
    graph = _db_graph_data(db_path, graph_id)
    algo_name = algo.strip().lower()

    node_map = {str(node["id"]): node["id"] for node in graph["nodes"]}
    if not node_map:
        raise SystemExit("graph has no nodes")
    start_key = str(start)
    if start_key not in node_map:
        raise SystemExit(f"start node not found: {start}")
    if goal is None:
        ordered_keys = sorted(node_map.keys(), key=_node_sort_key)
        goal_key = ordered_keys[-1]
    else:
        goal_key = str(goal)
        if goal_key not in node_map:
            raise SystemExit(f"goal node not found: {goal}")

    if algo_name in {"a*", "astar", "a-star"}:
        adjacency: dict[str, list[tuple[str, float]]] = {}
        for edge in graph["edges"]:
            adjacency.setdefault(str(edge["from"]), []).append((str(edge["to"]), float(edge["weight"])))

        open_heap: list[tuple[float, int, str]] = []
        heappush(open_heap, (0.0, 0, start_key))
        came_from: dict[str, str] = {}
        g_score: dict[str, float] = {start_key: 0.0}
        seen: set[str] = set()
        counter = 0

        while open_heap:
            _, _, current = heappop(open_heap)
            if current in seen:
                continue
            seen.add(current)
            if current == goal_key:
                break
            for neighbor, cost in adjacency.get(current, []):
                tentative = g_score[current] + cost
                if tentative < g_score.get(neighbor, math.inf):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative
                    counter += 1
                    heappush(open_heap, (tentative, counter, neighbor))

        if goal_key not in g_score:
            raise SystemExit(f"no path found for graph {graph_id}")

        path_keys = [goal_key]
        while path_keys[-1] != start_key:
            path_keys.append(came_from[path_keys[-1]])
        path_keys.reverse()
        path = [node_map[key] for key in path_keys]
        return {
            "graph_id": graph_id,
            "algo": algo,
            "start": node_map[start_key],
            "goal": node_map[goal_key],
            "path": path,
            "cost": g_score[goal_key],
        }

    if algo_name in {"beam", "beam-search", "beam_search"}:
        beam_width = max(1, int(beam_width))
        adjacency: dict[str, list[tuple[str, float]]] = {}
        for edge in graph["edges"]:
            from_node = str(edge["from"])
            to_node = str(edge["to"])
            cost = float(edge["weight"])
            if filter_min_weight is not None and cost < filter_min_weight:
                continue
            adjacency.setdefault(from_node, []).append((to_node, cost))

        beam: list[tuple[list[str], float]] = [([start_key], 0.0)]
        best_complete: tuple[list[str], float] | None = None
        best_complete_score: tuple | None = None
        max_steps = max(1, len(node_map))

        for _ in range(max_steps):
            candidates: list[tuple[tuple, list[str], float]] = []
            for path_keys, cost in beam:
                current = path_keys[-1]
                if current == goal_key:
                    score = _beam_sort_key(path_keys, cost, goal_key)
                    if best_complete_score is None or score < best_complete_score:
                        best_complete = (path_keys, cost)
                        best_complete_score = score
                    candidates.append((score, path_keys, cost))
                    continue
                for neighbor, edge_cost in adjacency.get(current, []):
                    if neighbor in path_keys:
                        continue
                    new_path = path_keys + [neighbor]
                    new_cost = cost + edge_cost
                    score = _beam_sort_key(new_path, new_cost, goal_key)
                    if neighbor == goal_key and (
                        best_complete_score is None or score < best_complete_score
                    ):
                        best_complete = (new_path, new_cost)
                        best_complete_score = score
                    candidates.append((score, new_path, new_cost))

            if not candidates:
                break
            candidates.sort(key=lambda item: item[0])
            beam = [(path, cost) for _, path, cost in candidates[:beam_width]]

            for path_keys, cost in beam:
                if path_keys[-1] == goal_key:
                    score = _beam_sort_key(path_keys, cost, goal_key)
                    if best_complete_score is None or score < best_complete_score:
                        best_complete = (path_keys, cost)
                        best_complete_score = score

        if best_complete is None:
            raise SystemExit(f"no path found for graph {graph_id}")

        path = [node_map[key] for key in best_complete[0]]
        return {
            "graph_id": graph_id,
            "algo": algo,
            "start": node_map[start_key],
            "goal": node_map[goal_key],
            "path": path,
            "cost": best_complete[1],
            "beam_width": beam_width,
            "filter_min_weight": filter_min_weight,
        }

    raise SystemExit(f"unsupported algorithm: {algo}")


def list_graphs(db_path: str | Path, graph_id: int | None = None) -> list[dict]:
    db_path = init_db(db_path)
    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA foreign_keys = ON")
        if graph_id is None:
            rows = con.execute(
                """
                SELECT g.graph_id, g.graph_name, g.source_file,
                       COUNT(DISTINCT n.id) AS nodes,
                       COUNT(DISTINCT e.id) AS edges
                FROM graphs g
                LEFT JOIN graph_nodes n ON n.graph_id = g.graph_id
                LEFT JOIN graph_edges e ON e.graph_id = g.graph_id
                GROUP BY g.graph_id, g.graph_name, g.source_file
                ORDER BY g.graph_id
                """
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT g.graph_id, g.graph_name, g.source_file,
                       COUNT(DISTINCT n.id) AS nodes,
                       COUNT(DISTINCT e.id) AS edges
                FROM graphs g
                LEFT JOIN graph_nodes n ON n.graph_id = g.graph_id
                LEFT JOIN graph_edges e ON e.graph_id = g.graph_id
                WHERE g.graph_id = ?
                GROUP BY g.graph_id, g.graph_name, g.source_file
                ORDER BY g.graph_id
                """,
                (graph_id,),
            ).fetchall()
    return [{"graph_id": row[0], "graph_name": row[1], "source_file": row[2], "nodes": row[3], "edges": row[4]} for row in rows]


def parse_cli(argv: list[str] | None = None) -> dict:
    args = list(sys.argv[1:] if argv is None else argv)
    db_path: Path | None = DEFAULT_DB_PATH
    init_path: Path | None = None
    load_path: Path | None = None
    list_flag: bool | None = None
    graph_id: int | None = None
    graph_name: str | None = None
    export_path: Path | None = None
    compare_path: Path | None = None
    gviz_path: Path | None = None
    algo_name: str | None = None
    py_flag: bool | None = None
    rs_flag: bool | None = None
    start_node: object | None = None
    goal_node: object | None = None
    beam_width: int = 3
    filter_min_weight: float | None = None

    def need_value(index: int) -> str:
        if index + 1 >= len(args):
            raise SystemExit(f"missing value for {args[index]}")
        return args[index + 1]

    i = 0
    while i < len(args):
        token = args[i]
        if token in ("-h", "--help"):
            print(
                "graph_tool.py --init DB | --db DB --load GRAPH.json | "
                "--db DB --list | --db DB --export [FILE] --id GRAPH_ID|--name GRAPH_NAME | "
                "--db DB --compare JSON --id GRAPH_ID|--name GRAPH_NAME | --db DB --algo NAME "
                "--start NODE [--goal NODE] [--beam-width N] "
                "[--filter-min-weight W] --id GRAPH_ID|--name GRAPH_NAME | --db DB --py --id GRAPH_ID|--name GRAPH_NAME | "
                "--db DB --rs --id GRAPH_ID|--name GRAPH_NAME | --db DB -gviz [BASE] --id GRAPH_ID|--name GRAPH_NAME | --db DB --list [--id GRAPH_ID|--name GRAPH_NAME]"
                f"\nDefault DB: {DEFAULT_DB_PATH}"
            )
            raise SystemExit(0)
        if token in ("-v", "--version"):
            print(f"graph_tool.py {__version__}")
            raise SystemExit(0)
        if token == "--db":
            db_path = Path(need_value(i))
            i += 2
            continue
        if token == "--init":
            init_path = Path(need_value(i))
            i += 2
            continue
        if token == "--load":
            load_path = Path(need_value(i))
            i += 2
            continue
        if token == "--list":
            list_flag = True
            i += 1
            continue
        if token == "--id":
            graph_id = int(need_value(i))
            i += 2
            continue
        if token in ("--name", "-name"):
            graph_name = need_value(i)
            i += 2
            continue
        if token == "--export":
            if i + 1 < len(args) and not args[i + 1].startswith("-"):
                export_path = Path(args[i + 1])
                i += 2
            else:
                export_path = Path("out.json")
                i += 1
            continue
        if token == "--compare":
            compare_path = Path(need_value(i))
            i += 2
            continue
        if token == "--algo":
            algo_name = need_value(i)
            i += 2
            continue
        if token in ("--gviz", "-gviz"):
            if i + 1 < len(args) and not args[i + 1].startswith("-"):
                gviz_path = Path(args[i + 1])
                i += 2
            else:
                gviz_path = Path("assets/graph")
                i += 1
            continue
        if token == "--py":
            py_flag = True
            i += 1
            continue
        if token == "--rs":
            rs_flag = True
            i += 1
            continue
        if token == "--start":
            start_node = need_value(i)
            i += 2
            continue
        if token == "--goal":
            goal_node = need_value(i)
            i += 2
            continue
        if token == "--beam-width":
            beam_width = int(need_value(i))
            i += 2
            continue
        if token == "--filter-min-weight":
            filter_min_weight = float(need_value(i))
            i += 2
            continue
        raise SystemExit(f"unrecognized argument: {token}")

    return {
        "db": db_path,
        "init": init_path,
        "load": load_path,
        "list": list_flag,
        "id": graph_id,
        "name": graph_name,
        "export": export_path,
        "compare": compare_path,
        "gviz": gviz_path,
        "algo": algo_name,
        "py": py_flag,
        "rs": rs_flag,
        "start": start_node,
        "goal": goal_node,
        "beam_width": beam_width,
        "filter_min_weight": filter_min_weight,
    }


def main(argv: list[str] | None = None) -> int:
    parsed = parse_cli(argv)
    if parsed["init"] is not None:
        path = init_db(parsed["init"])
        print(f"initialized empty graph db at {path}")
        return 0
    if parsed["db"] is None:
        raise SystemExit("--db is required for --load, --list, --export, --compare, --gviz, --algo, --py, or --rs")
    selected_graph_id = parsed["id"]
    if parsed["name"] is not None:
        selected_graph_id = _resolve_graph_id(parsed["db"], parsed["id"], parsed["name"])
    if parsed["load"] is not None:
        report = load_graph(parsed["db"], parsed["load"])
        name_part = f" name={report['graph_name']}" if report.get('graph_name') else ""
        print(
            f"loaded graph {report['graph_id']}{name_part} from {report['source_file']} "
            f"with {report['nodes_loaded']} nodes and {report['edges_loaded']} edges"
        )
        for warning in report["warnings"]:
            print(f"warning: {warning}")
        return 0
    if parsed["list"]:
        graphs = list_graphs(parsed["db"], selected_graph_id)
        if selected_graph_id is not None and not graphs:
            print(f"warning: graph {selected_graph_id} not found")
        for graph in graphs:
            name_part = f" graph_name={graph['graph_name']}" if graph.get('graph_name') else ""
            print(
                f"graph_id={graph['graph_id']}{name_part} source_file={graph['source_file']} "
                f"nodes={graph['nodes']} edges={graph['edges']}"
            )
        return 0
    if parsed["export"] is not None:
        if selected_graph_id is None:
            raise SystemExit("--id is required for --export")
        report = export_graph(parsed["db"], selected_graph_id, parsed["export"])
        print(f"exported graph {report['graph_id']} to {report['output_file']}")
        return 0
    if parsed["compare"] is not None:
        if selected_graph_id is None:
            raise SystemExit("--id is required for --compare")
        report = compare_graph(parsed["db"], selected_graph_id, parsed["compare"])
        print(f"compare graph {report['graph_id']} against {report['json_file']}: {'ok' if report['equal'] else 'different'}")
        return 0 if report["equal"] else 1
    if parsed["gviz"] is not None:
        if selected_graph_id is None:
            raise SystemExit("--id is required for -gviz")
        report = export_graphviz(parsed["db"], selected_graph_id, parsed["gviz"])
        print(f"exported graph {report['graph_id']} to {report['dot_file']} and {report['svg_file']}")
        return 0
    if parsed["algo"] is not None:
        if selected_graph_id is None:
            raise SystemExit("--id is required for --algo")
        if parsed["start"] is None:
            raise SystemExit("--start is required for --algo")
        report = run_algorithm(
            parsed["db"],
            selected_graph_id,
            parsed["algo"],
            parsed["start"],
            parsed["goal"],
            beam_width=parsed["beam_width"],
            filter_min_weight=parsed["filter_min_weight"],
        )
        path_text = " -> ".join(str(item) for item in report["path"])
        goal_text = f" goal={report['goal']}" if parsed["goal"] is not None else ""
        extra = ""
        if parsed["algo"].strip().lower() in {"beam", "beam-search", "beam_search"}:
            extra = f" beam_width={report['beam_width']}"
            if report["filter_min_weight"] is not None:
                extra += f" filter_min_weight={report['filter_min_weight']}"
        print(f"ran {report['algo']} on graph {report['graph_id']}: start={report['start']}{goal_text}{extra} path={path_text} cost={report['cost']}")
        return 0
    if parsed["py"]:
        if selected_graph_id is None:
            raise SystemExit("--id is required for --py")
        if py_from_ast is None:
            raise SystemExit("py_from_ast module is unavailable")
        graph = _db_graph_data(parsed["db"], selected_graph_id)
        tree = py_from_ast.graph_to_ast(graph)
        output_path = Path("compare.py")
        output_path.write_text(ast.unparse(tree) + "\n", encoding="utf-8")
        print(f"wrote {output_path}")
        return 0
    if parsed["rs"]:
        if selected_graph_id is None:
            raise SystemExit("--id is required for --rs")
        report = export_rust_from_ast(parsed["db"], selected_graph_id)
        print(f"wrote {report['output_file']}")
        return 0
    raise SystemExit("either --init, --load, --list, --export, --compare, --gviz, --algo, --py, or --rs is required")


if __name__ == "__main__":
    raise SystemExit(main())
