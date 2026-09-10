---
id: 000-PH-001-CREQ-SYNCHRONISATION
category: Core Requirement
title: Core Requirement for the Synchronisation Component
parent: ../
artifact_role: project-adapted
---

## Purpose

Define a dedicated Synchronisation component for continuity.db that keeps database, memory, glossary, concepts, routes, and project-related filesystem representations aligned.

## Scope

- Scan project filesystem surfaces and identify declared synchronization contracts.
- Use nearby `_sync/<filename>_sync.yaml` manifests for authority, import/export direction, roundtrip level, and bounded action history.
- Compare canonical continuity.db records with project files and report drift or conflicts.
- Import and export only through explicit, reviewable operations.
- Treat all project folders as potential synchronization surfaces except `out/`, which is generated output unless explicit recovery or force mode is used.
- Keep synchronization separate from logging, governance, routing, and recovery while delegating to those components as needed.

## Component Responsibilities

- Synchronisation owns scanning, manifest handling, comparison, conflict detection, and bounded sync actions.
- Governance decides authority, permissions, safety, and conflict policy.
- Routes and the tool interface invoke synchronization operations.
- Logging records manifests, diffs, decisions, and epistemic receipts.
- Recovery handles failed, interrupted, or reversible synchronization actions.

## Related

- `000-PH-001-SREQ-SYNCHRONISATION.md`
- `000-PH-001-AC-SYNCHRONISATION.md`
- `../../../../../base/sync/000-PH-001-CREQ-SYNCHRONISATION.md`
