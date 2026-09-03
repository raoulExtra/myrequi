'''yaml
title: R10-G-py-from-ast-acc-crit
requirement_id: R10-G
source_requirement: R10-G-py-from-ast.md
'''

# Acceptance criteria for R10-G

## Requirement
- [R10-G requirement](R10-G-py-from-ast.md)

## Verification ideas
- The demo project provides `prj/demo/imple/V00.00.01/py_from_ast.py`.
- The demo graph tool exposes a `--py` argument for invoking the module on the selected graph.
- When `--py` is used, the default output file is `compare.py`.
- The `compare.py` file contains generated Python source for the selected graph.
- The module accepts the graph-syntax JSON form used by the demo.
- The graph-syntax AST examples use explicit edge `order` values.
- The module traverses the graph structure and constructs Python `ast` nodes.
- The module can be used by graph-oriented code without needing manual AST assembly at every call site.
- The examples directory contains graph-syntax JSON examples that can be transformed by the module.
- The converter respects explicit edge order when building ordered Python AST fields.
- A reviewer can confirm the module is a reusable conversion layer, not a one-off script.
