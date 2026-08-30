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

- TODO: add multi-layer recall across episodic, semantic, procedural, and metacognitive memory
- TODO: rank by relevance, confidence, recency, and layer priority
- TODO: version beliefs with update history
- TODO: detect conflicts between old and new statements
- TODO: separate raw evidence from derived synthesis
- TODO: add a reflection step after major tasks
- TODO: link episodes, beliefs, projects, and open questions

**Success criteria**
- Contradictions are visible
- Beliefs can evolve without losing history
- The model can explain why it believes something

## v2
Goal: make memory a real thinking partner.

- TODO: add persistent planning and goal tracking
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
1. Recall API
2. Ranking and filtering
3. Working context builder
4. Writeback policy
5. Provenance and confidence
6. Reflection and conflict handling
