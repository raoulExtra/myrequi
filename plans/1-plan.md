# Memory-Assisted Thinking Implementation Plan

- file: 1-plan.md
- kind: human_generated

## Name
Memory-Assisted Thinking: Implement core recall and multi-layer memory system

## Source
- upgrade_plan.md: Memory-Assisted Thinking design document

## Objective
Implement a memory-assisted thinking system that enables recall across episodic, semantic, procedural, and metacognitive memory layers, with versioned beliefs, convictions layer, conflict detection, and long-horizon continuity.

## Steps

### MVP (Next Turn Focus)
- [ ] Implement core recall API: `recall(query, layer=None, filters={})`
- [ ] Add episodic memory recall: fetch from `reasoning_episodes`, `journal`, `open_questions`
- [ ] Add semantic memory recall: fetch from `beliefs`, `syntheses`, `concepts`
- [ ] Rank results by recency and simple relevance
- [ ] Build compact working context from top matches
- [ ] Store reasoning episodes after each interaction
- [ ] Save open questions, decisions, and action items
- [ ] Attach basic confidence and source metadata

### v1 Implementation (Ongoing Work)
- [ ] Add multi-layer recall across all four memory types
- [ ] Rank by relevance, confidence, recency, and layer priority
- [ ] Version beliefs with update history in `belief_versions`
- [ ] Add explicit convictions layer for durable commitments
- [ ] Detect conflicts between old and new statements
- [ ] Separate raw evidence from derived synthesis
- [ ] Add reflection step after major tasks
- [ ] Link episodes, beliefs, convictions, projects, and open questions

### v2 Implementation (Future)
- [ ] Keep one current primary goal in `metacognitive_state.primary_goal`
- [ ] Keep one active plan per topic in `work_plans`
- [ ] Keep 3-7 actionable steps in `work_plan_steps`
- [ ] Use `open_questions` for blockers and unresolved dependencies
- [ ] Write `reasoning_episode` when goal is revised
- [ ] Tune recall by task type and intent
- [ ] Generate synthesis from accumulated evidence
- [ ] Monitor uncertainty, bias, and stale assumptions
- [ ] Support long-horizon continuity across sessions
- [ ] Make writeback adaptive to memory layer and task type

## Notes
- Start with MVP: implement recall across episodic and semantic memory
- Use `continuity.db` as the only core memory store
- Each step should be testable and auditable
- Success criteria: system recalls relevant past notes and writes back with traceable provenance

## Priority Order
1. `continuity.db` as the only core memory store
2. Recall API
3. Ranking and filtering
4. Working context builder
5. Writeback policy
6. Provenance and confidence
7. Reflection and conflict handling