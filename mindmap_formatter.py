#!/usr/bin/env python3
"""Format mindmap text with morphology-aware affix splitting.

The formatter reads common prefix/suffix tags from continuity.db concepts:
- morphology.common_prefixes
- morphology.common_suffixes

It applies them to plain word tokens while preserving markdown structure,
non-word punctuation, and simple plural notation.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "continuity.db"
PREFIX_CONCEPT = "morphology.common_prefixes"
SUFFIX_CONCEPT = "morphology.common_suffixes"

WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


_META_TAGS = {'common_prefix', 'common_suffix', 'prefix_list', 'suffix_list', 'morphology'}


def _load_tags(conn: sqlite3.Connection, concept_key: str) -> list[str]:
    row = conn.execute(
        """
        select om.tags_json
        from object_metadata om
        where om.object_type='concept' and om.object_key=?
        """,
        (concept_key,),
    ).fetchone()
    if not row or not row[0]:
        return []
    try:
        tags = json.loads(row[0])
    except json.JSONDecodeError:
        return []
    out = []
    for tag in tags:
        tag = str(tag).strip().lower()
        if not tag or tag in _META_TAGS:
            continue
        if not re.fullmatch(r'[a-z]+', tag):
            continue
        out.append(tag)
    return out


def load_affixes(conn: sqlite3.Connection) -> tuple[list[str], list[str]]:
    prefixes = _load_tags(conn, PREFIX_CONCEPT)
    suffixes = _load_tags(conn, SUFFIX_CONCEPT)
    prefixes = sorted(set(prefixes), key=lambda s: (-len(s), s))
    suffixes = sorted(set(suffixes), key=lambda s: (-len(s), s))
    return prefixes, suffixes


def _looks_like_acronym(word: str) -> bool:
    return len(word) > 1 and word.isupper()


IRREGULAR_PLURALS = {
    'men': 'man',
    'women': 'woman',
    'children': 'child',
    'people': 'person',
    'mice': 'mouse',
    'geese': 'goose',
    'teeth': 'tooth',
    'feet': 'foot',
    'lice': 'louse',
    'oxen': 'ox',
    'data': 'datum',
    'criteria': 'criterion',
    'phenomena': 'phenomenon',
    'media': 'medium',
}


def _plural_base(word: str) -> tuple[str, bool]:
    lower = word.lower()
    if lower in IRREGULAR_PLURALS:
        return IRREGULAR_PLURALS[lower], True
    if lower.endswith('ies') and len(lower) > 4:
        return lower[:-3] + 'y', True
    if lower.endswith(('ses', 'xes', 'zes', 'ches', 'shes')) and len(lower) > 4:
        return lower[:-2], True
    if lower.endswith('s') and len(lower) > 3 and not lower.endswith(('ss', 'us', 'is')):
        return lower[:-1], True
    return lower, False


def _split_affixes(word: str, prefixes: list[str], suffixes: list[str]) -> str:
    if not word or not word.isalpha() or _looks_like_acronym(word):
        return word

    lower = word.lower()

    prefix = next((p for p in prefixes if len(p) >= 2 and lower.startswith(p) and len(lower) - len(p) >= 2), "")
    suffix = next((s for s in suffixes if len(s) >= 2 and lower.endswith(s) and len(lower) - len(s) >= 2), "")

    if not prefix and not suffix:
        return lower

    start = len(prefix)
    end = len(lower) - len(suffix) if suffix else len(lower)
    stem = lower[start:end]
    if len(stem) < 2:
        return lower

    parts = []
    if prefix:
        parts.append(f"({prefix})")
    parts.append(stem)
    if suffix:
        parts.append(f"({suffix})")
    return "".join(parts)


def format_word(word: str, prefixes: list[str], suffixes: list[str]) -> str:
    if not word or not word.isalpha() or _looks_like_acronym(word):
        return word

    base, is_plural = _plural_base(word)
    formatted = _split_affixes(base, prefixes, suffixes)
    if is_plural:
        return f"{formatted}(s)"
    return formatted


# Backward-compatible alias for older tests and callers.
def split_word(word: str, prefixes: list[str], suffixes: list[str]) -> str:
    return format_word(word, prefixes, suffixes)


def format_text(text: str, prefixes: list[str], suffixes: list[str]) -> str:
    parts = []
    last = 0
    for match in WORD_RE.finditer(text):
        start, end = match.span()
        left = text[start - 1] if start > 0 else ''
        right = text[end] if end < len(text) else ''
        parts.append(text[last:start])
        if (left and left in '()') or (right and right in '()'):
            parts.append(match.group(0))
        else:
            parts.append(format_word(match.group(0), prefixes, suffixes))
        last = end
    parts.append(text[last:])
    return ''.join(parts)


def format_file(path: Path, db_path: Path = DB_PATH, inplace: bool = True) -> str:
    conn = connect(db_path)
    try:
        prefixes, suffixes = load_affixes(conn)
    finally:
        conn.close()
    original = path.read_text(encoding="utf-8")
    formatted = format_text(original, prefixes, suffixes)
    if inplace:
        path.write_text(formatted, encoding="utf-8")
    return formatted


def main() -> None:
    parser = argparse.ArgumentParser(description="Morphology-aware mindmap formatter")
    parser.add_argument("path", nargs="?", help="File to format; reads stdin if omitted")
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--inplace", action="store_true", help="Rewrite the file in place")
    args = parser.parse_args()

    db_path = Path(args.db)
    conn = connect(db_path)
    try:
        prefixes, suffixes = load_affixes(conn)
    finally:
        conn.close()

    if args.path:
        path = Path(args.path)
        text = path.read_text(encoding="utf-8")
        out = format_text(text, prefixes, suffixes)
        if args.inplace:
            path.write_text(out, encoding="utf-8")
        print(out)
    else:
        import sys

        text = sys.stdin.read()
        print(format_text(text, prefixes, suffixes), end="")


if __name__ == "__main__":
    main()
