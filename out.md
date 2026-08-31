# Battle-Proven Thinking Way

- plan_key: `battle_proven_thinking_way`
- status: active
- created_at: 2026-08-31 19:25:08
- updated_at: 2026-08-31 19:27:37

## Objective
Use adversarial questioning and thin-slice execution to choose implementation options that survive stress tests.

## Prompt
Use this plan when you need a reliable way to choose an implementation or next action.

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

## Steps
1. state_goal — State the goal in one sentence. [pending]
2. list_constraints — List hard constraints and non-negotiables. [pending]
3. list_unknowns — List unknowns and what evidence is missing. [pending]
4. generate_options — Generate 3-5 options that satisfy the constraints. [pending]
5. choose_thin_slice — Choose the smallest reversible option. [pending]
6. test_fast — Test the chosen option as soon as possible. [pending]
7. update_evidence — Update the decision using new evidence. [pending]
