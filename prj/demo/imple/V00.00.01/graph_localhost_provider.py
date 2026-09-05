from __future__ import annotations

import argparse
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Tuple

import graph_tool

DEFAULT_DB_PATH = Path("assets/graph.db")


class _GraphHandler(BaseHTTPRequestHandler):
    body: bytes = b""
    content_type: str = "application/octet-stream"
    dot_text: str = ""

    def do_GET(self):
        if self.path in {"/", "/graph.png"}:
            body = self.body
            self.send_response(200)
            self.send_header("Content-Type", self.content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/graph.dot":
            body = self.dot_text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, fmt, *args):  # pragma: no cover - quiet server
        return


def render_graph_svg(graph: dict) -> Tuple[str, str]:
    dot_text = graph_tool._graph_to_dot(graph)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        dot_file = tmp_dir / "graph.dot"
        svg_file = tmp_dir / "graph.svg"
        dot_file.write_text(dot_text, encoding="utf-8")
        subprocess.run(["dot", "-Tsvg", str(dot_file), "-o", str(svg_file)], check=True, capture_output=True, text=True)
        svg_text = svg_file.read_text(encoding="utf-8")
    return svg_text, dot_text


def render_dot_png(dot_file: str | Path) -> tuple[bytes, str]:
    dot_file = Path(dot_file)
    dot_text = dot_file.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        png_file = tmp_dir / "graph.png"
        subprocess.run(["dot", "-Tpng", str(dot_file), "-o", str(png_file)], check=True, capture_output=True, text=True)
        png_bytes = png_file.read_bytes()
    return png_bytes, dot_text


def serve_graph(db_path: str | Path, graph_id: int, host: str = "127.0.0.1", port: int = 8000):
    graph = graph_tool._db_graph_data(db_path, graph_id)
    svg_text, dot_text = render_graph_svg(graph)
    handler = type("GraphHandler", (_GraphHandler,), {"body": svg_text.encode("utf-8"), "content_type": "image/svg+xml; charset=utf-8", "dot_text": dot_text})
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def serve_graph_file(graph_file: str | Path, host: str = "127.0.0.1", port: int = 8000):
    graph = graph_tool._read_json(graph_file)
    svg_text, dot_text = render_graph_svg(graph)
    handler = type("GraphHandler", (_GraphHandler,), {"body": svg_text.encode("utf-8"), "content_type": "image/svg+xml; charset=utf-8", "dot_text": dot_text})
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def serve_dot_file(dot_file: str | Path, host: str = "127.0.0.1", port: int = 8000):
    png_bytes, dot_text = render_dot_png(dot_file)
    handler = type("GraphHandler", (_GraphHandler,), {"body": png_bytes, "content_type": "image/png", "dot_text": dot_text})
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def parse_cli(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--file")
    parser.add_argument("--dot", "-dot")
    parser.add_argument("--id", type=int)
    parser.add_argument("--name")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    return {
        "db": Path(args.db),
        "file": None if args.file is None else Path(args.file),
        "dot": None if args.dot is None else Path(args.dot),
        "id": args.id,
        "name": args.name,
        "host": args.host,
        "port": args.port,
    }


def main(argv: list[str] | None = None) -> int:
    parsed = parse_cli(argv)
    if parsed["dot"] is not None:
        server, thread = serve_dot_file(parsed["dot"], host=parsed["host"], port=parsed["port"])
        label = parsed["dot"].name
    elif parsed["file"] is not None:
        server, thread = serve_graph_file(parsed["file"], host=parsed["host"], port=parsed["port"])
        label = parsed["file"].name
    else:
        graph_id = graph_tool._resolve_graph_id(parsed["db"], parsed["id"], parsed["name"])
        server, thread = serve_graph(parsed["db"], graph_id, host=parsed["host"], port=parsed["port"])
        label = f"graph {graph_id}"
    try:
        host, port = server.server_address
        print(f"serving {label} on http://{host}:{port}/")
        thread.join()
    except KeyboardInterrupt:  # pragma: no cover - interactive stop
        pass
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
