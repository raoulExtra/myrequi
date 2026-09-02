'''yaml
title: R7-G-graph-semaphore
requirement_id: R7-G
phase: phase_1_1
for_version: default_version
'''

# R7-G: Graph semaphore for multi-process work

The demo project SHALL provide a semaphore mechanism so multiple PID processes can coordinate work on the same graph without conflicting updates. The semaphore SHALL accept a PID argument so a process can identify itself when claiming or releasing access.

## Traceability
- stakeholder need: multiple processes should be able to work on the same graph safely using PID-based coordination
- related phase: [phase_1_1](phase_1_1.md)

## Acceptance criteria
- [Acceptance criteria](R7-G-graph-semaphore-acc-crit.md)
