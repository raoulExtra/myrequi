from pathlib import Path

import metacognitive_state_id_migrator
import metacognitive_state_reader
import table_row_markdown


REPO_ROOT = Path(__file__).resolve().parents[7]


def test_production_defaults_use_repository_root_database():
    expected = REPO_ROOT / "continuity.db"
    assert metacognitive_state_id_migrator.DEFAULT_DB == expected
    assert metacognitive_state_reader.DEFAULT_DB == expected
    assert table_row_markdown.DEFAULT_DB == expected


def test_duplicate_project_database_is_not_present():
    assert not (REPO_ROOT / "prj" / "continuity.db").exists()
