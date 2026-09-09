#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MimapNode:
    level: int
    text: str


def default_output_path(source_path: Path) -> Path:
    """Return the default HTML output path for a MIMAP markdown file.

    If the input is under prj/<project>/docs/..., preserve the project-relative
    path below prj/<project>/out/, including the docs folder itself:
      prj/name/docs/a/b.md -> prj/name/out/docs/a/b.html

    Other inputs are written next to the source with .html suffix.
    """
    source_path = Path(source_path)
    parts = source_path.parts
    for idx, part in enumerate(parts):
        if part == "prj" and idx + 2 < len(parts):
            project_root_idx = idx + 2  # prj/<project>
            docs_idx = idx + 2
            if parts[docs_idx] == "docs":
                project_root = Path(*parts[:project_root_idx])
                relative_from_project = Path(*parts[docs_idx:]).with_suffix(".html")
                return project_root / "out" / relative_from_project
    return source_path.with_suffix(".html")


def parse_mimap_lines(lines: list[str]) -> list[MimapNode]:
    nodes: list[MimapNode] = []
    for raw in lines:
        if not raw.strip():
            continue
        leading = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if stripped.startswith("- "):
            level = leading // 2 + 1
            text = stripped[2:].strip()
        else:
            level = leading // 2
            text = stripped
        nodes.append(MimapNode(level=level, text=text))
    return nodes


def normalize_mimap_token(token: str) -> str:
    """Normalize a rendered/source token to a concept key candidate.

    Parentheses are removed, punctuation is stripped, and internal non-word
    separators collapse to underscores.
    """
    token = re.sub(r"[()]", "", token).strip().lower()
    token = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", token)
    token = re.sub(r"[^a-z0-9]+", "_", token).strip("_")
    return token


def _mimap_term_from_filename(path: Path) -> str | None:
    match = re.match(r"^\d{3}-PH-\d+(?:\.\d+)?-MIMAP-(.+)\.md$", path.name)
    if not match:
        return None
    return normalize_mimap_token(match.group(1))


def is_mimap_source(path: Path) -> bool:
    """Return true for canonical standalone MIMAP files, not RC/SR/AC docs."""
    return _mimap_term_from_filename(path) is not None


def build_concept_link_map(source_path: Path, output_path: Path) -> dict[str, str]:
    """Map sibling MIMAP term keys to relative output HTML hrefs.

    This lets a term such as ``(re)ason(ing)`` in the inference MIMAP link to
    the generated reasoning MIMAP HTML, behind the morphology-enriched token.
    """
    source_path = Path(source_path)
    output_path = Path(output_path)
    source_term = _mimap_term_from_filename(source_path)
    links: dict[str, str] = {}
    if not source_path.parent.exists():
        return links
    for candidate in sorted(source_path.parent.glob("*-MIMAP-*.md")):
        if candidate == source_path or not is_mimap_source(candidate):
            continue
        term = _mimap_term_from_filename(candidate)
        if not term or term == source_term:
            continue
        candidate_output = default_output_path(candidate)
        href = os.path.relpath(candidate_output, start=output_path.parent)
        links[term] = href.replace(os.sep, "/")
    return links


def _morph_href(part: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", part.strip().lower()).strip("-") or "part"
    return f"#morph-{safe}"


def render_morphology_token(token: str, concept_links: dict[str, str] | None = None) -> str:
    """Render one token, linking parenthesized morphology parts in source order."""
    out: list[str] = []
    pos = 0
    matched = False
    for match in re.finditer(r"\(([^()]+)\)", token):
        matched = True
        if match.start() > pos:
            out.append(html.escape(token[pos:match.start()]))
        part = match.group(1)
        out.append(
            f'<a class="morph-link" href="{html.escape(_morph_href(part), quote=True)}">'
            f"{html.escape(part)}</a>"
        )
        pos = match.end()
    if pos < len(token):
        out.append(html.escape(token[pos:]))
    rendered = "".join(out) if matched else html.escape(token)
    concept_href = (concept_links or {}).get(normalize_mimap_token(token))
    if concept_href:
        rendered += (
            f'<a class="concept-link" href="{html.escape(concept_href, quote=True)}" '
            f'title="Open linked MIMAP for {html.escape(normalize_mimap_token(token), quote=True)}">↗</a>'
        )
    return rendered


def render_morphology_text(text: str, concept_links: dict[str, str] | None = None) -> str:
    """Render text while preserving whitespace and linking morphology tokens."""
    pieces = re.split(r"(\s+)", text)
    return "".join(
        html.escape(piece) if piece.isspace() else render_morphology_token(piece, concept_links)
        for piece in pieces
    )


def collect_morphology_parts(text: str) -> list[str]:
    seen: set[str] = set()
    parts: list[str] = []
    for part in re.findall(r"\(([^()]+)\)", text):
        key = part.lower()
        if key not in seen:
            seen.add(key)
            parts.append(part)
    return parts


def _render_tree(nodes: list[MimapNode], concept_links: dict[str, str] | None = None) -> str:
    if not nodes:
        return '<div class="mimap-empty">No MIMAP content.</div>'

    output: list[str] = ['<ul class="mimap-tree">']
    current_level = 0
    open_li = False
    for node in nodes:
        level = max(0, node.level)
        if open_li:
            if level > current_level:
                output.append("\n" + "  " * (current_level + 1) + "<ul>")
                current_level += 1
                while current_level < level:
                    output.append("\n" + "  " * (current_level + 1) + "<li><ul>")
                    current_level += 1
            else:
                output.append("</li>")
                while current_level > level:
                    output.append("\n" + "  " * current_level + "</ul></li>")
                    current_level -= 1
        output.append(
            "\n" + "  " * (current_level + 1) + f"<li>{render_morphology_text(node.text, concept_links)}"
        )
        open_li = True
    if open_li:
        output.append("</li>")
    while current_level > 0:
        output.append("\n" + "  " * current_level + "</ul></li>")
        current_level -= 1
    output.append("\n</ul>")
    return "".join(output)


def _render_morphology_index(parts: list[str]) -> str:
    if not parts:
        return '<section class="morphology-index"><h2>Morphology Links</h2><p>No morphology markers found.</p></section>'
    rows = []
    for part in sorted(parts, key=lambda p: p.lower()):
        anchor = _morph_href(part)[1:]
        rows.append(f'<li id="{html.escape(anchor, quote=True)}"><code>{html.escape(part)}</code></li>')
    return '<section class="morphology-index"><h2>Morphology Links</h2><ul>' + "".join(rows) + "</ul></section>"


def mimap_to_html(markdown_text: str, title: str | None = None, concept_links: dict[str, str] | None = None) -> str:
    lines = markdown_text.splitlines()
    nodes = parse_mimap_lines(lines)
    inferred_title = title or (nodes[0].text if nodes else "MIMAP")
    parts = collect_morphology_parts(markdown_text)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(inferred_title)}</title>
<style>
body {{ font-family: system-ui, sans-serif; line-height: 1.45; margin: 2rem; }}
.mimap-tree, .mimap-tree ul {{ margin-top: 0.35rem; }}
.mimap-tree li {{ margin: 0.2rem 0; }}
.morph-link {{ color: #0645ad; text-decoration: none; border-bottom: 1px dotted #0645ad; }}
.concept-link {{ margin-left: 0.15rem; color: #0a7f27; text-decoration: none; font-size: 0.85em; }}
.morphology-index {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #ddd; }}
code {{ background: #f6f8fa; padding: 0.1rem 0.25rem; border-radius: 0.25rem; }}
</style>
</head>
<body>
<h1>{html.escape(inferred_title)}</h1>
{_render_tree(nodes, concept_links)}
{_render_morphology_index(parts)}
</body>
</html>
"""


def export_mimap(source_path: Path, output_path: Path | None = None, overwrite: bool = False) -> Path:
    source_path = Path(source_path)
    if not source_path.exists():
        raise FileNotFoundError(f"MIMAP input does not exist: {source_path}")
    if not source_path.is_file():
        raise ValueError(f"MIMAP input is not a file: {source_path}")
    target = Path(output_path) if output_path is not None else default_output_path(source_path)
    if target.exists() and not overwrite:
        raise FileExistsError(f"Output already exists; pass --overwrite to replace: {target}")
    text = source_path.read_text(encoding="utf-8")
    title = source_path.stem
    concept_links = build_concept_link_map(source_path, target)
    html_text = mimap_to_html(text, title=title, concept_links=concept_links)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html_text, encoding="utf-8")
    return target


def export_all_mimaps(folder_path: Path, overwrite: bool = False) -> list[Path]:
    """Export every sibling *-MIMAP-*.md file in a folder.

    This keeps related MIMAP HTML pages fresh after a new MIMAP is added, so
    old pages gain links to the new page when their text mentions its term.
    """
    folder_path = Path(folder_path)
    if not folder_path.exists():
        raise FileNotFoundError(f"MIMAP folder does not exist: {folder_path}")
    if not folder_path.is_dir():
        raise ValueError(f"MIMAP folder is not a directory: {folder_path}")
    sources = [source for source in sorted(folder_path.glob("*-MIMAP-*.md")) if is_mimap_source(source)]
    if not sources:
        raise ValueError(f"No MIMAP markdown files found in: {folder_path}")
    return [export_mimap(source, overwrite=overwrite) for source in sources]


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export MIMAP markdown to HTML.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--mimap", metavar="PATH", help="Single MIMAP markdown file to export")
    group.add_argument("--all-mimaps", metavar="FOLDER", help="Folder containing related *-MIMAP-*.md files to regenerate")
    parser.add_argument("--output", "-o", metavar="PATH", help="Explicit output HTML path; only valid with --mimap")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing HTML output files")
    args = parser.parse_args(argv)
    if args.output and args.all_mimaps:
        print("error: --output is only valid with --mimap", file=sys.stderr)
        return 2
    try:
        if args.all_mimaps:
            outputs = export_all_mimaps(Path(args.all_mimaps), overwrite=args.overwrite)
            for output in outputs:
                print(output)
        else:
            output = export_mimap(Path(args.mimap), Path(args.output) if args.output else None, overwrite=args.overwrite)
            print(output)
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def main() -> int:
    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
