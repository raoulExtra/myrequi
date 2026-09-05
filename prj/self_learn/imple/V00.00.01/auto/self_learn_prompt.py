from __future__ import annotations

import os
import sys


def ask(
    question: str,
    options: list[str] | None = None,
    note: str = "",
    default: str = "",
) -> str:
    if note:
        print(f"note: {note}")
    if options:
        for idx, option in enumerate(options, 1):
            print(f"  {idx}) {option}")
        prompt = f"{question} [1-{len(options)}]"
    else:
        prompt = question
    if default:
        prompt += f" (default: {default})"
    prompt += ": "

    if not sys.stdin.isatty():
        answer = os.environ.get("SELF_LEARN_ANSWER", "")
        if answer:
            return answer
        if default:
            return default
        raise RuntimeError(
            "non-interactive mode requires SELF_LEARN_ANSWER env var or a default"
        )

    answer = input(prompt).strip()
    if not answer and default:
        return default
    if options and answer.isdigit():
        idx = int(answer) - 1
        if 0 <= idx < len(options):
            return options[idx]
    return answer
