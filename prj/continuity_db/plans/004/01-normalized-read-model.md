# Part 01: Normalized read model

1. Add a failing test for one normalized semantic projection.
2. Implement a view such as `v_semantic_records` with:
   `semantic_type`, `semantic_key`, `statement`, `confidence`, `status`, and
   `source_table`.
3. Add source-specific fields only when they do not blur the canonical role.
4. Update `v_core_model` to describe ownership and projection layers.
5. Verify the view is read-only and deterministic.
