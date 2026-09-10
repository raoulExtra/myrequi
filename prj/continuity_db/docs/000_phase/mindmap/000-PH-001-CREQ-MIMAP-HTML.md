---
id: 000-PH-001-CREQ
category: Core Requirement
title: Core Requirement for MIMAP HTML Export
parent: ../000-PH-001-MIMAP-thinking.md
artifact_role: canonical
---

## Purpose

Clarify the requirements for a command that converts `prj/<prj>/docs/000_phase/*.md` MIMAP/mindmap markdown files into standalone `.html` files with preserved hierarchy, morphology links, MIMAP cross-links, and safe filesystem behavior.

## Scope

- Input: `.md` source with MIMAP/mindmap structure.
- Output: `.html` with matching name under `prj/<prj>/out/` (preserving `docs/` in path unless override given).
- Mode: `--mimap` selects MIMAP export.
- All-MIMAP mode (`--all-mimaps <folder>`): regenerates standalone MIMAP outputs; excludes CREQ/SREQ/AC support files.

## Related

- `000-PH-001-AC-MIMAP-HTML.md`
- `000-PH-001-SREQ-MIMAP-HTML.md`
- `../000-PH-001-MIMAP-thinking.md`
