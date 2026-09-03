'''yaml
title: R10-G-py-from-ast
requirement_id: R10-G
phase: phase_1_1
for_version: default_version
'''

# R10-G: Provide a `py_from_ast.py` module for graph-to-Python-AST use

The demo project SHALL provide `prj/demo/imple/V00.00.01/py_from_ast.py` as a reusable module for graph-based Python AST generation. The module SHALL accept the graph-syntax JSON form used by the demo and SHALL convert it into Python `ast` nodes by traversal plus node construction. The graph syntax for AST generation SHALL use explicit edge `order` values for ordered child lists. The demo graph tool SHALL expose a `--py` argument that calls this module for the selected graph, and when `--py` is used the default output file SHALL be `compare.py` containing generated Python source.

## Traceability
- stakeholder need: the demo should have a reusable module that graph-oriented code can call to turn graph syntax into Python AST
- related phase: [phase_1_1](phase_1_1.md)

## Acceptance criteria
- [Acceptance criteria](R10-G-py-from-ast-acc-crit.md)
