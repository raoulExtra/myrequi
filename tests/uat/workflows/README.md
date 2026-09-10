# UAT workflows

Run the user-acceptance baseline with:

```bash
python3 -m pytest tests/uat -m uat
```

The repository layout supplies automatic phase/component metadata:

- `unit`, `sit`, and `uat` identify execution phase.
- `core` and `extension` identify the implementation boundary.

Examples:

```bash
python3 -m pytest -m "unit and core"
python3 -m pytest -m "unit and extension"
python3 -m pytest -m "sit and core"
```

UAT workflows must exercise public boundaries and must not require the
optional `llm-guard` environment unless a workflow explicitly targets it.
