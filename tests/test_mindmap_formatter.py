import shutil
import tempfile
import unittest
from pathlib import Path

import mindmap_formatter


class MindmapFormatterTests(unittest.TestCase):
    def test_load_affixes_reads_common_prefixes_and_suffixes(self):
        conn = mindmap_formatter.connect()
        try:
            prefixes, suffixes = mindmap_formatter.load_affixes(conn)
        finally:
            conn.close()

        self.assertIn('trans', prefixes)
        self.assertIn('con', prefixes)
        self.assertIn('ment', suffixes)
        self.assertIn('ation', suffixes)
        self.assertIn('cy', suffixes)

    def test_split_word_uses_prefix_and_suffix(self):
        prefixes = ['trans', 'con', 'comp']
        suffixes = ['ation', 'cy', 'ment', 's']
        self.assertEqual(mindmap_formatter.split_word('transportation', prefixes, suffixes), '(trans)port(ation)')
        self.assertEqual(mindmap_formatter.split_word('movement', prefixes, suffixes), 'move(ment)')
        self.assertEqual(mindmap_formatter.split_word('concurrency', prefixes, suffixes), '(con)curren(cy)')
        self.assertEqual(mindmap_formatter.split_word('components', prefixes, suffixes), '(comp)onent(s)')

    def test_format_text_keeps_markdown_formats_words_and_pluralizes(self):
        prefixes = ['trans']
        suffixes = ['ation', 'ment']
        text = '# Road\n- transportation of goods\n- roads and men\n'
        formatted = mindmap_formatter.format_text(text, prefixes, suffixes)
        self.assertIn('(trans)port(ation)', formatted)
        self.assertIn('good(s)', formatted)
        self.assertIn('road(s)', formatted)
        self.assertIn('man(s)', formatted)
        self.assertIn('# road', formatted)

    def test_format_file_inplace(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            src = tmpdir / 'sample.md'
            src.write_text('navigation and transportation and roads', encoding='utf-8')
            out = mindmap_formatter.format_file(src, inplace=True)
            self.assertTrue(src.exists())
            self.assertEqual(src.read_text(encoding='utf-8'), out)
            self.assertIn('(trans)port(ation)', out)
            self.assertIn('navig(ation)', out)
            self.assertIn('road(s)', out)
        finally:
            shutil.rmtree(tmpdir)

    def test_formatter_is_idempotent_on_already_formatted_text(self):
        prefixes = ['trans', 'comp']
        suffixes = ['ation', 's']
        text = '(trans)port(ation) and (comp)onent(s)'
        first = mindmap_formatter.format_text(text, prefixes, suffixes)
        second = mindmap_formatter.format_text(first, prefixes, suffixes)
        self.assertEqual(first, text)
        self.assertEqual(second, text)

    def test_format_text_formats_edge_words(self):
        prefixes = ['trans']
        suffixes = ['ation', 's']
        text = 'navigation and roads'
        formatted = mindmap_formatter.format_text(text, prefixes, suffixes)
        self.assertEqual(formatted, 'navig(ation) and road(s)')


if __name__ == '__main__':
    unittest.main()
