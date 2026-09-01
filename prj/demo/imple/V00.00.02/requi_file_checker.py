from __future__ import annotations

# R2-2: This checker module is aligned to the base Python-code requirement.
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

__version__ = "V00.00.01"


def _read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _missing_items(text: str, required: Iterable[str]) -> list[str]:
    return [item for item in required if item and item not in text]


def _resolve_relative(base: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


# R2-2: Marker extraction keeps the requirement-id alignment explicit in code.
def _extract_marker_values(text: str, marker_name: str) -> list[str]:
    if not marker_name:
        return []
    pattern = rf"([^\s\[\]]+)\[{re.escape(marker_name)}\]"
    return re.findall(pattern, text)


def _load_json_tokens(path: str | Path) -> list[str]:
    data = json.loads(_read_text(path))
    if isinstance(data, dict):
        if "args" in data:
            data = data["args"]
        else:
            raise SystemExit("--json-in file must be a JSON array or an object with an 'args' array")
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise SystemExit("--json-in file must contain a JSON array of strings")
    return data


def check_guidance_requirement(
    requi_path: str | Path,
    evidence_path: str | Path,
    required_filesystem_cues: Iterable[str] = (),
    marker_name: str = "REF_EXISTS",
    link_targets: Iterable[str] = (),
    link_files: Iterable[str | Path] = (),
) -> dict:
    report = {
        "ok": True,
        "checks": [],
        "paths": {
            "requirement": str(requi_path),
            "evidence": str(evidence_path),
            "link_files": [str(path) for path in link_files],
        },
        "marker_values": [],
    }

    def add_check(name: str, ok: bool, detail: str) -> None:
        report["checks"].append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            report["ok"] = False

    requi_file = Path(requi_path)
    evidence_file = Path(evidence_path)

    if requi_file.exists():
        requi_text = _read_text(requi_file)
        add_check("requirement_exists", True, f"found {requi_file}")
    else:
        requi_text = ""
        add_check("requirement_exists", False, f"missing {requi_file}")

    if evidence_file.exists():
        evidence_text = _read_text(evidence_file)
        add_check("evidence_exists", True, f"found {evidence_file}")
    else:
        evidence_text = ""
        add_check("evidence_exists", False, f"missing {evidence_file}")

    marker_values = _extract_marker_values(requi_text, marker_name) if requi_text else []
    report["marker_values"] = marker_values
    add_check(
        "marker_values",
        bool(marker_values),
        "extracted: " + ", ".join(marker_values) if marker_values else f"no markers found for name {marker_name}",
    )

    if evidence_text:
        missing_markers = _missing_items(evidence_text, marker_values)
        add_check(
            "marker_coverage",
            not missing_markers,
            "missing: " + ", ".join(missing_markers) if missing_markers else "all extracted markers present in evidence",
        )
        missing_cues = _missing_items(evidence_text, required_filesystem_cues)
        add_check(
            "filesystem_cues",
            not missing_cues,
            "missing: " + ", ".join(missing_cues) if missing_cues else "all filesystem cues present in evidence",
        )
    else:
        add_check("marker_coverage", False, "skipped because evidence text is unavailable")
        add_check("filesystem_cues", False, "skipped because evidence text is unavailable")

    if link_targets:
        link_texts = []
        for path in link_files:
            link_texts.append(_read_text(path) if Path(path).exists() else "")
        if link_texts:
            missing_links = [target for target in link_targets if not any(target in text for text in link_texts)]
            add_check(
                "link_targets",
                not missing_links,
                "missing: " + ", ".join(missing_links) if missing_links else "all link targets present",
            )
        else:
            add_check("link_targets", False, "no readable link files were provided")
    else:
        add_check("link_targets", True, "no optional link targets requested")

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="requi_file_checker",
        description="Reusable R4.1 checker; use --root and --path to resolve following file arguments.",
    )
    parser.add_argument("-v", "--version", action="version", version=f"requi_file_checker {__version__}")
    parser.add_argument("--root", help="Root folder for relative paths.")
    parser.add_argument("--path", help="Relative folder for following file arguments.")
    parser.add_argument("--json-in", help="JSON file of arguments to splice into the current command sequence.")
    parser.add_argument("--requi", help="Requirement file path relative to the current path.")
    parser.add_argument("--evidence", help="Evidence file path relative to the current path.")
    parser.add_argument(
        "--filesystem-cue",
        action="append",
        default=[],
        help="Required filesystem cue to check in the evidence text.",
    )
    parser.add_argument(
        "--marker",
        default="REF_EXISTS",
        help="Marker name in the requirement file; values after [MARKER] are checked against the evidence text.",
    )
    parser.add_argument("--link-target", action="append", default=[], help="Target text expected in a link file.")
    parser.add_argument("--link-file", action="append", default=[], help="Link file path relative to the current path.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    return parser


def parse_cli(argv: list[str] | None = None) -> dict:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(".")
    current_path = Path(".")
    requi_path: Path | None = None
    evidence_path: Path | None = None
    required_filesystem_cues: list[str] = []
    marker_name = "REF_EXISTS"
    link_targets: list[str] = []
    link_files: list[Path] = []
    json_inputs: list[Path] = []
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
            build_parser().print_help()
            raise SystemExit(0)
        if token in ("-v", "--version"):
            print(f"requi_file_checker {__version__}")
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
            required_filesystem_cues.append(need_value(i))
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
        "required_filesystem_cues": required_filesystem_cues,
        "marker": marker_name,
        "link_targets": link_targets,
        "link_files": link_files,
        "json_inputs": json_inputs,
        "json": emit_json,
    }


# R2-2: The CLI entrypoint is part of the requirement-aligned checker surface.
def main(argv: list[str] | None = None) -> int:
    parsed = parse_cli(argv)
    report = check_guidance_requirement(
        requi_path=parsed["requirement"],
        evidence_path=parsed["evidence"],
        required_filesystem_cues=parsed["required_filesystem_cues"],
        marker_name=parsed["marker"],
        link_targets=parsed["link_targets"],
        link_files=parsed["link_files"],
    )
    report["paths"]["root"] = parsed["root"]
    report["paths"]["json_inputs"] = [str(path) for path in parsed["json_inputs"]]
    if parsed["json"]:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        for check in report["checks"]:
            status = "PASS" if check["ok"] else "FAIL"
            print(f"{status} {check['name']}: {check['detail']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
