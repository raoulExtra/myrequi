# Conventions

## Where to Store Conventions

Project-wide conventions live in two places:

- **`CONVENTIONS.md`** (this file) – human-facing style/naming/process conventions.
- **`continuity.db` → `object_metadata` where `object_type = 'convention'`** – enforced policies (data storage, recording, storage, memory, README canonical name). Policy-keyed, not duplicated here.

## Convention Categories

| Category | Location | Description |
|----------|----------|-------------|
| File organization | `prj/` folder structure | How project files should be organized |
| Project phases | `policy:project.phase_structure` in `continuity.db` | Every project must have at least phase 0; `docs/000_phase/` is the starting folder and `000-plan.md` is the anchor |
| Naming standards | `CONVENTIONS.md` | Naming rules for files, variables, functions |
| Documentation style | `README.md` | Markdown doc format and length guidelines |
| Code patterns | `patterns_for/` | Extraction patterns for MD project docs |
| Planning formats | `plans/` | Plan file templates and structure |
| Review processes | `review_checklist.md` | Steps for peer/code reviews |

## Quick Reference

- **File naming**: Use descriptive, lowercase, hyphen-separated names (e.g., `001-phase.md`)
- **Header format**: Markdown headings (`#`, `##`, `###`) for section structure
- **Code fences**: Wrap code in triple backticks (```)
- **Observations, beliefs, decisions, README usage**: See `continuity.db` → `object_metadata` where `object_type = 'convention'`. These are enforced as `policy:data.*` and `policy:readme.*` keys.

## Updating Conventions

To add or modify a convention:
1. Edit `CONVENTIONS.md`
2. Commit the change to the repo
3. The AI will automatically pick up the update on next visit
