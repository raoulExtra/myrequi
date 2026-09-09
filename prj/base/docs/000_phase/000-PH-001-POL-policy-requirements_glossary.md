# 000-P-001-POL

**ID:** 000-P-001-POL

**Category:** Policy

**Title:** Glossary Policy for Requirements and Projects

## Description
Defines the governing policy for all glossaries across the project. Ensures terms are unique, consistently defined, traceable, and testable. Establishes conventions for glossary files, naming, cross-referencing, and lifecycle management.

## Scope
Applies to all glossary artifacts, including:
- General project glossaries (base terms)
- Phase-specific glossaries (Frame, Elicit, Specify, Validate)
- Domain glossaries (requirements, acceptance criteria, etc.)
- Glossary files created in `prj/base/docs/000_phase/` and subfolders

## Policy Rules

### P-001: Term Uniqueness
Every term appears exactly once across all project documentation. Duplicate terms are forbidden in any requirement, acceptance criterion, or glossary.

### P-002: Concise Definition
Each term has a concise, unambiguous definition. Definitions use simple, specific language without vague qualifiers.

### P-003: Traceability
Every term is traceable back to a project, goal, phase, stakeholder need, or higher-level requirement. Links are explicit and verifiable.

### P-004: Testability
Each term has an associated check or test that can verify correct usage. Testability is assessed via the Dense Referencable Checklist.

### P-005: Naming Convention
Glossary filenames follow the convention: `###-<category>-###-<type>`. Categories include `POL` (Policy), `RC` (Core Requirement), `GLOS` (Glossary), `TERM` (Term). The first `###` maps to the phase. Example: `000-P-001-POL-policy-requirements_glossary`.

### P-006: Glossary Reuse
Glossaries can be connected to a larger set via `connected:` <glossary_list>. Cross-references must be explicit and maintained.

### P-007: Source of Truth
The canonical source of truth for glossary terms is the `continuity.db` database, specifically the `requirements_glossary_terms` table. All terms are enriched with phase, definition, why-it-matters, elegant prompt, example, anti-pattern, source URL, and confidence score.

### P-008: Policy vs Glossary Separation
- **Policy files** (`000-P-...`): Define rules, conventions, and acceptance criteria. No term definitions.
- **Glossary files** (`001-GLOS-...`): Contain actual term definitions and enriched content.
- **Phase files** (`000_phase.md`): Reference both policy and glossary files for navigation.

### P-009: Version Control
All glossary and policy files follow `V00.00.01` initial draft convention. Version bumps occur on structural changes (major), content additions (minor), or typo fixes (patch).

## Dense Referencable Checklist

Before accepting any term or policy change, verify:

1. **Unique** – the term appears nowhere else in the project glossary.
2. **Defined** – a concise, unambiguous definition is present.
3. **Traceable** – the term links back to a goal, phase, or higher-level requirement.
4. **Testable** – there exists a test or check that can confirm correct usage.
5. **Consistent** – the term follows naming conventions (e.g., `POL-`, `RC-`, `GLOS-` prefixes).
6. **Sourced** – the term references its source in `continuity.db` or an external standard.
7. **Cross-referenced** – the term is linked from `000_phase.md` navigation.

## Version History

- `V00.00.01` — Initial glossary policy draft.

## Related

- [Glossary: Requirements](001-GLOS-001-requirements_glossary.md)
- [Core Requirement Glossary](000-P-001-RC-Glossary.md)
- [Phase 0 Navigation](../../../../000_phase.md)
