from __future__ import annotations

# R2-2: These tests keep the checker code aligned with the base Python-code requirement.
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DEMO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_DIR = DEMO_ROOT / "examples/r4_1_checker"
sys.path.insert(0, str(ROOT))

from requi_file_checker import _extract_marker_values, _load_json_tokens, _missing_items, _read_text, build_parser, check_guidance_requirement, main, parse_cli, __version__


# R2-2: Test coverage is part of the traceable code-to-requirement alignment.
class R41CheckTests(unittest.TestCase):
    def _example_paths(self) -> tuple[Path, Path, Path]:
        return (
            EXAMPLE_DIR / "requi_t_ok.md",
            EXAMPLE_DIR / "evidence_ok.md",
            EXAMPLE_DIR / "phase_1_1_ok.md",
        )

    def test_read_text_reads_example_file(self):
        self.assertEqual(_read_text(EXAMPLE_DIR / "requi_t_ok.md"), "# R4 requirement example with marker lines\n\ncontinuity.db[REF_EXISTS]\nstarter.md[REF_EXISTS]\nfilesystem[REF_EXISTS]\n")

    def test_missing_items_reports_only_missing_nonempty_entries(self):
        self.assertEqual(_missing_items("continuity.db docs/ starter.md", ["continuity.db", "", "starter.md", "plans/"]), ["plans/"])

    def test_extract_marker_values_finds_term_before_marker(self):
        self.assertEqual(_extract_marker_values("continuity.db[REF_EXISTS] starter.md[REF_EXISTS]", "REF_EXISTS"), ["continuity.db", "starter.md"])

    def test_load_json_tokens_reads_args_array(self):
        self.assertEqual(_load_json_tokens(EXAMPLE_DIR / "config.json"), [
            "--path", ".",
            "--requi", "004-requi-continuity-db-starter-guidance.md",
            "--path", "docs",
            "--evidence", "memory-and-filesystem-guidance.md",
            "--filesystem-cue", "docs/",
            "--marker", "REF_EXISTS",
            "--path", "examples/r4_1_checker",
            "--link-file", "phase_1_1_ok.md",
            "--link-target", "004.1-requi-continuity-db-file-level-evidence.md",
            "--json",
        ])

    def test_build_parser_supports_version_flag(self):
        parser = build_parser()
        with self.assertRaises(SystemExit) as ctx:
            parser.parse_args(["-v"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertEqual(__version__, "V00.00.01")

    def test_parse_cli_resolves_json_in_file_from_root(self):
        parsed = parse_cli([
            "--root", str(DEMO_ROOT),
            "--json-in", "examples/r4_1_checker/config.json",
        ])
        self.assertEqual(parsed["root"], str(DEMO_ROOT))
        self.assertEqual(Path(parsed["requirement"]), DEMO_ROOT / "004-requi-continuity-db-starter-guidance.md")
        self.assertEqual(Path(parsed["evidence"]), DEMO_ROOT / "docs/memory-and-filesystem-guidance.md")
        self.assertEqual([Path(p) for p in parsed["link_files"]], [DEMO_ROOT / "examples/r4_1_checker/phase_1_1_ok.md"])
        self.assertEqual(parsed["marker"], "REF_EXISTS")
        self.assertEqual(parsed["link_targets"], ["004.1-requi-continuity-db-file-level-evidence.md"])
        self.assertEqual([Path(p) for p in parsed["json_inputs"]], [DEMO_ROOT / "examples/r4_1_checker/config.json"])

    def test_version_flag_shows_version(self):
        buf = StringIO()
        with redirect_stdout(buf):
            with self.assertRaises(SystemExit) as ctx:
                main(["-v"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("requi_file_checker V00.00.01", buf.getvalue())

    def test_check_guidance_requirement_passes_with_example_files(self):
        requi, evidence, link_file = self._example_paths()
        report = check_guidance_requirement(
            requi_path=requi,
            evidence_path=evidence,
            required_filesystem_cues=["phase_*.md", "docs/", "examples/", "references/", "assets/", "archive/", "decisions/", "plans/", "imple/<version>/", "imple/<version>/test/"],
            marker_name="REF_EXISTS",
            link_targets=["004.1-requi-continuity-db-file-level-evidence.md"],
            link_files=[link_file],
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["marker_values"], ["continuity.db", "starter.md", "filesystem"])
        self.assertTrue(all(item["ok"] for item in report["checks"]))

    def test_check_guidance_requirement_reports_missing_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            requi = tmp / "requi.md"
            evidence = tmp / "evidence.md"
            requi.write_text("continuity.db[REF_EXISTS]", encoding="utf-8")
            report = check_guidance_requirement(
                requi_path=requi,
                evidence_path=evidence,
                required_filesystem_cues=["docs/"],
                marker_name="REF_EXISTS",
            )
            self.assertFalse(report["ok"])
            names = {item["name"] for item in report["checks"]}
            self.assertIn("evidence_exists", names)
            self.assertIn("marker_coverage", names)

    def test_check_guidance_requirement_reports_link_targets(self):
        _, evidence, link_file = self._example_paths()
        report = check_guidance_requirement(
            requi_path=EXAMPLE_DIR / "requi_t_ok.md",
            evidence_path=evidence,
            required_filesystem_cues=["docs/"],
            link_targets=["missing-target.md"],
            link_files=[link_file],
            marker_name="REF_EXISTS",
        )
        self.assertFalse(report["ok"])
        self.assertIn("link_targets", {item["name"] for item in report["checks"]})

    def test_main_json_emits_json_from_json_in(self):
        buf = StringIO()
        with redirect_stdout(buf):
            exit_code = main([
                "--root", str(DEMO_ROOT),
                "--json-in", "examples/r4_1_checker/config.json",
            ])
        self.assertEqual(exit_code, 0)
        report = json.loads(buf.getvalue())
        self.assertTrue(report["ok"])
        self.assertEqual(report["paths"]["root"], str(DEMO_ROOT))
        self.assertEqual(report["paths"]["requirement"], str(DEMO_ROOT / "004-requi-continuity-db-starter-guidance.md"))
        self.assertEqual(report["paths"]["evidence"], str(DEMO_ROOT / "docs/memory-and-filesystem-guidance.md"))
        self.assertEqual(report["paths"]["json_inputs"], [str(DEMO_ROOT / "examples/r4_1_checker/config.json")])

    def test_cli_returns_nonzero_for_missing_marker(self):
        requi = EXAMPLE_DIR / "requi_no_marker.md"
        evidence = EXAMPLE_DIR / "evidence_ok.md"
        exit_code = main([
            "--requi", str(requi),
            "--evidence", str(evidence),
            "--filesystem-cue", "docs/",
            "--marker", "REF_EXISTS",
        ])
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
