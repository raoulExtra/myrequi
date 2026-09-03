'''yaml
title: R9-G-graph-to-py-ast-acc-crit
requirement_id: R9-G
source_requirement: R9-G-graph-to-py-ast.md
'''

# Acceptance criteria for R9-G

## Requirement
- [R9-G requirement](R9-G-graph-to-py-ast.md)

## Verification ideas
- The demo project supports a graph-to-Python-AST conversion mode.
- The selected graph can be chosen with `--id` or the equivalent graph selector.
- The conversion input uses a special JSON form intended for AST generation.
- The special JSON form includes explicit node types, ordered child lists, and fields that map cleanly to Python `ast` nodes.
- The conversion traverses the graph and constructs Python AST nodes.
- The result is a Python `ast` tree or a clearly equivalent AST representation.
- The examples directory contains at least three JSON examples for the AST form and at least three graph-syntax counterpart JSON examples for the same structures.
- A reviewer can confirm the conversion is not just a text export, but a traversal plus node-construction step.
