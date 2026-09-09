# Project Requirement Goal Check (Refined)

**Purpose**
This document refines the original `000-P-RG-check-fsys-prj-requi-goal.md` checklist into a clearer, more maintainable format. It outlines the valid requirement‑goal set for project files, abbreviation conventions, folder‑naming rules, file‑naming conventions, and version‑notation standards.

Make sure that Core requirements must relate to chapters ## <number>. <title_in_this_md_file>. points below lead to acc criterias.
---

## 1. Requirement‑Goal Set Validity
The following elements are recognised as **core requirements (RC)** for any project file:

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
|10 | `test_type` | (list) |

> **Note:** The `test_type` field accepts a single entry from the list `(unit \| int \| system \| git \| uat)`.

---

## 2. Abbreviation Reference
| Full Name | Abbreviation |
|-----------|--------------|
| project | `prj` |
| project_inherited | `prj` |
| phase | `p` |
| module | `mod` |
| requi_core | `RC` |
| acc_crit_core | `AC` |
| version | `V` |
| implementation | `imple` |
| test | `test` |
| test_type (list) | – |

These abbreviations are used consistently in filenames and folder structures.

---

## 3. Folder‑Naming Rules
| Folder | Rule |
|--------|------|
| **Project root** | named `prj` |
| **Sub‑folders (under `prj`)** | `plans`, `docs`, `examples`, `imple`, `assets` |

*All project‑specific documentation should reside under the `docs` folder.*

---

## 4. File‑Naming Conventions
### 4.1 Project‑level files
- **Pattern:** `project_name` + `docs` + optional `module_name` + numeric index + file type.
- **Example:** `myprojectdocs01_intro.md`

### 4.2 Phase documents
- **Pattern for the `000_phase` folder:** `000-P-###-<project_element_abbrev><topic>[<module_name>]0..n`
  - `###` is a three‑digit index that orders the documents within the project (e.g., `001`, `002`, … `900`).
  - e.g.`000-P` is the phase marker indicating phase  000 for all documents in this folder. The phase number can be derived from the filename path.
  - `-` separates the phase marker from the index and the element abbreviation.
  - `<project_element_abbrev>` is the abbreviation as defined in the Abbreviation Reference table (e.g., `prj`, `p`, `mod`, `RC`, `AC`, `V`, `imple`, `test`).
  - `<topic>` is a short descriptive term (no spaces).
  - `[<module_name>]0..n` is an optional module suffix; when present the filename becomes `000-P-###-<abbrev><topic>[<module_name>]0..n`.

**Examples (using the `000_phase` pattern)**
- `000-P-001-prj-project.md` – project‑root core requirement (phase 000).
- `000-P-002-prj-inherited.md` – inherited project marker (phase 000).
- `000-P-003-p-phase.md` – phase description (phase 000).
- `000-P-004-mod-module.md` – module definition (phase 000).
- `000-P-005-RC-requi_core.md` – core requirement set (phase 000).
- `000-P-006-AC-acc_crit_core.md` – acceptance‑criteria core (phase 000).
- `000-P-007-V-version.md` – version notation (phase 000).
- `000-P-008-imple-implementation.md` – implementation overview (phase 000).
- `000-P-009-test-test.md` – test strategy (phase 000).
- `000-P-010-test_type-list.md` – test‑type list (phase 000).

### 4.3 Version notation
- **In‑file content:** `V00.00.01` (dot‑separated major.minor.patch).
- **On the filesystem:** `V00_00_01` (underscore‑separated, used in folder/file names).

---

## 5. Implementation Folder
- The `imple` folder contains all implementation artifacts (source code, binaries, compiled assets, etc.).
- Structure within `imple` may mirror the module layout, but must respect the overall `prj` root conventions.

---

## 6. Summary
- **Core RC elements** are defined and abbreviated.
- **Folder hierarchy** is strict: `prj/` → `plans`, `docs`, `examples`, `imple`, `assets`.
- **File names** follow a phased `P-###-<abbrev><topic>` pattern, with version notation consistent between content and filesystem.
- Adhering to these rules ensures **automated validation**, **clear navigation**, and **consistent version tracking** across the project.

--- 

**Note:** All core requirement files currently belong to phase **000**.

*Generated from the original checklist and refined for clarity, consistency, and maintainability.*