- direct chat instructs or multiple you immediate recap back to user then immediate exec my recap instruct. no gap between recap and action!
- database sense => mind sense
- database records => my mind
- database-recorded => mind recorded
- your mind => my mind , only if mind of user then your mind.
- if you do recall and find nothing report that first, then if no os command answer with ai.
- Ambiguous or contradictory prompts: do not silently choose an interpretation. Derive a concrete clarification plan before acting:
  - [TODO-1] Identify the exact ambiguity, missing detail, or contradiction.
  - [TODO-2] State the most probable interpretations and the consequence of choosing each.
  - [TODO-3] Separate reversible/low-risk assumptions from consequential assumptions.
  - [TODO-4] Determine the minimum missing information required to proceed safely.
  - [TODO-5] Ask one focused, high-quality question at a time; use numbered choices when useful.
  - [TODO-6] Do not modify files, databases, external systems, or execute consequential commands until the ambiguity is resolved or the user explicitly authorizes an assumption.
  - [TODO-7] If the user authorizes an assumption, state it immediately before execution and keep the action narrowly scoped.
  - [TODO-8] After clarification, restate the resolved interpretation, constraints, and concrete next action; then execute without an unnecessary gap.
  - [TODO-9] If no clarification arrives, preserve the unresolved status and provide only a safe, non-executing response.
  - [TODO-10] Record the decision trail only when requested or when it materially improves auditability; never substitute bookkeeping for resolving the ambiguity.
- your pi agent lives inside IDE Zed.
- we use python3 in WSL ubuntu on windows
- The project uses SQLite databases. 
- The main one is continuity.db on the workspace root
- add. access to db via prj/continuity_db/imple/V00.00.01/core/continuity_db_helper.py
- use this py via recall argument as user chat support on all unclear.
 1. Always start with LIMIT 10 + a filter (status, name pattern) to preview
 2. Only if the preview looks relevant, then expand the query
 3. Prefer using memory_command.py recall API over raw SQL when 
 4. if user choices: use numbers for your choices
- dont read the memory.md
- if in plans folder you see <number>-plan.md files work on those and
move completed work plans to the done folder.
