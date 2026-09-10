"""Extract matching lines from configuration files."""

from pathlib import Path
from typing import Union


PathLike = Union[str, Path]


def extract_lines(
    input_filename: PathLike,
    output_filename: PathLike,
    include_pattern: str,
    exclude_pattern: str,
) -> None:
    """Write lines containing the include pattern but not the exclude pattern."""
    input_path = Path(input_filename)
    output_path = Path(output_filename)
    lines = input_path.read_text(encoding="utf-8").splitlines(keepends=True)
    matching_lines = (
        line for line in lines
        if include_pattern in line and exclude_pattern not in line
    )
    output_path.write_text("".join(matching_lines), encoding="utf-8")
