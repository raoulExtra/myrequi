# Plan: Rename Phase References in `prj/demo/`

## TODO List

### Background
The `prj/demo/` project uses `phase_0.md` and `phase_1_1.md` with `phase_1_1` references throughout. This plan updates all references to use the new naming convention consistent with the main `prj/self_learn/` rename pattern.

### [X] Step 1: Rename Demo Phase Files
- [X] `prj/demo/phase_0.md` → `prj/demo/000_phase.md`
- [X] `prj/demo/phase_1_1.md` → `prj/demo/001_1_phase.md`

### [X] Step 2: Update Internal Links in Renamed Files
- [X] **000_phase.md**: Updated `[[Phase 1.1 index]]` link from `phase_1_1.md` → `001_1_phase.md`
- [X] **001_1_phase.md**: No internal link updates needed (inherits_from: -)

### [X] Step 3: Update All Demo Markdown Files with Phase References
- [X] `prj/demo/R9-G-graph-to-py-ast.md` - `phase: phase_1_1` → `phase: 001_1_phase`, `[[phase_1_1]]` → `[[001_1_phase]]`
- [X] `prj/demo/R14-G-graph-localhost-view.md` - Same updates
- [X] `prj/demo/R7-G-graph-semaphore.md` - Same updates
- [X] `prj/demo/R1-G-graph.md` - Same updates
- [X] `prj/demo/004.1-requi-continuity-db-file-level-evidence.md` - Same
- [X] `prj/demo/006-requi-filespace-organized-for-prj_tool.md` - Same
- [X] `prj/demo/R12-G-graph-name-selection.md` - Same
- [X] `prj/demo/R13-G-graph-color-style.md` - Same
- [X] `prj/demo/R3-G-graph-load-list.md` - Same
- [X] `prj/demo/R10-G-py-from-ast.md` - Same
- [X] `prj/demo/005-requi-prj_tool-mvp-role.md` - Same
- [X] `prj/demo/R5-G-graph-export-compare.md` - Same
- [X] `prj/demo/R2-G-graph-db.md` - Same
- [X] `prj/demo/R15-G-graph-dot-localhost.md` - Same
- [X] `prj/demo/000-requi-checker-simulator-narration.md` - Same
- [X] `prj/demo/R11-G-graph-gviz.md` - Same
- [X] `prj/demo/003-requi-project-scope-structure-intended-use.md` - Same
- [X] `prj/demo/001-requi-markdown-docs.md` - Same

### [X] Step 4: Update Demo Example Files
- [X] Updated `phase_1_1` → `001_1_phase` in all demo markdown files (20+ files)

### [X] Step 5: Verify No Remaining Old References in .md Files
- [X] Confirmed: No `phase_1_1` references remain in `prj/demo/*.md` (except `phase_1_1_ok.md` test link file)
- [X] All links resolve correctly with new naming `001_1_phase`

### [X] Step 7: Additional Rename `001_1_phase` → `001_001_phase`
- [X] `prj/demo/001_1_phase.md` → `prj/demo/001_001_phase.md`
- [X] Updated all 20+ demo markdown files: `001_1_phase` → `001_001_phase` in `phase:` headers and `[[001_1_phase]]` links
- [X] Updated `000_phase.md` internal link from `[[001_1_phase]]` → `[[001_001_phase]]`
- [X] Updated remaining files: `004-requi-continuity-db-starter-guidance.md`, `007-requi-traceability.md`, `002-requi-phase-document-structure.md`, `R4-G-graph-tool-init.md`, `R8-G-graph-beam-filter.md`, `R6-G-graph-algo.md`

### [X] Step 8: Update Plan Markers
- [X] Mark all TODO items as completed in `prj/self_learn/plans/003-plan-change-demo-phase-references.md`

---

## Reference Summary (before rename)

### Demo Project Phase Files:
| File | Description |
|------|-------------|
| `prj/demo/phase_0.md` | PROJECT PHASE 0 - entry point, inherits from base |
| `prj/demo/phase_1_1.md` | PROJECT PHASE 1.1 - canonical index for demo requirements |

### Files referencing `phase_1_1` (before rename):
| File | Type of Reference |
|------|------------------|
| `prj/demo/phase_0.md` | `[[Phase 1.1 index]](phase_1_1.md)` (internal link) |
| `prj/demo/phase_1_1.md` | Top-level phase index, inherits from `-` |
| 20+ demo markdown files (`R*-G-*.md`, `00*.md`, `001-*.md`) | `phase: phase_1_1`, `[[phase_1_1]]` related phase references |

---

## New Naming Convention
| Old Name | New Name |
|----------|----------|
| `phase_0.md` | `000_phase.md` |
| `phase_1_1.md` | `001_1_phase.md` → `001_001_phase.md` (additional rename) |
| `[[Phase 1.1 index]]` | `[[001_1_phase]]` → `[[001_001_phase]]` (after additional rename) |
| `phase: phase_1_1` | `phase: 001_1_phase` → `phase: 001_001_phase` (after additional rename) |
| `[[phase_1_1]]` | `[[001_1_phase]]` → `[[001_001_phase]]` (after additional rename) |

---

**Plan saved to**: `prj/self_learn/plans/003-plan-change-demo-phase-references.md`

## Execution Summary
- ✅ Renamed `prj/demo/phase_0.md` → `prj/demo/000_phase.md`
- ✅ Renamed `prj/demo/phase_1_1.md` → `prj/demo/001_1_phase.md`
- ✅ Updated internal links in renamed files
- ✅ Updated 20+ demo markdown files with `phase: 001_1_phase` and `[[001_1_phase]]` references
- ✅ Verified: No remaining `phase_1_1` references in `prj/demo/*.md` (only `phase_1_1_ok.md` test link file)
- ✅ All phase links now use consistent `001_1_phase` naming