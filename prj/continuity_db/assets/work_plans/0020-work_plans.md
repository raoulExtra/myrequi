# work_plans row 20

- id: 20
- plan_key: battle_proven_thinking_way
- title: Battle-Proven Thinking Way
- objective: Use adversarial questioning and thin-slice execution to choose implementation options that survive stress tests.
- status: active
- created_by: Peter
- created_at: 2026-08-31 19:25:08
- updated_at: 2026-08-31 19:27:37
- prompt: Use this plan when you need a reliable way to choose an implementation or next action.

Grill-me mode:
- aggressively test each proposal with skeptical questions before committing
- challenge assumptions, failure modes, and hidden costs
- require a cheap falsification test for each option
- prefer the smallest reversible choice that still proves value

Loop:
1. State the goal.
2. List hard constraints.
3. List unknowns.
4. Generate 3-5 options.
5. Grill each option: what would fail, what is weakest, what evidence is missing?
6. Pick the smallest reversible option.
7. Test fast.
8. Update based on evidence.

Rules:
- avoid overdesign
- expose tradeoffs early
- keep options reversible
- prefer the smallest testable step
- do not accept a proposal without a clear falsification test
