# decisions row 13

- id: 13
- decision: Use automatic conditional recall for non-general plans, but keep the general-plan heuristic conservative and allow manual override when a plan is intentionally broad.
- rationale_summary: The DB now has evidence that non-general plans benefit from scoped recall. Over-triggering is worse than under-triggering, so the heuristic should avoid classifying a plan as general unless its title/objective clearly indicate a broad baseline/system role.
- alternatives: Make every plan conditional by default; make the heuristic aggressive; require manual condition entry for all plans.
- uncertainty: Some broad plans may still be misclassified if they use specific wording in their title.
- status: active
- created_at: 2026-08-31 10:23:50
- origin_reasoning_episode_id: 23
