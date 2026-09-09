# 000-P-005-RC-Learning-Domain-Separation

**ID:** 000-P-005-RC

**Category:** Core Requirement

**Title:** Learning Domain Separation

## Description
Learning must be clearly separated between project-specific learnings (stored in filesystem) and general continuity.db learnings, with independent export/import capabilities and clear ownership markers.

## Acceptance Criteria

### AC-005.1: Project Learning Storage
- Project-specific learnings are stored in `prj/self_learn/knowledge/` as markdown/JSON files
- General continuity.db learnings remain in the main database
- Each storage location has a clear ownership marker (project vs. system)

### AC-005.2: Ownership Markers
- Project knowledge files have `owner: self_learn` tag
- Each entry has `domain: project` or `domain: system` marker
- Cross-domain items use both markers appropriately

### AC-005.3: Trace ID Mapping
- Cross-referencing uses unique trace IDs
- Trace IDs are stored in `knowledge/trace_ids.json`
- IDs link project files to continuity.db episode IDs

### AC-005.4: Independent Export/Import
- Project knowledge can be exported as a single archive
- Import does not require continuity.db access
- Export/import preserves all metadata and formatting

## Status
draft

## Related
- Phase 0: Core infrastructure requirements
