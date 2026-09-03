'''yaml
title: R8-G-graph-beam-filter-acc-crit
requirement_id: R8-G
source_requirement: R8-G-graph-beam-filter.md
'''

# Acceptance criteria for R8-G

## Requirement
- [R8-G requirement](R8-G-graph-beam-filter.md)

## Verification ideas
- The demo project supports a beam-search algorithm.
- The beam-search algorithm runs on the selected graph.
- The requirement explains that beam search keeps only a limited set of promising paths at each step.
- The demo project applies filtering during expansion or re-ranking.
- A reviewer can confirm the beam-search and filtering behavior are connected.
