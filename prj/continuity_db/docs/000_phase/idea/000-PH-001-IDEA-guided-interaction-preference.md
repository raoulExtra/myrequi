# Idea: Improve the Thinking of Our Thinking Engine

## Overview

This document captures the idea to improve how our thinking engine thinks — its reasoning, clarification, and decision-making processes — based on the guided interaction preference.

## Concept

| Field | Value |
|-------|-------|
| **concept_key** | `guided_interaction_preference` |
| **name** | Guided Interaction Preference |
| **description** | User prefers structured interactions: ask for missing information, present numbered options, and confirm before executing actions. |
| **status** | active |
| **confidence** | 0.95 |
| **glossary_term** | 1 |

## Idea Statement

Improve the thinking engine by making it:
- **Ask before assuming** — clarify missing information.
- **Present options** — offer numbered choices instead of open-ended leaps.
- **Confirm before acting** — especially for irreversible or high-stakes actions.
- **Structure the dialogue** — break complex tasks into steps with checkpoints.

## Implementation Notes

- Stored as a concept in `concepts` (concept_key=`guided_interaction_preference`, glossary_term=1).
- Stored as a memory fragment in `memory_fragments` (fragment_type=preference, factual_status=verified).
- Memory condition added to surface the preference when discussing guided clarification or confirmation.

## Next Steps

1. Test in real dialogues.
2. Monitor metrics: fewer clarification turns, better task completion.
3. Extend templates to other domains (coding, planning, brainstorming).

---

*Document ID:* `000-PH-001-Idea`  
*Category:* `idea`  
*Last Updated:* 2026-09-09
