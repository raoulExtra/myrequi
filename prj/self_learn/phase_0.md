# Phase 0: Auto Prompt Automation

PROJECT PHASE 0

purpose: Enable AI to ask questions and automate self-learning paths through interactive prompts.

goals:
- Implement a lightweight prompt helper for automation questions
- Support one-line questions, options, notes, and defaults
- Maintain non-interactive safety and CLI compatibility
- Keep documentation small and reviewable

goals:
- Create a standardized way to ask questions in automation workflows
- Enable AI to suggest paths based on user input
- Maintain backward compatibility with existing automation

outcome: Interactive automation surface for decision-making in self-learning projects
outcome_doc: docs/phase-0-outcome.md

core_requirements:
- [code] PH000-RC001: define auto as the project automation subproject.
- [code] RC012-AUTO: provide a lightweight prompt helper for automation questions.
- [code] RC013-AUTO: support one-line questions without options.
- [code] RC014-AUTO: support questions with numbered options.
- [code] RC015-AUTO: support an optional note and default answer.
- [code] RC017-AUTO: keep the CLI trigger surface stable for manual filesystem actions.

acceptance criteria:
- RC012-AC001-AUTO: auto is described as the place where project automations live.
- RC012-AC002-AUTO: the description stays visible in the phase 0 story.
- RC012-AC003-AUTO: the implementation path is explicit and reusable.
- RC017-AC001-AUTO: the CLI trigger surface remains stable for filesystem actions.