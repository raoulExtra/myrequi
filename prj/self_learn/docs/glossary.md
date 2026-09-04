# Glossary for self_learn

This glossary is the shared vocabulary for the self_learn project.
It is meant to stay small, clear, and extensible.

## Canonical terms

| Term | Meaning | Notes |
| --- | --- | --- |
| project | A named workspace with its own filespace, goal, and operating rules. | self_learn is the current project. |
| filespace | The project directory tree that holds docs, plans, examples, and implementation. | This is the working memory of the project. |
| phase | A named stage of the project docs and workflow. | `phase_0.md` is the entry point. |
| plan | A bounded work unit with an objective and steps. | Plans move to `plans/done/` when complete. |
| step | One actionable item inside a plan. | Keep steps small and ordered. |
| goal | The target state the project is trying to reach. | Goals can drive plans and checkpoints. |
| outcome | The result that actually happens after work. | Outcomes are observed, not assumed. |
| objective | The reason a plan or project exists. | Usually broader than a step and narrower than a mission. |
| canonical | The preferred default-facing term, file, or path. | Use one canonical home per idea. |
| active | Currently in progress. | Active plans live outside `plans/done/`. |
| done | Finished and retained for history. | Completed plans move to `plans/done/`. |
| archive | Superseded material kept for reference. | Keep old material out of the active path. |
| refresh | Sync the tree and rebuild generated views. | Used by `self_learn_automation.py`. |
| checkpoint | Refresh, stage, and commit the current filesystem state. | This is the phase boundary action. |
| docs index | A generated overview of docs and plans. | Lives at `docs/index.md`. |
| learning loop | Observe, update, verify, reuse. | The core self-improvement cycle. |
| glossary | The controlled vocabulary for the project. | Add terms here before relying on them heavily. |
| future-proof | Designed to remain usable as the project grows. | Prefer stable terms, small definitions, and explicit aliases. |
| self_learn | The project that improves its own filesystem and tools. | This repo’s current self-improvement workspace. |
| continuity.db | The durable database for project memory and state. | Use it for persistent goals and checkpoints. |

## Future-proofing rules

1. Keep one canonical term per concept.
2. Add aliases only when they reduce confusion.
3. Prefer short definitions that still hold as the project grows.
4. Separate target state (`goal`) from realized result (`outcome`).
5. Separate active work (`plan`) from finished history (`done`).
6. Update this glossary when a term becomes important enough to reuse.
7. If a term starts to drift, add a note rather than rewriting history.
