# Plan: Rename Phase References `phase_0/phase_1` → `000_phase/001_phase`

## TODO List

### Background
The project currently references `phase_0.md` and `phase_1.md` in multiple files. This plan updates all references to use the new naming convention `000_phase.md` / `001_phase.md`, consistent with the project's `V00_00_01` → `V00_00_01` rename pattern.

### [X] Completed: Identify All References
- [X] Found 10+ files referencing `phase_0.md` or `phase_1.md`
- [X] Categorized references: internal links, doc overviews, README, tool configs

### [X] Step 1: Update Internal Phase Files
- [X] **phase_0.md**: Update internal `[[Phase 1]]` link from `phase_1.md` → `001_phase.md`
- [X] **phase_1.md**: Update `inherits_from: phase_0` → `inherits_from: 000_phase` and all `[[Project phase 0]]` links → `[[000_phase]]`

### [X] Step 2: Update README.md
- [X] `prj/self_learn/README.md` - Change `phase_0.md` → `000_phase.md` and `phase_1.md` → `001_phase.md` in:
  - Table of contents entries
  - Bullet list entries
  - Any other references

### [X] Step 3: Update Docs Overview Files
- [X] `prj/self_learn/docs/000_phase/auto/overview.md` - Update `[[Phase 1]]` link → `[[001_phase]]`
- [X] `prj/self_learn/docs/overview.md` - Update table of contents `phase_0.md` → `000_phase.md` and `phase_1.md` → `001_phase.md`

### [X] Step 4: Update All Remaining Self-Learn Files
- [X] Check and update any other `.md` or `.py` files with phase references
- [X] Verify no remaining `phase_0.md` or `phase_1.md` references in `prj/self_learn/` (excluding `prj/demo/`)

### [X] Step 5: Verify Changes
- [X] Confirm `phase_0.md` and `phase_1.md` still exist (backward compatibility) OR confirm they've been renamed
- [X] Verify all links resolve correctly with new naming
- [X] Run any available tests to confirm integrity

### [X] Step 6: Update Plan Markers
- [X] Mark all TODO items as completed in `prj/self_learn/plans/002-plan-change-phase-references.md`

---

## Reference Summary (before rename)

### Files referencing `phase_0.md`:
| File | Type of Reference |
|------|------------------|
| `prj/self_learn/phase_1.md` | `[[Project phase 0]]`, `[[Base project phase 0]]`, `[[Continuity_db phase 0]]` |
| `prj/self_learn/phase_0.md` | `[[Phase 1]](phase_1.md)` (internal link) |
| `prj/self_learn/README.md` | TOC entries: `phase_0.md`, `phase_1.md` |
| `prj/self_learn/docs/000_phase/auto/overview.md` | `[[Phase 1]]` |
| `prj/self_learn/docs/overview.md` | TOC entries: `phase_0.md`, `phase_1.md` |

### Files referencing `phase_1.md`:
| File | Type of Reference |
|------|------------------|
| `prj/self_learn/phase_0.md` | `[[Phase 1]](phase_1.md)` (internal link) |
| `prj/self_learn/phase_1.md` | `inherits_from: phase_0`, `[[Project phase 0]]`, `[[Base project phase 0]]`, `[[Continuity_db phase 0]]` |
| `prj/self_learn/README.md` | TOC entries: `phase_0.md`, `phase_1.md` |
| `prj/self_learn/docs/000_phase/auto/overview.md` | `[[Phase 1]]` |
| `prj/self_learn/docs/overview.md` | TOC entries: `phase_0.md`, `phase_1.md` |

---

## New Naming Convention
| Old Name | New Name |
|----------|----------|
| `phase_0.md` | `000_phase.md` |
| `phase_1.md` | `001_phase.md` |
| `[[Phase 1]]` | `[[001_phase]]` |
| `[[Project phase 0]]` | `[[000_phase]]` |
| `inherits_from: phase_0` | `inherits_from: 000_phase` |

---

**Plan saved to**: `prj/self_learn/plans/002-plan-change-phase-references.md`