from __future__ import annotations

import html
import tempfile
import unittest
from pathlib import Path
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mimap_html import (
    build_concept_link_map,
    cli_main,
    default_output_path,
    export_all_mimaps,
    mimap_to_html,
    normalize_mimap_token,
    parse_mimap_lines,
    render_morphology_token,
    render_morphology_text,
)


class MimapHtmlTests(unittest.TestCase):
    def test_default_output_path_preserves_docs_folder_under_project_out(self):
        source = Path("/repo/prj/continuity_db/docs/000_phase/000-PH-001-MIMAP-thinking.md")
        expected = Path("/repo/prj/continuity_db/out/docs/000_phase/000-PH-001-MIMAP-thinking.html")
        self.assertEqual(default_output_path(source), expected)

    def test_default_output_path_for_non_docs_file_uses_sibling_html(self):
        self.assertEqual(default_output_path(Path("tmp/mimap.md")), Path("tmp/mimap.html"))

    def test_parse_mimap_lines_preserves_nested_bullet_levels(self):
        nodes = parse_mimap_lines([
            "think(ing)",
            "- purpos(s)",
            "  - learn(ing)",
            "    - form concept(s)",
        ])
        self.assertEqual([(n.level, n.text) for n in nodes], [
            (0, "think(ing)"),
            (1, "purpos(s)"),
            (2, "learn(ing)"),
            (3, "form concept(s)"),
        ])

    def test_render_morphology_token_suffix_keeps_stem_before_link(self):
        rendered = render_morphology_token("ment(al)")
        self.assertIn("ment", rendered)
        self.assertIn('href="#morph-al"', rendered)
        self.assertLess(rendered.index("ment"), rendered.index('href="#morph-al"'))

    def test_render_morphology_token_prefix_stem_suffix_order(self):
        rendered = render_morphology_token("(in)clude(s)")
        self.assertIn('href="#morph-in"', rendered)
        self.assertIn("clude", rendered)
        self.assertIn('href="#morph-s"', rendered)
        self.assertLess(rendered.index('href="#morph-in"'), rendered.index("clude"))
        self.assertLess(rendered.index("clude"), rendered.index('href="#morph-s"'))

    def test_render_morphology_text_escapes_plain_text_and_links_multiple_words(self):
        rendered = render_morphology_text("(de)fine <risk(s)>")
        self.assertIn('href="#morph-de"', rendered)
        self.assertIn("fine", rendered)
        self.assertIn("&lt;", rendered)
        self.assertIn('href="#morph-s"', rendered)
        self.assertNotIn("<risk", rendered)

    def test_normalize_mimap_token_removes_morphology_and_punctuation(self):
        self.assertEqual(normalize_mimap_token("(re)ason(ing),"), "reasoning")
        self.assertEqual(normalize_mimap_token("ment(al)"), "mental")

    def test_render_morphology_text_adds_concept_link_after_enriched_term(self):
        rendered = render_morphology_text("(re)ason(ing) uses (in)fer(ence)", {"reasoning": "000-PH-002-MIMAP-reasoning.html"})
        self.assertIn('href="#morph-re"', rendered)
        self.assertIn('href="#morph-ing"', rendered)
        self.assertIn('class="concept-link" href="000-PH-002-MIMAP-reasoning.html"', rendered)
        self.assertLess(rendered.index('href="#morph-ing"'), rendered.index('class="concept-link"'))
        self.assertNotIn('MIMAP-inference.html', rendered)

    def test_build_concept_link_map_finds_sibling_mimap_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "prj" / "continuity_db" / "docs" / "000_phase"
            docs.mkdir(parents=True)
            source = docs / "000-PH-003-MIMAP-inference.md"
            source.write_text("(in)fer(ence)\n", encoding="utf-8")
            (docs / "000-PH-001-MIMAP-thinking.md").write_text("think(ing)\n", encoding="utf-8")
            (docs / "000-PH-002-MIMAP-reasoning.md").write_text("(re)ason(ing)\n", encoding="utf-8")
            (docs / "000-PH-001-CREQ-MIMAP-HTML.md").write_text("requirement\n", encoding="utf-8")

            links = build_concept_link_map(source, default_output_path(source))

            self.assertEqual(links["thinking"], "000-PH-001-MIMAP-thinking.html")
            self.assertEqual(links["reasoning"], "000-PH-002-MIMAP-reasoning.html")
            self.assertNotIn("inference", links)
            self.assertNotIn("html", links)

    def test_mimap_to_html_contains_title_hierarchy_and_morphology_index(self):
        source = "think(ing)\n- (de)fini(tion)\n  - ment(al) activ(ity)\n"
        rendered = mimap_to_html(source, title="Thinking")
        self.assertIn("<!doctype html>", rendered)
        self.assertIn("<title>Thinking</title>", rendered)
        self.assertIn("mimap-tree", rendered)
        self.assertIn("morphology-index", rendered)
        self.assertIn('id="morph-al"', rendered)
        self.assertIn('id="morph-de"', rendered)
        self.assertIn('href="#morph-ing"', rendered)

    def test_cli_writes_html_to_out_docs_path_and_keeps_source_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "prj" / "continuity_db" / "docs" / "000_phase" / "000-PH-001-MIMAP-thinking.md"
            source.parent.mkdir(parents=True)
            original = "think(ing)\n- ment(al) activ(ity)\n"
            source.write_text(original, encoding="utf-8")

            with redirect_stdout(StringIO()):
                code = cli_main(["--mimap", str(source)])

            expected = root / "prj" / "continuity_db" / "out" / "docs" / "000_phase" / "000-PH-001-MIMAP-thinking.html"
            self.assertEqual(code, 0)
            self.assertTrue(expected.exists())
            self.assertIn('href="#morph-al"', expected.read_text(encoding="utf-8"))
            self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_cli_adds_links_to_related_sibling_mimaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "prj" / "continuity_db" / "docs" / "000_phase"
            docs.mkdir(parents=True)
            source = docs / "000-PH-003-MIMAP-inference.md"
            source.write_text("(in)fer(ence)\n- link to (re)ason(ing) and think(ing)\n", encoding="utf-8")
            (docs / "000-PH-001-MIMAP-thinking.md").write_text("think(ing)\n", encoding="utf-8")
            (docs / "000-PH-002-MIMAP-reasoning.md").write_text("(re)ason(ing)\n", encoding="utf-8")

            with redirect_stdout(StringIO()):
                code = cli_main(["--mimap", str(source)])

            output = default_output_path(source)
            html_text = output.read_text(encoding="utf-8")
            self.assertEqual(code, 0)
            self.assertIn('class="concept-link" href="000-PH-002-MIMAP-reasoning.html"', html_text)
            self.assertIn('class="concept-link" href="000-PH-001-MIMAP-thinking.html"', html_text)

    def test_export_all_mimaps_regenerates_every_mimap_with_fresh_cross_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "prj" / "continuity_db" / "docs" / "000_phase"
            docs.mkdir(parents=True)
            thinking = docs / "000-PH-001-MIMAP-thinking.md"
            reasoning = docs / "000-PH-002-MIMAP-reasoning.md"
            inference = docs / "000-PH-003-MIMAP-inference.md"
            thinking.write_text("think(ing)\n- uses (re)ason(ing) and (in)fer(ence)\n", encoding="utf-8")
            reasoning.write_text("(re)ason(ing)\n- part of think(ing) and uses (in)fer(ence)\n", encoding="utf-8")
            inference.write_text("(in)fer(ence)\n- part of (re)ason(ing)\n", encoding="utf-8")
            (docs / "000-PH-001-CREQ-MIMAP-HTML.md").write_text("requirement\n", encoding="utf-8")

            outputs = export_all_mimaps(docs, overwrite=True)

            self.assertEqual(len(outputs), 3)
            thinking_html = default_output_path(thinking).read_text(encoding="utf-8")
            reasoning_html = default_output_path(reasoning).read_text(encoding="utf-8")
            self.assertIn('href="000-PH-002-MIMAP-reasoning.html"', thinking_html)
            self.assertIn('href="000-PH-003-MIMAP-inference.html"', thinking_html)
            self.assertIn('href="000-PH-001-MIMAP-thinking.html"', reasoning_html)
            self.assertIn('href="000-PH-003-MIMAP-inference.html"', reasoning_html)
            self.assertFalse(default_output_path(docs / "000-PH-001-CREQ-MIMAP-HTML.md").exists())

    def test_cli_all_mimaps_regenerates_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "prj" / "continuity_db" / "docs" / "000_phase"
            docs.mkdir(parents=True)
            thinking = docs / "000-PH-001-MIMAP-thinking.md"
            reasoning = docs / "000-PH-002-MIMAP-reasoning.md"
            thinking.write_text("think(ing)\n- uses (re)ason(ing)\n", encoding="utf-8")
            reasoning.write_text("(re)ason(ing)\n- part of think(ing)\n", encoding="utf-8")

            with redirect_stdout(StringIO()) as buf:
                code = cli_main(["--all-mimaps", str(docs), "--overwrite"])

            self.assertEqual(code, 0)
            self.assertIn("000-PH-001-MIMAP-thinking.html", buf.getvalue())
            self.assertTrue(default_output_path(thinking).exists())
            self.assertTrue(default_output_path(reasoning).exists())
            self.assertIn('href="000-PH-002-MIMAP-reasoning.html"', default_output_path(thinking).read_text(encoding="utf-8"))

    def test_cli_refuses_to_overwrite_without_explicit_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "prj" / "demo" / "docs" / "map.md"
            source.parent.mkdir(parents=True)
            source.write_text("root\n", encoding="utf-8")
            output = default_output_path(source)
            output.parent.mkdir(parents=True)
            output.write_text("old", encoding="utf-8")

            with redirect_stderr(StringIO()):
                code = cli_main(["--mimap", str(source)])

            self.assertEqual(code, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "old")

    def test_cli_overwrite_replaces_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "map.md"
            source.write_text("root\n", encoding="utf-8")
            output = source.with_suffix(".html")
            output.write_text("old", encoding="utf-8")

            with redirect_stdout(StringIO()):
                code = cli_main(["--mimap", str(source), "--overwrite"])

            self.assertEqual(code, 0)
            self.assertIn("root", output.read_text(encoding="utf-8"))

    def test_cli_reports_missing_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.md"
            with redirect_stderr(StringIO()):
                code = cli_main(["--mimap", str(missing)])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
