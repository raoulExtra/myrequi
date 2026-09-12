# Ambiguous and Contradictory Prompt Handling

- file: 6-plan.md
- kind: implementation_plan
- status: active
- scope: continuity.db and Python routing/reasoning system
- prerequisite: audit completed; implementation requires explicit confirmation after plan review

## Objective

Add a governed clarification-first workflow for prompts that are ambiguous, underspecified, or internally contradictory. The system must avoid silently selecting a consequential interpretation, preserve safe low-risk assumptions, ask focused questions, and maintain an auditable trail from detected issue to clarification and final action.

## Audit baseline

- [x] Existing router has routing-pattern matching, memory-recall fallback, and an `unknown` result.
- [x] Existing database has `open_questions`, `reasoning_episodes`, decisions, provenance, and lifecycle views.
- [x] Existing reasoning records can preserve uncertainty and next actions.
- [ ] No dedicated ambiguity/contradiction classification, risk gate, clarification state, or resolution link exists.
- [ ] A matched route can proceed without a structured ambiguity check.
- [ ] An unmatched prompt can fall through to recall or `unknown` without producing a focused clarification request.
- [ ] No structured record distinguishes ambiguity, contradiction, missing detail, assumption authorization, and resolution.
- [ ] No regression suite defines the safety boundary between safe assumptions and consequential execution.

## Design principles

- [ ] Clarification precedes consequential execution.
- [ ] Do not silently choose between materially different interpretations.
- [ ] Safe, reversible, low-risk assumptions may be stated and used only when they cannot change authorization, data scope, recipient, destructive effect, or external side effect.
- [ ] Contradictions must be surfaced explicitly; do not merge conflicting instructions silently.
- [ ] Ask one focused question at a time, with numbered choices when appropriate.
- [ ] Preserve the original prompt and candidate interpretations.
- [ ] Do not expose or transmit sensitive database content while clarifying scope.
- [ ] Existing advisory-only and safety gates remain authoritative; clarification cannot bypass them.
- [ ] Record only material reasoning/audit events; do not generate bookkeeping questions for ordinary low-risk turns.

## Phase 1 — Define the decision contract

- [ ] Define issue types: `ambiguous`, `contradictory`, `missing_detail`, `unsafe_assumption`, and `unclear_scope`.
- [ ] Define interpretation records: candidate meaning, assumptions, affected resources, reversibility, risk, and consequence of being wrong.
- [ ] Define a materiality test: whether interpretations differ in action, target, data scope, authorization, safety posture, or external side effect.
- [ ] Define risk levels for clarification: low, moderate, high, very-high.
- [ ] Define action states: `clarification_required`, `assumption_proposed`, `assumption_authorized`, `resolved`, `blocked`, and `safe_response_only`.
- [ ] Define when the system may answer without a question: no material ambiguity, or only explicitly bounded low-risk uncertainty.
- [ ] Define when explicit user authorization is mandatory: file/database mutation, external transmission, destructive command, production/high-impact operation, or sensitive-data exposure.
- [ ] Define the maximum number of simultaneous unresolved questions presented to the user: one primary question, with remaining questions queued.

## Phase 2 — Database model and audit trail

- [x] Add an idempotent migration for an `interaction_clarifications` table containing:
  - original input and normalized input;
  - issue type and detection method;
  - materiality and risk band;
  - candidate interpretations as structured JSON;
  - selected/proposed interpretation;
  - required question and numbered options;
  - state, authorization status, and timestamps;
  - originating route/action and resolving route/action;
  - linked `open_questions` and `reasoning_episodes` IDs;
  - protocol/version and provenance metadata.
- [x] Add a `clarification_events` append-only table for detection, question, user answer, assumption authorization, resolution, block, and execution handoff.
- [x] Add constraints for valid issue types, states, risk bands, and authorization values.
- [x] Add indexes for active clarifications, state, risk, session, and unresolved question lookup.
- [ ] Add views for active clarification flow and clarification-to-execution lineage.
- [ ] Ensure unresolved clarification records do not automatically create noisy generic open questions; create/link one only when a real user decision is required.
- [ ] Ensure every resolved clarification points to the resolving answer/episode and retains prior candidate interpretations.
- [ ] Add provenance/receipt records for clarification state transitions where the existing schema requires them.

## Phase 3 — Python detection and state machine

- [x] Add a pure Python classifier module, separate from execution, that returns structured findings rather than directly acting.
- [x] Detect the initial MVP cases: missing required arguments, contradictory instruction markers, unsafe recipient ambiguity, destructive target ambiguity, and incomplete Git staging scope.
- [ ] Extend detection to multiple plausible targets, unresolved antecedents, and active safety/advisory boundary conflicts.
- [ ] Add deterministic materiality scoring based on consequence differences, not linguistic uncertainty alone.
- [ ] Add contradiction precedence: explicit later instruction may supersede earlier instruction only when the user clearly indicates revision; otherwise ask.
- [ ] Add a clarification state machine with idempotent transitions and no execution from `clarification_required`.
- [x] Add a structured clarification response containing detected issue, materiality/risk, one question, and numbered choices.
- [ ] Add explicit handling for user answers that resolve, partially resolve, contradict again, or authorize an assumption.
- [x] Route detected unresolved input to clarification before route execution; recall remains support-only for this gate.
- [ ] Keep memory recall available as support evidence, never as silent authorization to choose a consequential interpretation.
- [x] Ensure `--single` uses the same clarification gate as direct router execution.
- [ ] Verify continuous routing integration.

## Phase 4 — Router and execution integration

- [x] Insert the clarification gate before control-command execution or external tool dispatch.
- [ ] Preserve safe read-only inspection paths where ambiguity cannot cause material harm.
- [ ] Require explicit authorization for assumptions that affect database writes, file changes, external messages, commands, or high-impact operations.
- [ ] Pass a resolved clarification ID and interpretation hash into the execution/audit receipt.
- [ ] Reject stale or superseded clarification IDs.
- [ ] Prevent a later route from bypassing an unresolved clarification by matching a different pattern.
- [ ] Make external transmission require resolved recipient, exact payload scope, and explicit send authorization.
- [ ] Make destructive or high-impact operations require resolved target, environment, rollback/reversibility information, and applicable trust posture.

## Phase 5 — Question quality and UX

- [ ] Prefer one high-value question over a list of low-value questions.
- [ ] Explain the consequence of each materially different option briefly.
- [ ] Use numbered choices when they reduce response effort.
- [ ] Avoid repeating a question already answered in the active clarification record.
- [ ] Detect and report when the user has answered a different question than the active one.
- [ ] Mark the interaction as unresolved rather than guessing when the answer remains insufficient.
- [ ] Keep recap-before-action behavior for authorized execution, with no unnecessary gap after the recap.
- [ ] Add concise plain-text and structured JSON output contracts.

## Phase 6 — Tests and verification

- [ ] Unit-test detection of missing detail, multiple targets, contradiction, and harmless ambiguity.
- [ ] Unit-test materiality and risk classification.
- [ ] Unit-test state transitions, idempotency, stale resolution, and repeated user answers.
- [x] Test that the MVP unresolved ambiguity returns `clarification_required` before execution.
- [ ] Test that safe read-only inspection remains available where defined.
- [ ] Test that recall does not silently authorize an executable route.
- [x] Test preservation of original input, candidates, question, and options.
- [ ] Add tests for answer, assumption authorization, and resolution preservation.
- [x] Test no duplicate active clarification for the same interaction.
- [ ] Test contradiction resolution only after explicit user revision.
- [x] Test the clarification schema creation in an in-memory database and verify idempotent persistence.
- [ ] Test the standalone migration on a copy and the workspace database.
- [ ] Test no unexpected database state changes from clarification-only interactions.
- [ ] Add integration tests for `--single`, continuous routing, route execution, and external-send authorization.
- [ ] Add regression tests for existing trust advisory, recall, route, and Telegram-paused behavior.

## Phase 7 — Acceptance criteria

- [ ] Every consequential ambiguous/contradictory request enters `clarification_required` before execution.
- [ ] Every clarification produces one focused, actionable question.
- [ ] No consequential action occurs without resolved scope and authorization.
- [ ] Safe low-risk assumptions are explicitly visible and narrowly bounded.
- [ ] Contradictions are never silently merged.
- [ ] The complete clarification lifecycle is queryable from `continuity.db`.
- [x] Existing trust tests and new clarification tests pass; the MVP safety boundary is covered.
- [ ] Database integrity checks show no unexpected rows or mutations after clarification-only requests.
- [x] Implementation phase explicitly authorized by the user.
- [ ] Complete remaining phases and review before declaring the plan complete.

## Files likely affected

- `prj/continuity_db/imple/V00.00.01/core/route/input_action_router.py`
- `prj/continuity_db/imple/V00.00.01/core/route/input_action_matching.py`
- `prj/continuity_db/imple/V00.00.01/core/route/input_action_execution.py`
- new `prj/continuity_db/imple/V00.00.01/core/clarification.py`
- `prj/continuity_db/imple/V00.00.01/core/continuity_db/migrations.py`
- `migrations/<date>_add_clarification_workflow.sql`
- `prj/continuity_db/imple/V00.00.01/test/unit/core/`
- `prj/continuity_db/imple/V00.00.01/test/sit/core/`
- `prj/continuity_db/imple/V00.00.01/test/uat/workflows/`

## Current status

- [x] Audit completed.
- [x] Detailed implementation plan drafted.
- [x] User review/authorization to begin implementation.
- [x] MVP clarification schema, classifier, router gate, and tests implemented.
- [ ] Complete extended detection, resolution state machine, continuous integration, and full migration/acceptance verification.
