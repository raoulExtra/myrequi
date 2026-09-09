# 001-GLOS-001-glossary-projects

**Category:** Glossary

## Glossary for Projects
Terms specific to project management and requirements engineering.

### acceptance_criterion
**Phase:** Validate
**Definition:** A specific observable condition used to decide whether a requirement or increment is acceptable.
**Why it matters:** Turns agreement into a repeatable decision rather than an impression.
**Elegant prompt:** What example would clearly pass, and what boundary example should fail?
**Example:** Given a case aged 4h01m, an alert is visible to its assigned lead within 60 seconds.
**Anti-pattern:** Works as expected.

### aim
**Phase:** Frame
**Definition:** A broad intended direction or effect.
**Why it matters:** Keeps the highest-level direction separate from concrete targets.
**Elegant prompt:** What broad direction or effect are we aiming for?
**Example:** Improve the onboarding experience for new users.
**Anti-pattern:** Treat the aim as a task list.

### assumption
**Phase:** Frame
**Definition:** A proposition treated as true for planning but not yet established by evidence.
**Why it matters:** Turns hidden beliefs into testable risks.
**Elegant prompt:** What are we relying on without having confirmed it?
**Example:** Assume 90% of users can receive SMS; validate against account data.
**Anti-pattern:** Users will understand it.

### baseline
**Phase:** Manage
**Definition:** An approved snapshot used as a stable reference for controlled change.
**Why it matters:** Provides a known comparison point without pretending requirements will never evolve.
**Elegant prompt:** Which approved set is the current reference, and who may change it?
**Example:** Baseline 2.1 approved by product, operations, security, and the customer representative.
**Anti-pattern:** The latest document in the folder.

### business_rule
**Phase:** Specify
**Definition:** A policy or decision rule governing operations independently of a particular interface.
**Why it matters:** Keeps organizational logic visible and reusable across solutions.
**Elegant prompt:** Which policy determines the permitted decision?
**Example:** Cases involving minors require approval by a trained specialist.
**Anti-pattern:** Disable the button for some users.

### change_request
**Phase:** Manage
**Definition:** A proposed modification with rationale, affected items, impact, authority, and disposition.
**Why it matters:** Makes change explicit and assessable rather than silently rewriting history.
**Elegant prompt:** Why change, what is affected, what will it cost or risk, and who decides?
**Example:** CR-18 changes retention from 30 to 90 days; impacts storage, policy, tests, and notice text.
**Anti-pattern:** Update the requirement.

### conflict
**Phase:** Analyze
**Definition:** An incompatibility between requirements or a disagreement among stakeholders about them.
**Why it matters:** Naming conflict early enables reasoned negotiation instead of hidden compromise.
**Elegant prompt:** Which goals cannot currently be satisfied together, and who bears each trade-off?
**Example:** Immediate deletion conflicts with the seven-year audit-retention obligation.
**Anti-pattern:** Stakeholders need alignment.

### constraint
**Phase:** Frame
**Definition:** A non-negotiable limit on possible solutions or delivery.
**Why it matters:** Distinguishes mandatory boundaries from preferences.
**Elegant prompt:** Which legal, technical, temporal, budgetary, or operational limits cannot be traded away?
**Example:** Customer records must remain in the EU region.
**Anti-pattern:** Use the current database because it is familiar.

### decision_rationale
**Phase:** Manage
**Definition:** A concise record of why an option was chosen, including evidence, trade-offs, dissent, and review conditions.
**Why it matters:** Allows later learning and prevents the decision from losing its context.
**Elegant prompt:** Why this option, why not the alternatives, and what would trigger reconsideration?
**Example:** Choose reversible manual review now; automate after error rates stay below 1% for a month.
**Anti-pattern:** Approved in the meeting.

### elicitation
**Phase:** Elicit
**Definition:** The deliberate seeking, capturing, and consolidation of information from relevant sources.
**Why it matters:** Frames collection as active discovery rather than passive transcription.
**Elegant prompt:** Which source and technique will reveal what is still unknown?
**Example:** Observe agents handling failed onboarding, then confirm findings in a workshop.
**Anti-pattern:** Ask stakeholders what features they want.

### elicitation_probe
**Phase:** Elicit
**Definition:** A neutral question or prompt designed to expose goals, exceptions, evidence, and consequences.
**Why it matters:** Good probes reduce suggestion bias and surface tacit knowledge.
**Elegant prompt:** Can you show the last time this happened, including exceptions?
**Example:** Walk me through yesterday’s failed case from trigger to resolution.
**Anti-pattern:** Would an automated alert solve this?

### evidence
**Phase:** Elicit
**Definition:** An observation, record, measurement, or authoritative statement that supports or challenges a claim.
**Why it matters:** Separates demonstrated conditions from opinion.
**Elegant prompt:** What would make this claim credible or falsify it?
**Example:** Ticket data shows 37% of blocked cases receive no response within 48 hours.
**Anti-pattern:** The stakeholder sounded confident.

### functional_requirement
**Phase:** Specify
**Definition:** A requirement describing behavior or a result the system must provide.
**Why it matters:** Clarifies what the system does while leaving unnecessary design choices open.
**Elegant prompt:** Given what trigger and state, what response must occur?
**Example:** When verification fails twice, the service shall create a manual-review task.
**Anti-pattern:** Implement a workflow engine.

### goal
**Phase:** Frame
**Definition:** A specific desired target state or condition; if achieved, it yields an outcome.
**Why it matters:** Keeps the target state distinct from the realized result.
**Elegant prompt:** What specific target state do we want?
**Example:** Reduce onboarding support delay to four hours.
**Anti-pattern:** Call the goal the outcome before it has happened.

### milestone
**Phase:** Manage
**Definition:** A significant point or event in a project timeline marking the completion of a deliverable or phase.
**Why it matters:** Provides checkpoints for progress tracking and stakeholder alignment.

### mission
**Phase:** Frame
**Definition:** The enduring purpose that organizes a project’s aims and goals.
**Why it matters:** Provides a stable reason for the project and its work.
**Elegant prompt:** What enduring purpose does this project serve?
**Example:** Help new users succeed at onboarding with less friction.
**Anti-pattern:** Use the mission as a one-off task.

### negotiation
**Phase:** Analyze
**Definition:** Structured deliberation aimed at resolving conflicts and reaching an accountable agreement.
**Why it matters:** Preserves dissent, rationale, and consequences while enabling decisions.
**Elegant prompt:** Which interests, evidence, authority, and exposure should shape this trade-off?
**Example:** Legal, operations, and affected users compare harm, obligation, and reversible options.
**Anti-pattern:** The loudest stakeholder decides.

### open_question
**Phase:** Frame
**Definition:** A material unknown with an owner and a resolution path.
**Why it matters:** Preserves uncertainty without allowing it to disappear into prose.
**Elegant prompt:** What must be learned, by whom, and before which decision?
**Example:** Security will confirm the retention period before architecture approval.
**Anti-pattern:** TBD.

### outcome
**Phase:** Frame
**Definition:** A measurable improvement expected for stakeholders or the organization.
**Why it matters:** Keeps requirements tied to value rather than output volume.
**Elegant prompt:** What should become measurably better, for whom, and by when?
**Example:** Reduce median onboarding support delay from three days to four hours.
**Anti-pattern:** Improve customer experience.

### plan
**Phase:** Specify
**Definition:** The ordered execution path that turns strategy into actionable work.
**Why it matters:** Makes the intended sequence of work explicit.
**Elegant prompt:** What ordered execution path gets us there?
**Example:** First reduce the support queue, then simplify onboarding, then measure the change.
**Anti-pattern:** Treat the plan as a vague intention.

### priority
**Phase:** Analyze
**Definition:** The relative importance or ordering of an item under stated criteria and time horizon.
**Why it matters:** Prevents urgency, value, risk, and effort from being collapsed into one unexplained rank.
**Elegant prompt:** Priority for what objective, by when, using which criteria?
**Example:** High now because it reduces regulatory exposure before the audit; revisit afterward.
**Anti-pattern:** Everything is high priority.

### problem
**Phase:** Frame
**Definition:** The situation worth changing, expressed without assuming a particular solution.
**Why it matters:** Prevents premature design from disguising the actual purpose.
**Elegant prompt:** What observable situation makes change worthwhile?
**Example:** Support requests take three days, causing customers to abandon onboarding.
**Anti-pattern:** Build an AI chatbot.

### project
**Phase:** Frame
**Definition:** A bounded initiative with a goal, scope, stakeholders, and delivery path.
**Why it matters:** Keeps work organized into accountable efforts instead of vague activity.
**Elegant prompt:** What initiative are we advancing, for whom, and by when?
**Example:** Demo project for step-by-step delivery from MVP to V0.0.1.
**Anti-pattern:** Just a task list.

### quality_attribute
**Phase:** Specify
**Definition:** A measurable characteristic describing how well a system performs or behaves.
**Why it matters:** Makes performance, security, usability, reliability, and similar expectations testable.
**Elegant prompt:** How well must it work, under what load or environment, and at what percentile?
**Example:** For 95% of cases, the alert shall appear within 60 seconds of the threshold.
**Anti-pattern:** Alerts must be fast.

### release
**Phase:** Manage
**Definition:** A published version of the product delivered to stakeholders, marking the end of a development cycle.
**Why it matters:** Creates accountability and a clear handoff point for stakeholders.

### requirement
**Phase:** Specify
**Definition:** A documented condition, capability, or quality that must be satisfied to address a need or obligation.
**Why it matters:** Creates an agreed, assessable statement without confusing it with implementation.
**Elegant prompt:** What must hold, for whom, under which conditions, and how will it be checked?
**Example:** When a case exceeds four hours, the service shall alert the assigned support lead.
**Anti-pattern:** Add alerting.

### requirement_source
**Phase:** Elicit
**Definition:** The identifiable origin from which a need or requirement was derived.
**Why it matters:** Enables confirmation, accountability, and later impact analysis.
**Elegant prompt:** Who or what supports this statement?
**Example:** Source: observation of five support shifts and policy SEC-14.
**Anti-pattern:** Everyone says so.

### scenario
**Phase:** Elicit
**Definition:** A concrete sequence describing context, trigger, interaction, and outcome, including exceptions.
**Why it matters:** Reveals hidden states and edge cases more effectively than isolated statements.
**Elegant prompt:** What happens from the triggering event through success or failure?
**Example:** When identity verification fails twice, route the case to manual review and notify the customer.
**Anti-pattern:** The system handles failures.

### scope_boundary
**Phase:** Frame
**Definition:** An explicit statement of what the initiative includes and excludes.
**Why it matters:** Makes trade-offs visible and prevents silent expansion.
**Elegant prompt:** What is deliberately inside, outside, and undecided?
**Example:** Includes onboarding cases; excludes billing disputes in this release.
**Anti-pattern:** Handle all support problems.

### stakeholder
**Phase:** Frame
**Definition:** A person, group, or organization that influences the change or experiences its consequences.
**Why it matters:** Missing stakeholders create missing needs and late surprises.
**Elegant prompt:** Who decides, uses, operates, supports, regulates, pays for, or is affected by this?
**Example:** Include users, support staff, security, legal, and customers who cannot use the new flow.
**Anti-pattern:** The product owner represents everyone.

### stakeholder_need
**Phase:** Frame
**Definition:** A capability or result a stakeholder requires, stated from that stakeholder’s perspective.
**Why it matters:** Separates the human or organizational need from the system response.
**Elegant prompt:** What must this stakeholder be able to achieve, and why?
**Example:** A support agent needs to identify blocked onboarding cases before customers leave.
**Anti-pattern:** The dashboard must use React.

### stakeholders
**Phase:** Frame
**Definition:** A person, group, or organization that influences the change or experiences its consequences.
**Why it matters:** Missing stakeholders create missed needs and late surprises. Understanding who is involved ensures buy-in and reduces risk.
**Elegant prompt:** Who decides, uses, operates, supports, regulates, pays for, or is affected by this change?
**Example:** Product Owner (PO), end-user customers, support staff, security team, legal department.
**Anti-pattern:** Assuming only developers care about the project; ignoring external partners.

### step
**Phase:** Manage
**Definition:** One executable action inside a plan.
**Why it matters:** Keeps execution concrete and tractable.
**Elegant prompt:** What is the next executable action in the plan?
**Example:** Update the onboarding checklist.
**Anti-pattern:** Bundle many actions into one step.

### strategy
**Phase:** Analyze
**Definition:** A chosen approach for pursuing a mission and its goals.
**Why it matters:** Turns the mission into a deliberate path.
**Elegant prompt:** What approach will best reach the mission and goals?
**Example:** Start with guided setup, then simplify the remaining tasks.
**Anti-pattern:** Confuse the strategy with the execution plan.

### traceability
**Phase:** Manage
**Definition:** Recorded links among sources, needs, requirements, decisions, implementation, and evidence.
**Why it matters:** Makes rationale and change impact inspectable.
**Elegant prompt:** Can this item be followed backward to its reason and forward to its proof?
**Example:** Need N-12 → requirement R-31 → decision D-8 → test T-44.
**Anti-pattern:** The ticket links to the epic.

### validation
**Phase:** Validate
**Definition:** Checking that requirements and the resulting solution address the intended stakeholder needs in context.
**Why it matters:** Asks whether the correct problem is being solved.
**Elegant prompt:** Would this outcome genuinely help the affected stakeholder in the real setting?
**Example:** Support agents trial the alert and confirm it prevents overlooked cases.
**Anti-pattern:** All acceptance tests passed, so users must want it.

### verification
**Phase:** Validate
**Definition:** Checking that a requirement or work product meets its specified form, quality rules, and implementation criteria.
**Why it matters:** Asks whether the result was built and documented correctly.
**Elegant prompt:** Is the statement and implementation internally correct and testable?
**Example:** Review finds one actor, one trigger, a measurable response, and a passing test.
**Anti-pattern:** The developer reviewed it.

### workspace
**Phase:** Manage
**Definition:** A structured, auditable working area for one problem or task, keeping the goal, constraints, evidence, uncertainty, decisions, and next actions together.
**Why it matters:** Prevents scattered notes and makes thinking easier to revisit, revise, and audit.
**Elegant prompt:** What belongs in the workspace so this problem can be understood and advanced without losing provenance?
**Example:** For the policy change, keep one workspace with the goal, constraints, options, evidence, decision log, and follow-up steps.
**Anti-pattern:** A pile of unrelated notes, chats, and ad hoc decisions with no shared structure or traceability.
