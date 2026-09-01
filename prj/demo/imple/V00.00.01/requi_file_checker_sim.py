from __future__ import annotations

# R2-2: Simulator code is aligned to the base Python-code requirement.
import json
import re
import sys
from pathlib import Path

__version__ = "V00.00.01"


def _read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _resolve_relative(base: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def _load_json_tokens(path: str | Path) -> list[str]:
    data = json.loads(_read_text(path))
    if isinstance(data, dict):
        data = data.get("args", [])
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise SystemExit("--json-in file must contain a JSON array of strings or an object with an 'args' array")
    return data


def _extract_marker_values(text: str, marker_name: str) -> list[str]:
    if not marker_name:
        return []
    pattern = rf"([^\s\[\]]+)\[{re.escape(marker_name)}\]"
    return re.findall(pattern, text)


def parse_cli(argv: list[str] | None = None) -> dict:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(".")
    current_path = Path(".")
    requi_path: Path | None = None
    evidence_path: Path | None = None
    filesystem_cues: list[str] = []
    marker_name = "REF_EXISTS"
    link_targets: list[str] = []
    link_files: list[Path] = []
    json_inputs: list[Path] = []
    explain = False
    emit_json = False

    def need_value(index: int) -> str:
        if index + 1 >= len(args):
            raise SystemExit(f"missing value for {args[index]}")
        return args[index + 1]

    def current_base() -> Path:
        return root / current_path if not current_path.is_absolute() else current_path

    i = 0
    while i < len(args):
        token = args[i]
        if token in ("-h", "--help"):
            print("requi_file_checker_sim --root ROOT --json-in FILE [options]")
            raise SystemExit(0)
        if token in ("-v", "--version"):
            print(f"requi_file_checker_sim {__version__}")
            raise SystemExit(0)
        if token == "--root":
            root = Path(need_value(i))
            current_path = Path(".")
            i += 2
            continue
        if token == "--path":
            current_path = Path(need_value(i))
            i += 2
            continue
        if token == "--json-in":
            json_input = _resolve_relative(current_base(), need_value(i))
            json_inputs.append(json_input)
            loaded = _load_json_tokens(json_input)
            args = args[:i] + loaded + args[i + 2 :]
            continue
        if token == "--requi":
            requi_path = _resolve_relative(current_base(), need_value(i))
            i += 2
            continue
        if token == "--evidence":
            evidence_path = _resolve_relative(current_base(), need_value(i))
            i += 2
            continue
        if token == "--filesystem-cue":
            filesystem_cues.append(need_value(i))
            i += 2
            continue
        if token == "--marker":
            marker_name = need_value(i)
            i += 2
            continue
        if token == "--link-target":
            link_targets.append(need_value(i))
            i += 2
            continue
        if token == "--link-file":
            link_files.append(_resolve_relative(current_base(), need_value(i)))
            i += 2
            continue
        if token == "--explain":
            explain = True
            i += 1
            continue
        if token == "--json":
            emit_json = True
            i += 1
            continue
        raise SystemExit(f"unrecognized argument: {token}")

    if requi_path is None:
        raise SystemExit("--requi is required")
    if evidence_path is None:
        raise SystemExit("--evidence is required")

    return {
        "root": str(root),
        "requirement": requi_path,
        "evidence": evidence_path,
        "filesystem_cues": filesystem_cues,
        "marker": marker_name,
        "link_targets": link_targets,
        "link_files": link_files,
        "json_inputs": json_inputs,
        "explain": explain,
        "json": emit_json,
    }


# R2-2: This simulator demonstrates what the checker would do step by step.
def explain_run(argv: list[str] | None = None) -> str:
    parsed = parse_cli(argv)
    requi_text = _read_text(parsed["requirement"]) if Path(parsed["requirement"]).exists() else ""
    extracted = _extract_marker_values(requi_text, parsed["marker"])

    lines = []
    step = 1

    def add(text: str) -> None:
        nonlocal step
        lines.append(f"{step}. {text}")
        step += 1

    add(f"set root to {parsed['root']}")
    if parsed["json_inputs"]:
        for item in parsed["json_inputs"]:
            add(f"load arg config from {item}")
            add("apply args from the config in the current sequence")
    add(f"set current path and resolve requirement to {parsed['requirement']}")
    add(f"set current path and resolve evidence to {parsed['evidence']}")
    add(f"read marker name {parsed['marker']}")
    add("extract terms from the requirement using term[MARKER] lines")
    for term in extracted:
        add(f"extract term {term}")
    add("compare extracted terms against the evidence file")
    for term in extracted:
        add(f"would check evidence for {term}")
    for cue in parsed["filesystem_cues"]:
        add(f"would check evidence for filesystem cue {cue}")
    if parsed["link_files"]:
        for path in parsed["link_files"]:
            add(f"load link file {path}")
    if parsed["link_targets"]:
        for target in parsed["link_targets"]:
            add(f"would check link target {target}")
    add("finish with a simulated result")
    return "\n".join(lines)


# R2-2: The CLI entrypoint stays simple so the simulator can be invoked directly.
def main(argv: list[str] | None = None) -> int:
    print(explain_run(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
