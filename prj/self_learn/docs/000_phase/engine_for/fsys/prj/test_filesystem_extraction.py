import pytest
from pathlib import Path
from checker_for_conf import extract_lines

def test_filesystem_extraction(tmp_path):
    # Create a temporary input file
    input_filename = "test_config.md"
    input_content = """This is a test configuration file.
Include this line.
Exclude this line.
Include another line.
Exclude another line.
"""
    (tmp_path / input_filename).write_text(input_content)

    # Define patterns for inclusion and exclusion
    include_pattern = "Include"
    exclude_pattern = "Exclude"

    # Run the extraction script
    output_filename = f"{input_filename}+extr.md"
    extract_lines(str(tmp_path / input_filename), str(tmp_path / output_filename), include_pattern, exclude_pattern)

    # Read the output file and check its content
    expected_output = [
        "Include this line.",
        "Include another line."
    ]
    actual_output = (tmp_path / output_filename).read_text().splitlines()
    assert actual_output == expected_output