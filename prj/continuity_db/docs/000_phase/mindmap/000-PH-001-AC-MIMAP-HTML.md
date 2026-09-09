# 000-PH-001-AC

**ID:** 000-PH-001-AC

**Category:** Acceptance Criteria

**Title:** Acceptance Criteria for MIMAP HTML Export

**Parent Requirement:** `000-PH-001-RC-MIMAP-HTML.md`

## AC-001.1: MIMAP Input Accepted
- The command accepts a `.md` source file that contains a MIMAP/mindmap structure.
- The command supports `--mimap` as the explicit mode selector.

## AC-001.2: HTML Output Created
- Running the command creates an `.html` file.
- The output file is non-empty.
- The output file can be opened in a browser.

## AC-001.3: Structure Preserved
- Top-level mindmap branches remain visibly distinct.
- Nested bullet hierarchy is preserved in the HTML.
- The central/root topic remains identifiable.

## AC-001.4: Predictable Naming and Location
- The generated HTML filename is derived from the input filename.
- For inputs under `prj/<prj_name>/docs/`, the output is written under `prj/<prj_name>/out/` while keeping `docs/` in the path.
- Example: `prj/continuity_db/docs/000_phase/000-PH-001-MIMAP-thinking.md` produces `prj/continuity_db/out/docs/000_phase/000-PH-001-MIMAP-thinking.html`, unless an explicit output path is provided.

## AC-001.5: Safe Filesystem Behavior
- The command does not modify the source markdown file.
- Existing output files are not overwritten unless overwrite behavior is explicit or documented.
- Errors are reported clearly when the input file does not exist or is not readable.

## AC-001.6: Documentation Example
- Project documentation includes at least one example using:
  - `--mimap`
  - `prj/continuity_db/docs/000_phase/000-PH-001-MIMAP-thinking.md`

## AC-001.7: Morphology Links Rendered in Order
- A token like `ment(al)` renders `ment` as text and `al` as a link after it.
- A token like `(in)clude(s)` renders `in` as a link first, `clude` as text second, and `s` as a link last.
- Prefix and suffix links preserve source order and do not hide the stem.

## AC-001.8: MIMAP Cross-Links Rendered Behind Enriched Terms
- When a rendered term matches another standalone sibling MIMAP source, the HTML appends a concept/MIMAP link after the complete rendered word.
- Morphology links remain inside the enriched word before the concept/MIMAP link.
- Example: `(re)ason(ing)` keeps its morphology links and then links to the reasoning MIMAP HTML when `000-PH-002-MIMAP-reasoning.md` exists.
- RC/SR/AC support files are not treated as standalone MIMAP cross-link targets.

## AC-001.9: All-MIMAP Regeneration
- The command supports `--all-mimaps <folder>`.
- Running all-MIMAP mode regenerates all standalone MIMAP HTML outputs in the folder.
- Existing related MIMAP HTML files gain links to newly added MIMAP terms after regeneration.
- All-MIMAP mode excludes RC/SR/AC files whose names contain `MIMAP`.

## Dense Referencable Checklist

Before accepting the implementation, verify:

1. **Mode explicit** – `--mimap` selects MIMAP/mindmap export behavior.
2. **Input traceable** – the source markdown path is visible and reproducible.
3. **Output present** – an HTML file is generated on the filesystem.
4. **Output routed** – project-relative input paths, including `docs/`, are preserved below `prj/<prj_name>/out/`.
5. **Hierarchy preserved** – nested MIMAP structure remains readable.
6. **Morphology linked** – parenthesized prefixes/suffixes become links in source order while stems remain visible.
7. **MIMAP cross-linked** – matching sibling MIMAP terms get a concept/MIMAP link after the enriched word.
8. **All regenerated** – `--all-mimaps` refreshes all standalone MIMAP HTML files and excludes RC/SR/AC support files.
9. **Source safe** – the markdown source file is not changed.
10. **Error clear** – missing or invalid input produces a useful error message.

## Related

- `000-PH-001-RC-MIMAP-HTML.md`
- `000-PH-001-SR-MIMAP-HTML.md`
- `000-PH-001.001-SR-docs-to-out-path-preservation.md`
- `000-PH-001.002-SR-morphology-link-ordering.md`
- `000-PH-001.003-SR-MIMAP-cross-links.md`
- `000-PH-001.004-SR-all-MIMAP-regeneration.md`
- `../000-PH-001-MIMAP-thinking.md`
