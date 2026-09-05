# Rust graph schema

This tool consumes a graph JSON format and renders Rust source.

## Schema focus

The richer Rust graph schema is meant to represent real Rust source, including:

- modules and files
- `use` items
- `struct`, `enum`, `trait`, `impl`
- functions, params, generics, return types, where clauses
- `let`, `if`, `match`, `while`, `for`, `loop`
- expressions, patterns, types, and comments/doc comments

## Files

- `rust_graph_schema.json` — machine-readable schema reference
- `src/main.rs` — Rust renderer
- `src/main.rs.graph.json` — source-structure graph for this renderer
- `src/main.rs.graph.detailed.json` — finer-grained graph with branch and subsection nodes

## Examples

- `../../examples/040-rust-ast-func-graph.json`
- `../../examples/041-rust-ast-struct-impl-graph.json`
