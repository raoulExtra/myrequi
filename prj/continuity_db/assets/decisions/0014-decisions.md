# decisions row 14

- id: 14
- decision: Represent trust as an explicit concept in the DB, not merely as implicit belief or metacognitive state.
- rationale_summary: Trust is a cross-cutting abstraction that affects evidence weighting, source reliability, and reasoning transparency. A concept gives it a stable home without overloading state.
- alternatives: Store trust only as a belief; store trust only as a state; keep trust implicit.
- uncertainty: The exact concept boundaries and links to evidence scoring may need refinement later.
- status: active
- created_at: 2026-08-31 10:30:24
- origin_reasoning_episode_id: 24
