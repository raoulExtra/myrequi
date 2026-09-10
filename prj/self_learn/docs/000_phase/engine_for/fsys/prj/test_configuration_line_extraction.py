import pytest

from .checker_for_conf import extract_lines


def test_configuration_line_extraction(tmp_path):
    input_path = tmp_path / "test_config.md"
    input_path.write_text(
        """This is a test configuration file.
Include this line.
Exclude this line.
Include another line.
Exclude another line.
""",
        encoding="utf-8",
    )

    output_path = tmp_path / "test_config+extr.md"
    extract_lines(input_path, output_path, "Include", "Exclude")

    assert output_path.read_text(encoding="utf-8").splitlines() == [
        "Include this line.",
        "Include another line.",
    ]


def test_configuration_line_extraction_with_no_matches(tmp_path):
    input_path = tmp_path / "empty.conf"
    output_path = tmp_path / "result.conf"
    input_path.write_text("unrelated\n", encoding="utf-8")

    extract_lines(input_path, output_path, "Include", "Exclude")

    assert output_path.read_text(encoding="utf-8") == ""


def test_configuration_line_extraction_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        extract_lines(tmp_path / "missing.conf", tmp_path / "result.conf", "Include", "Exclude")
