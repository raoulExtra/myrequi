# 000-P-005-AC-Learning-Domain-Separation

**ID:** 000-P-005-AC

**Related To:** 000-P-005-RC-Learning-Domain-Separation

**Category:** Acceptance Criteria

## Test Scenarios

### Test SC-005.1: Project Learning Storage
**Given** project knowledge should be created
**When** knowledge is stored
**Then** it appears in `prj/self_learn/knowledge/`

### Test SC-005.2: System Learning Storage
**Given** system knowledge should be created
**When** knowledge is stored
**Then** it appears in continuity.db tables

### Test SC-005.3: Ownership Markers
**Given** knowledge files exist
**When** ownership tags are checked
**Then** files have appropriate owner/domain markers

### Test SC-005.4: Independent Export/Import
**Given** project knowledge exists
**When** export is initiated
**Then** a standalone archive is created

## Validation Commands
```bash
ls prj/self_learn/knowledge/README.md
```

## Status
draft
