'''yaml
title: R7-G-graph-semaphore-acc-crit
requirement_id: R7-G
source_requirement: R7-G-graph-semaphore.md
'''

# Acceptance criteria for R7-G

## Requirement
- [R7-G requirement](R7-G-graph-semaphore.md)

## Verification ideas
- The demo project defines a semaphore mechanism for graph work.
- The semaphore accepts a PID argument.
- Multiple PID processes can coordinate against the same graph.
- The semaphore prevents conflicting updates or clearly arbitrates them.
- A reviewer can confirm the semaphore concept is represented in the demo project.
