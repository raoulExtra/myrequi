PROJECT PHASE 0
purpose: navigation entry point for the base project docs.
goal: point readers to the canonical base standards and phase indexes.
outcome: a simple index for the base project.

glossary (general):
- index
- canonical
- source of truth
- markdown file
- filespace
- requirement
- acceptance criteria
- test case
- 000-P-001-POL: Glossary Policy (DB: policy-001)
- 001-GLOS-001: Requirements Glossary (DB: glossary-001)

glossary for projects:

- stakeholders
- milestone
- release
- stakeholder (DB: term_key=stakeholder, Frame, defines who influences/experiences the change)
- stakeholder_need (DB: stakeholder_need)
- scope_boundary (DB: scope_boundary)
- constraint (DB: constraint)
- assumption (DB: assumption)
- open_question (DB: open_question)
- requirement (DB: requirement, Specify phase)
- acceptance_criterion (DB: acceptance_criterion)
- evidence (DB: evidence)
- scenario (DB: scenario)
- verification (DB: verification)
- validation (DB: validation)

stakeholders:
- product owner (PO)
- user
- operator

- [Glossary (rich terms with DB links)](docs/000_phase/001-GLOS-001-requirements_glossary.md)
navigation:
- [Phase 1](phase_1.md)
- [Phase 1.1](phase_1_1.md)
- [Requirement definition](001-requirement-definition.md)
- [Core Requirement](001-RC-requi_core.md)
- [Core Acceptance Criteria](001-AC-acc_crit_core.md)
- [Project file organization standard](002-requi-prj-file-organization-standard.md)
- [Python code requirement alignment](003-requi-python-code-requi-alignment.md)
- [db guidance](memory-and-filesystem-guidance.md)

default_version: V00.00.01

recommended_subdirs:
- docs/ — overview, usage, project explanation
- examples/ — sample outputs or mock content
- references/ — copied links to standards/specs if needed
- assets/ — images, diagrams, screenshots
- archive/ — old or superseded material
- decisions/ - project relevant decisions
- imple/<version>/ — implementation snapshots by version
- imple/<version>/test/ — tests for that implementation 
on tag: thinking_workspace
- plans - work_plan templates and executions

status: draft
