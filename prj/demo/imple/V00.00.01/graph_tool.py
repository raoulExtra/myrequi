from __future__ import annotations

import json
import math
import re
import sqlite3
import sys
from heapq import heappop, heappush
from pathlib import Path

__version__ = "V00.00.01"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS graphs (
    graph_id INTEGER PRIMARY KEY,
    source_file TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS graph_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    graph_id INTEGER NOT NULL,
    node_id TEXT NOT NULL,
    label TEXT,
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


def _scalar_weight(value: object, default: float | None = None) -> float:
    if value is None:
        if default is None:
            raise SystemExit("missing weight")
        return float(default)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    raise SystemExit("weights must be numeric")


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


def _db_graph_data(db_path: str | Path, graph_id: int) -> dict:
    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA foreign_keys = ON")
        graph = con.execute(
            "SELECT graph_id, source_file FROM graphs WHERE graph_id = ?",
            (graph_id,),
        ).fetchone()
        if graph is None:
            raise SystemExit(f"graph {graph_id} not found")
        nodes = con.execute(
            """
            SELECT n.node_id, n.label, n.weight, n.weight_int, a.attribute
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
            SELECT from_node_id, to_node_id, label, weight
            FROM graph_edges
            WHERE graph_id = ?
            ORDER BY id
            """,
            (graph_id,),
        ).fetchall()
    return {
        "graph_id": graph[0],
        "source_file": graph[1],
        "nodes": [
            {
                "id": int(row[0]) if str(row[0]).isdigit() else row[0],
                **({"label": row[1]} if row[1] is not None else {}),
                "weight": _normalize_number(row[2]),
                **({"weight_int": row[3]} if row[3] is not None else {}),
                **({"text": row[4]} if row[4] is not None else {}),
            }
            for row in nodes
        ],
        "edges": [
            {
                "from": int(row[0]) if str(row[0]).isdigit() else row[0],
                "to": int(row[1]) if str(row[1]).isdigit() else row[1],
                **({"label": row[2]} if row[2] is not None else {}),
                "weight": _normalize_number(row[3]),
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


def load_graph(db_path: str | Path, graph_file: str | Path) -> dict:
    db_path = init_db(db_path)
    graph_file = Path(graph_file)
    graph_id = _graph_id_from_source(graph_file)
    data = _read_json(graph_file)
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
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
        con.execute("INSERT INTO graphs (graph_id, source_file) VALUES (?, ?)", (graph_id, graph_file.name))

        nodes_loaded = 0
        for node in nodes:
            if not isinstance(node, dict) or "id" not in node:
                raise SystemExit("each node must be an object with an id")
            node_id = str(node["id"])
            label = node.get("label")
            weight = _scalar_weight(node.get("weight"), default=0.0)
            weight_int = node.get("weight_int")
            if weight_int is not None and not (isinstance(weight_int, int) and not isinstance(weight_int, bool)):
                raise SystemExit("node integer weight must be an integer")
            con.execute(
                "INSERT INTO graph_nodes (graph_id, node_id, label, weight, weight_int) VALUES (?, ?, ?, ?, ?)",
                (graph_id, node_id, label, weight, weight_int),
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
            weight = _scalar_weight(edge.get("weight"), default=1)
            con.execute(
                "INSERT INTO graph_edges (graph_id, from_node_id, to_node_id, label, weight) VALUES (?, ?, ?, ?, ?)",
                (graph_id, from_node, to_node, label, weight),
            )
            edges_loaded += 1

    return {
        "graph_id": graph_id,
        "db_path": str(db_path),
        "source_file": graph_file.name,
        "nodes_loaded": nodes_loaded,
        "edges_loaded": edges_loaded,
        "warnings": warnings,
    }


def export_graph(db_path: str | Path, graph_id: int, out_file: str | Path = "out.json") -> dict:
    graph = _db_graph_data(db_path, graph_id)
    path = _write_json(out_file, {"nodes": graph["nodes"], "edges": graph["edges"]})
    return {"graph_id": graph_id, "output_file": str(path), "nodes": len(graph["nodes"]), "edges": len(graph["edges"])}


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


def run_algorithm(db_path: str | Path, graph_id: int, algo: str, start: object, goal: object | None = None) -> dict:
    graph = _db_graph_data(db_path, graph_id)
    algo_name = algo.strip().lower()
    if algo_name not in {"a*", "astar", "a-star"}:
        raise SystemExit(f"unsupported algorithm: {algo}")

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


def list_graphs(db_path: str | Path, graph_id: int | None = None) -> list[dict]:
    db_path = init_db(db_path)
    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA foreign_keys = ON")
        if graph_id is None:
            rows = con.execute(
                """
                SELECT g.graph_id, g.source_file,
                       COUNT(DISTINCT n.id) AS nodes,
                       COUNT(DISTINCT e.id) AS edges
                FROM graphs g
                LEFT JOIN graph_nodes n ON n.graph_id = g.graph_id
                LEFT JOIN graph_edges e ON e.graph_id = g.graph_id
                GROUP BY g.graph_id, g.source_file
                ORDER BY g.graph_id
                """
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT g.graph_id, g.source_file,
                       COUNT(DISTINCT n.id) AS nodes,
                       COUNT(DISTINCT e.id) AS edges
                FROM graphs g
                LEFT JOIN graph_nodes n ON n.graph_id = g.graph_id
                LEFT JOIN graph_edges e ON e.graph_id = g.graph_id
                WHERE g.graph_id = ?
                GROUP BY g.graph_id, g.source_file
                ORDER BY g.graph_id
                """,
                (graph_id,),
            ).fetchall()
    return [{"graph_id": row[0], "source_file": row[1], "nodes": row[2], "edges": row[3]} for row in rows]


def parse_cli(argv: list[str] | None = None) -> dict:
    args = list(sys.argv[1:] if argv is None else argv)
    db_path: Path | None = None
    init_path: Path | None = None
    load_path: Path | None = None
    list_flag: bool | None = None
    graph_id: int | None = None
    export_path: Path | None = None
    compare_path: Path | None = None
    algo_name: str | None = None
    start_node: object | None = None
    goal_node: object | None = None

    def need_value(index: int) -> str:
        if index + 1 >= len(args):
            raise SystemExit(f"missing value for {args[index]}")
        return args[index + 1]

    i = 0
    while i < len(args):
        token = args[i]
        if token in ("-h", "--help"):
            print("graph_tool.py --init DB | --db DB --load GRAPH.json | --db DB --list | --db DB --export [FILE] --id GRAPH_ID | --db DB --compare JSON --id GRAPH_ID | --db DB --algo NAME --start NODE [--goal NODE] --id GRAPH_ID")
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
        if token == "--start":
            start_node = need_value(i)
            i += 2
            continue
        if token == "--goal":
            goal_node = need_value(i)
            i += 2
            continue
        raise SystemExit(f"unrecognized argument: {token}")

    return {
        "db": db_path,
        "init": init_path,
        "load": load_path,
        "list": list_flag,
        "id": graph_id,
        "export": export_path,
        "compare": compare_path,
        "algo": algo_name,
        "start": start_node,
        "goal": goal_node,
    }


def main(argv: list[str] | None = None) -> int:
    parsed = parse_cli(argv)
    if parsed["init"] is not None:
        path = init_db(parsed["init"])
        print(f"initialized empty graph db at {path}")
        return 0
    if parsed["db"] is None:
        raise SystemExit("--db is required for --load, --list, --export, or --compare")
    if parsed["load"] is not None:
        report = load_graph(parsed["db"], parsed["load"])
        print(
            f"loaded graph {report['graph_id']} from {report['source_file']} "
            f"with {report['nodes_loaded']} nodes and {report['edges_loaded']} edges"
        )
        for warning in report["warnings"]:
            print(f"warning: {warning}")
        return 0
    if parsed["list"]:
        graphs = list_graphs(parsed["db"], parsed["id"])
        if parsed["id"] is not None and not graphs:
            print(f"warning: graph {parsed['id']} not found")
        for graph in graphs:
            print(
                f"graph_id={graph['graph_id']} source_file={graph['source_file']} "
                f"nodes={graph['nodes']} edges={graph['edges']}"
            )
        return 0
    if parsed["export"] is not None:
        if parsed["id"] is None:
            raise SystemExit("--id is required for --export")
        report = export_graph(parsed["db"], parsed["id"], parsed["export"])
        print(f"exported graph {report['graph_id']} to {report['output_file']}")
        return 0
    if parsed["compare"] is not None:
        if parsed["id"] is None:
            raise SystemExit("--id is required for --compare")
        report = compare_graph(parsed["db"], parsed["id"], parsed["compare"])
        print(f"compare graph {report['graph_id']} against {report['json_file']}: {'ok' if report['equal'] else 'different'}")
        return 0 if report["equal"] else 1
    if parsed["algo"] is not None:
        if parsed["id"] is None:
            raise SystemExit("--id is required for --algo")
        if parsed["start"] is None:
            raise SystemExit("--start is required for --algo")
        report = run_algorithm(parsed["db"], parsed["id"], parsed["algo"], parsed["start"], parsed["goal"])
        path_text = " -> ".join(str(item) for item in report["path"])
        goal_text = f" goal={report['goal']}" if parsed["goal"] is not None else ""
        print(f"ran {report['algo']} on graph {report['graph_id']}: start={report['start']}{goal_text} path={path_text} cost={report['cost']}")
        return 0
    raise SystemExit("either --init, --load, --list, --export, --compare, or --algo is required")


if __name__ == "__main__":
    raise SystemExit(main())
