# Conventions

## Where to Store Conventions

All project-wide conventions are stored in this file:

**`CONVENTIONS.md`** – located at the project root (`/home/peter/xmyrequi/myrequi/prj/CONVENTIONS.md`).

## Convention Categories

| Category | Location | Description |
|----------|----------|-------------|
| File organization | `prj/` folder structure | How project files should be organized |
| Naming standards | `CONVENTIONS.md` | Naming rules for files, variables, functions |
| Documentation style | `README.md` | Markdown doc format and length guidelines |
| Code patterns | `patterns_for/` | Extraction patterns for MD project docs |
| Planning formats | `plans/` | Plan file templates and structure |
| Review processes | `review_checklist.md` | Steps for peer/code reviews |

## Quick Reference

- **File naming**: Use descriptive, lowercase, hyphen-separated names (e.g., `001-phase.md`)
- **Header format**: Markdown headings (`#`, `##`, `###`) for section structure
- **README usage**: Use `README.md` for project overview instead of `overview.md`
- **Code fences**: Wrap code in triple backticks (```)
- **Observations**: Store project insights in `continuity.db` (observations table)
- **Beliefs**: Store persistent claims in `beliefs` table with confidence scores
- **Decisions**: Record important choices in `decisions` table with rationale

## Updating Conventions

To add or modify a convention:
1. Edit `CONVENTIONS.md`
2. Commit the change to the repo
3. The AI will automatically pick up the update on next visit
