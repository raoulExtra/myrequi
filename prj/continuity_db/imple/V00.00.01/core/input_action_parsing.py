"""Pure input parsing helpers for the continuity database router."""

import json
from typing import Any, Optional, Tuple


SUPPORTED_STRUCTURED_INPUT_TYPES = {"json", "structured"}


def parse_input(input_text: str, input_type: str) -> Tuple[Optional[Any], str]:
    """Parse structured input when requested and return normalized text.

    Invalid JSON deliberately falls back to plain-text routing, preserving the
    router's existing behavior.
    """
    parsed_input = None
    if input_type in SUPPORTED_STRUCTURED_INPUT_TYPES:
        try:
            parsed_input = json.loads(input_text)
        except json.JSONDecodeError:
            pass
    return parsed_input, input_text.strip()
