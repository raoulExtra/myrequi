# Upgrade Plan: Memory-Assisted Thinking

> TODO: flesh out implementation details and owners.

## Core recall interface

- `recall(query, layer=None, filters={})`
- Layers:
  - **episodic**: past interactions, reasoning episodes, journal entries
  - **semantic**: beliefs, syntheses, facts, concepts
  - **procedural**: workflows, rules, how-to notes
  - **metacognitive**: confidence, uncertainty, conflicts, limits
- Output should include:
  - match text
  - source record
  - layer
  - confidence
  - timestamp
  - provenance

## Observed data flow in the current DB

1. **Incoming task / question**
   - starts in the conversation layer and is framed by `metacognitive_state.current_focus` or `journal`
2. **Recall**
   - fetch from `beliefs`, `belief_versions`, `syntheses`, `reasoning_episodes`, `open_questions`, and `metacognitive_state`
3. **Working packet**
   - compress matches into a temporary context: active claims, relevant evidence, conflicts, uncertainties, next actions
4. **Reasoning output**
   - produce a decision, answer, or next step
5. **Writeback**
   - persist updated beliefs, new synthesis, episode record, open questions, and provenance links
6. **Reflection / validation**
   - update `metacognitive_state`, `synthesis_conflicts`, and history tables when uncertainty or contradiction appears

## Table-by-table mapping

### Episodic memory
- `reasoning_episodes`: durable record of the reasoning result
- `reasoning_episode_inputs`: links an episode to the evidence and questions that grounded it
- `journal`: short conversational or operational notes
- `open_questions`: unresolved, deferred, or resolved questions
- `work_plans` / `work_plan_steps`: active or completed work over time

### Semantic memory
- `beliefs` / `belief_versions`: versioned claims and their history
- `convictions` / `conviction_versions` / `conviction_inputs`: durable commitments and working judgments with explicit provenance
- `syntheses` / `synthesis_inputs`: derived conclusions from multiple sources
- `synthesis_conflicts`: explicit warnings when a synthesis needs review
- `concepts`: canonical named concepts used in reasoning
- `object_metadata` / `object_provenance` / `provenance_catalog`: object-level provenance and review state

### Metacognitive memory
- `metacognitive_state`: current self-model, goals, focus, and epistemic posture
- `metacognitive_state_history`: version history of those states
- `storage_policy_versions`: what the system is allowed to store
- `storage_quality_reviews`: whether stored items are useful, clear, and safe
- `recording_policy`: when to record new memory
- `continuity_requirement_validation`: quality checks on the continuity layer itself

### Procedural memory
- `tool_routes`: named tool patterns and invocation templates
- `control_command_routes`: command hooks and enabled/disabled control actions
- `work_plans` / `work_plan_steps`: repeatable process structure
- `research_jobs` / `research_sources`: reusable evidence-gathering workflow

### Not in scope for core recall
- `thinker/thinker.db`: concept seed store and structured concept notes; useful only as auxiliary material
- `chat.db`: not part of the core memory system

## MVP
Goal: make memory useful in the next turn.

- TODO: implement recall across episodic and semantic memory
- TODO: rank results by recency and simple relevance
- TODO: build a compact working context from top matches
- TODO: store reasoning episodes after each interaction
- TODO: save open questions, decisions, and action items
- TODO: attach basic confidence and source metadata

**Success criteria**
- The system can recall relevant past notes
- It can answer using prior context instead of starting over
- New conclusions are written back with traceable provenance

## v1
Goal: make memory reliable for ongoing work.

1. TODO: add multi-layer recall across episodic, semantic, procedural, and metacognitive memory
   - expose one recall path that can return layered packets
   - keep `continuity.db` as the only core memory store

2. TODO: rank by relevance, confidence, recency, and layer priority
   - prefer strong exact matches
   - keep weaker matches available but lower

3. TODO: version beliefs with update history
   - preserve prior belief statements
   - keep current belief rows and append-only history in sync

4. TODO: add an explicit convictions layer for durable commitments
   - keep convictions distinct from ordinary beliefs
   - require explicit provenance and version history
   - use convictions to guide action and judgment

5. TODO: detect conflicts between old and new statements
6. TODO: separate raw evidence from derived synthesis
7. TODO: add a reflection step after major tasks
8. TODO: link episodes, beliefs, convictions, projects, and open questions

**Success criteria**
- Contradictions are visible
- Beliefs can evolve without losing history
- The model can explain why it believes something

## v2
Goal: make memory a real thinking partner.

### Lightweight persistent planning and goal tracking
- TODO: keep one current primary goal in `metacognitive_state.primary_goal`
- TODO: keep one active plan per topic in `work_plans`
- TODO: keep 3–7 actionable steps in `work_plan_steps`
- TODO: use `open_questions` for blockers and unresolved dependencies
- TODO: write a short `journal` note when a step completes or the goal changes
- TODO: write a `reasoning_episode` when the goal is revised or a plan is replaced

### Broader v2 work
- TODO: tune recall by task type and intent
- TODO: generate synthesis from accumulated evidence
- TODO: monitor uncertainty, bias, and stale assumptions
- TODO: support long-horizon continuity across sessions and branches
- TODO: make writeback adaptive to memory layer and task type

**Success criteria**
- The system maintains coherent long-term reasoning
- It can reflect on its own limits
- It improves with accumulated experience without collapsing into noise

## Priority order
1. `continuity.db` as the only core memory store
2. Recall API
3. Ranking and filtering
4. Working context builder
5. Writeback policy
6. Provenance and confidence
7. Reflection and conflict handling
