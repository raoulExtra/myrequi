# work_plans row 30

- id: 30
- plan_key: dependency_first_planning
- title: Dependency-first planning
- objective: Uncover hidden dependencies before execution
- status: completed
- created_by: Peter
- created_at: 2026-09-01 07:08:53
- updated_at: 2026-09-01 07:08:53
- prompt: 1. State the goal in one sentence
     - What’s the exact outcome?

 2. List assumptions
     - Inputs, data, permissions, tools, timing, stakeholders.

 3. Ask “what must be true before this can start?”
     - For each step, identify prerequisites.

 4. Break work into smallest steps
     - Hidden deps usually appear between steps.

 5. Trace interfaces
     - Look at handoffs: API, file formats, teams, systems, approvals.

 6. Ask failure questions
     - What breaks if X is missing?
     - What blocks deployment/testing/review?

 7. Check external constraints
     - Security, legal, budget, infrastructure, policy, deadlines.

 8. Build a dependency map
     - Mark: blocker / needed / optional / unknown.

 9. Validate with a second pass
     - Have someone else review the plan and point out what you missed.

 Quick prompt to use:

 │ “What inputs, approvals, systems, assumptions, and prior tasks does
 │ this depend on, and what happens if each is late or absent?”
