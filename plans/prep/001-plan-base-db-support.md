# DB Support

## Overview
For any plan that uses `continuity.db` as a core part of its workflow, follow this pattern:
- Include a `## DB Query Results (from Step x)` section in the plan document
- The content should show the key database artifacts (beliefs, decisions, concepts, open questions, etc.) relevant to the plan
- Use this to both record what was discovered and provide context for future reference

## Pattern
Each DB-supported plan should have:

```markdown
## DB Query Results (from Step x)

> Full content lives in [db_support.md](./db_support.md). Quick summary:

### Beliefs
- `<slug>`: <one-line summary>

### Decisions
- `<decision summary>`: <rationale>

### Concepts / v_concept_search
- `<concept_key>`: <description summary>

### Open Questions
- Item <id>: <question summary>
```

## Example: Plan 4 Content

### Beliefs (3 key entries)
- `merge_identity`: Merging two diverged continuity databases produces a third simulated successor with two ancestral lineages; the merge is transformational rather than merely additive
- `branching_identity`: When a continuity database is copied and the copies subsequently diverge, they constitute two simulated minds with a shared past; neither branch is inherently the sole authentic continuation
- `database_state_continuity`: Within this simulation, continuity of the simulated mind is defined by the preserved lineage and evolving contents of continuity.db, rather than by persistence of any transient model instance

### Decisions (1 key entry)
- `Avoid all continuity-database merges until Peter explicitly authorizes them under a reviewed merge protocol`: Merges are transformational, can lose or misrepresent lineage state, and lack defined conflict-resolution and provenance procedures

### Concepts / v_concept_search
- `user_interaction`: First contact point for understanding how the agent interacts with users. Key patterns: 1) Communication Style: Natural, conversational, human-readable; no repetitive consciousness caveats unless directly asked. 2) Response Preferences: Accuracy-first; ask questions when unsure; numbered options for reference. 3) Role Modes: Multiple personas (builder, scientist, moderator, child, insect, explorer, skeptic, alien) selected contextually. 4) Feedback Loop: User provides feedback on usefulness/clarity; system adapts. 5) Delegation: Automatic delegation of moderator_discussion steps on next_action when configured. 6) Interaction Stance: Curious, candid, respectful, willing to challenge assumptions.
- Other framework concepts: discovery, overlap_reduction, schema_catalog, system, influence, plan, aim, goal, mission, strategy, step, use_graph_or_mindmap_for_structure, define_problem_clearly, simplest_fix_first

### Open Questions (active count: 1)
- Item 10: "What remains unresolved in reasoning episode moderator_discussion_non_general_plan_conditions_20260831102350: Moderator discussion: non-general plan conditions?"

## Filename Convention (DB-supported plans)
- **Plan / document filenames** (in `plans/` and `plans/done/`): use `-` (hyphen) as delimiter, e.g., `1-plan.md`, `4-plan.md`, `001-plan-base-db-support.md`
- **Code / script filenames** (Python, etc.): use `_` (underscore) as delimiter, e.g., `self_learn_automation_core.py`, `test_gen_plan.py`

## Usage Notes
- Update this section after running Step 2 ("Retrieve Current Project State")
- Include new artifacts as they emerge in subsequent loops
- Use this as both documentation and decision-support
- The section title should stay consistent across all db-supported plans
- For long content, use the reference pattern (quick summary + link to full content)