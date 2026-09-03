PROJECT PHASE 1.1
inherits_from: -
purpose: index the canonical demo requirements and
acceptance criteria.
goal: provide one place to navigate the demo project's
req/acc set without duplicating the spec.
outcome: a clean index for the demo requirements

standard:
- [Global file organization
  standard](../base/002-requi-prj-file-organization-standard.md)

requirements:
- [R0: Checker simulator narrates
  processing](000-requi-checker-simulator-narration.md)
- [R1: Clear demo markdown
  files](001-requi-markdown-docs.md)
- [R1-G: Graph with weighted nodes and edges](R1-G-graph.md)
- [R2-G: Graphs stored in SQLite with graph
  IDs](R2-G-graph-db.md)
- [R3-G: Load and list graphs from simple
  JSON](R3-G-graph-load-list.md)
- [R4-G: Graph tool initializes an empty SQLite graph
  database](R4-G-graph-tool-init.md)
- [R5-G: Export graphs and compare against a database
  graph](R5-G-graph-export-compare.md)
- [R6-G: Run an algorithm on a selected
  graph](R6-G-graph-algo.md)
- [R7-G: Graph semaphore for multi-process
  work](R7-G-graph-semaphore.md)
- [R8-G: Beam search with filtering](R8-G-graph-beam-filter.md)
- [R9-G: Convert a selected graph into a Python AST](R9-G-graph-to-py-ast.md)
- [R10-G: Provide a `py_from_ast.py` module for graph-to-Python-AST use](R10-G-py-from-ast.md)
- [R2: Standard phase document
  fields](002-requi-phase-document-structure.md)
- [R3: Project overview
  content](003-requi-project-scope-structure-intended-use.md)
- [R4: Database guidance in
  docs](004-requi-continuity-db-starter-guidance.md)
- [R4.1: File-level evidence for
  R4](004.1-requi-continuity-db-file-level-evidence.md)
- [R5: prj_tool is
  documented](005-requi-prj_tool-mvp-role.md)
- [R6: Filespace
  organization](006-requi-filespace-organized-for-prj_tool.md)
- [R7: Requirement traceability](007-requi-traceability.md)

acceptance_criteria:
- [R0 acceptance
  criteria](000-acc-crit-checker-simulator-narration.md)
- [R1 acceptance criteria](001-acc-crit-markdown-docs.md)
- [R1-G acceptance criteria](R1-G-graph-acc-crit.md)
- [R2-G acceptance criteria](R2-G-graph-db-acc-crit.md)
- [R3-G acceptance
  criteria](R3-G-graph-load-list-acc-crit.md)
- [R4-G acceptance
  criteria](R4-G-graph-tool-init-acc-crit.md)
- [R5-G acceptance
  criteria](R5-G-graph-export-compare-acc-crit.md)
- [R6-G acceptance criteria](R6-G-graph-algo-acc-crit.md)
- [R7-G acceptance
  criteria](R7-G-graph-semaphore-acc-crit.md)
- [R8-G acceptance criteria](R8-G-graph-beam-filter-acc-crit.md)
- [R2 acceptance
  criteria](002-acc-crit-phase-document-structure.md)
- [R3 acceptance
  criteria](003-acc-crit-project-scope-structure-intended-use.md)
- [R4 acceptance
  criteria](004-acc-crit-continuity-db-starter-guidance.md)
- [R4.1 acceptance
  criteria](004.1-acc-crit-continuity-db-file-level-evidence.md)
- [R5 acceptance
  criteria](005-acc-crit-prj_tool-mvp-role.md)
- [R6 acceptance
  criteria](006-acc-crit-filespace-organized-for-prj_tool.md)
- [R7 acceptance criteria](007-acc-crit-traceability.md)

status: draft
