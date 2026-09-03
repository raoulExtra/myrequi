'''yaml
title: 004-requi-continuity-db-starter-guidance
requirement_id: R4
phase: phase_1_1
for_version: default_version
'''

# R4: Database and filesystem guidance in docs

The demo project documentation SHALL describe what lives 
in continuity.db, what lives in the filesystem.
for details to the db it links starter.md
the description sits in a Markdown file under project base
subdir docs/.

## Traceability
- stakeholder need: the demo project should link the memory
  database guidance from starter.md
- evidence markers: continuity.db[REF_EXISTS]
  starter.md[REF_EXISTS] filesystem[REF_EXISTS]
- related phase: [phase_1_1](phase_1_1.md)

## Acceptance criteria
- [Acceptance
  criteria](004-acc-crit-continuity-db-starter-guidance.md)
