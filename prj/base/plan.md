# Plan: Generate core requi and core acc crit files

## Overview
This plan asks the user for the path to a `refined.md` file. Based on the provided path, two files will be created in the same directory as the `refined.md` file:
- `core_requi.md` – core requirements file
- `core_acc_crit.md` – core acceptance criteria file

## Steps
1. **Prompt user** for the absolute or relative path to a `refined.md` file.
2. **Validate** that the file exists and is readable.
3. **Create** `001-RC-requi_core.md` and `001-AC-acc_crit_core.md` in the same directory as the user‑supplied `refined.md` file (i.e., the parent folder of the given path), **following the naming and structure conventions** from `prj/self_learn/docs/000_phase/check/fsys/prj/refined.md`:
   - Use the abbreviation `RC` for core requirements and `AC` for core acceptance criteria.
   - Name the files `001-RC-requi_core.md` and `001-AC-acc_crit_core.md` (phase‑000 pattern).
   - Populate each file with the relevant extracted content from the user‑supplied `refined.md` (requirements for `RC`, acceptance criteria for `AC`).
4. **Verify** that both files are well‑formed and adhere to the conventions (optionally run a quick validation against the reference file).

## Expected Outcome
After the user provides the path, two markdown files will appear in the same directory as the provided `refined.md` file:
- `001-RC-requi_core.md` – core requirements derived from `refined.md` following the phase‑000 naming convention.
- `001-AC-acc_crit_core.md` – core acceptance criteria derived from `refined.md` following the same convention.
Both files will respect the abbreviation rules, folder‑naming guidelines, and version‑notation standards defined in the reference document.
