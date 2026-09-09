# Plan: Generate core requi and core acc crit files per refined.md conventions

## Overview
Based on the conventions from `prj/self_learn/docs/000_phase/check/fsys/prj/refined.md`, this plan generates core requirement (RC) and core acceptance criteria (AC) file pairs. The phase index is derived from the source folder name (`000_phase` → phase `000`).

## Source Document
- **refined.md path:** `prj/self_learn/docs/000_phase/check/fsys/prj/refined.md`
- **Phase index:** `000` (extracted from `000_phase` folder)

## Requirement‑Goal Set (from Section 1 of refined.md)
The following core requirement elements are defined with their abbreviations:

| # | Element | Abbreviation |
|---|---------|--------------|
| 1 | `project` | `prj` |
| 2 | `project_inherited` | `prj` |
| 3 | `phase` | `p` |
| 4 | `module` | `mod` |
| 5 | `requi_core` | `RC` |
| 6 | `acc_crit_core` | `AC` |
| 7 | `version` | `V` |
| 8 | `implementation` | `imple` |
| 9 | `test` | `test` |
|10 | `test_type` | (unit \| int \| system \| git \| uat) |

## Generated File Pairs
For each requirement number `i` from 1 through 10, the following files are generated in `prj/base/plans/`:

### RC File: `{phase_index}{i}-RC-requi_core.md`
- **Title:** "Core Requirement {i}"
- **Content:** Element name and Abbreviation from the table above.
- **Example (i=1):** `0001-RC-requi_core.md` — Core Requirement 1: project — `prj`

### AC File: `{phase_index}{i}-AC-acc_crit_core.md`
- **Section 2:** Abbreviation Reference table (full names and abbreviations for: project, project_inherited, phase, module, requi_core, acc_crit_core, version, implementation, test, test_type).
- **Section 3:** Folder‑Naming Rules:
  - Project root: `prj`
  - Sub‑folders (under `prj`): `plans`, `docs`, `examples`, `imple`, `assets`
- **Section 4:** File‑Naming Conventions:
  - **Phase document pattern:** `000-P-###-<project_element_abbrev><topic>[<module_name>]0..n`
  - `###` is a three‑digit index ordering documents within the project (e.g., `001`, `002`, … `900`).
  - `-` separates the phase marker from the index and the element abbreviation.
  - `<project_element_abbrev>` is the abbreviation as defined (e.g., `prj`, `p`, `mod`, `RC`, `AC`, `V`, `imple`, `test`).
  - `<topic>` is a short descriptive term (no spaces).
  - `[<module_name>]0..n` is an optional module suffix.
  - **Examples:**
    - `000-P-001-prj-project.md` — project‑root core requirement (phase 000).
    - `000-P-002-prj-inherited.md` — inherited project marker (phase 000).
    - `000-P-003-p-phase.md` — phase description (phase 000).
    - `000-P-004-mod-module.md` — module definition (phase 000).
    - `000-P-005-RC-requi_core.md` — core requirement set (phase 000).
    - `000-P-006-AC-acc_crit_core.md` — acceptance‑criteria core (phase 000).
    - `000-P-007-V-version.md` — version notation (phase 000).
    - `000-P-008-imple-implementation.md` — implementation overview (phase 000).
    - `000-P-009-test-test.md` — test strategy (phase 000).
    - `000-P-010-test_type-list.md` — test‑type list (phase 000).
- **Section 5:** Version Notation:
  - **In‑file content:** `V00.00.01` (dot‑separated major.minor.patch).
  - **On the filesystem:** `V00_00_01` (underscore‑separated, used in folder/file names).
- **Section 6:** Implementation Folder:
  - The `imple` folder contains all implementation artifacts (source code, binaries, compiled assets, etc.).
  - Structure within `imple` may mirror the module layout, but must respect the overall `prj` root conventions.

## Generated File Count
- **10 RC files:** `0001-RC-requi_core.md` through `0010-RC-requi_core.md`
- **10 AC files:** `0001-AC-acc_crit_core.md` through `0010-AC-acc_crit_core.md`

## Conformance
All generated files adhere to the abbreviation rules, folder‑naming guidelines, file‑naming conventions, and version‑notation standards defined in `prj/self_learn/docs/000_phase/check/fsys/prj/refined.md`. The phase index `000` is embedded in filenames to indicate the origin phase.

## Next Steps
1. Generate the 20 markdown files per the specifications above.
2. Validate each file against the conventions in refined.md.
3. Move completed work plans to the `done` folder.