# Acceptance Criteria: Plan generation from memory

## R2.1: Module exists
- [ ] File exists for plan generation module

## R2.2: DB plan generation
- [ ] Can fetch a plan by plan_key from work_plans table
- [ ] Can extract title, objective, prompt, and steps
- [ ] Can handle linked plans (work_plan_links)

## R2.3: Prompt-based plan generation
- [ ] Can generate plan from free text prompt
- [ ] Can extract numbered steps from "ONLY" guidance
- [ ] Can create title from prompt text

## R2.4: Output format
- [ ] Markdown output includes file number
- [ ] Markdown output includes kind (db/prompt)
- [ ] Markdown output includes Name, Source, Objective sections

## R2.5: File creation
- [ ] Creates properly numbered file (N_plan.md)
- [ ] Writes to plans/ directory
- [ ] Returns paths of created files