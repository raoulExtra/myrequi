# decisions row 8

- id: 8
- decision: Backfill missing metacognitive_state_history rows when a current metacognitive_state row lacks its matching history version.
- rationale_summary: Consistency audits should repair missing history rows so versioned metacognitive state remains complete and auditable.
- alternatives: Ignore missing history rows; reconstruct later only if needed; delete the current state instead.
- uncertainty: Future migrations may need more explicit repair rules for other tables.
- status: active
- created_at: 2026-08-28 20:09:03
- origin_reasoning_episode_id: None
