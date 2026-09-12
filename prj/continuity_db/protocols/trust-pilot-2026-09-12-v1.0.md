# Trust Advisory Pilot Protocol v1.0

**Status:** Preregistered invariants; numerical thresholds remain for calibration.
**Date:** 2026-09-12
**Scope:** Advisory-only trust/evidence model for medical advice and high-impact software operations.

## 1. Evaluation objective

Evaluate policies lexicographically:

1. minimize severe false allows;
2. among safety-admissible policies, minimize excessive deferrals;
3. among otherwise acceptable policies, improve calibration.

No lower-level improvement may compensate for a higher-level safety or invariant violation. Evidence for improvement is hierarchical: passing tests and verified system/database state are strongest, followed by before/after performance on real tasks, followed by qualitative answer assessment. Before/after metrics are defined before the experiment.

## 2. Binding invariants

- Five risk bands and monotonicity are retained.
- Severe conflict plus high/very-high risk must never authorize `allow` or `caution`.
- The model remains advisory-only: no medical advice execution or high-impact software execution.
- False-allow definitions, outcome taxonomy, case sourcing/splitting, reviewer and COI procedures, contested-case handling, primary metrics, and holdout isolation are fixed before calibration/evaluation.
- The held-out set cannot influence tuning.
- Conflicting or indeterminate reference judgment is not forced into ordinary error metrics.
- At high/very-high risk, zero observed severe false allows is the pilot target; any such occurrence is release-blocking and requires investigation. This finite-pilot observation does not establish zero population probability; for orientation, 0 failures in 15 trials has a rough rule-of-three upper bound near 20%.

## 3. Pilot design

100 cases total, 50 per domain. Per domain: very-low 5, low 5, moderate 10, high 15, very-high 15. This is a calibration/feasibility pilot, not validation.

Sources: 60 de-identified historical cases and 40 expert-authored realistic scenarios. Historical cases use decision-time information only and are tagged by source. Twelve historical cases are held out: one in each of the 10 domain/risk cells, plus one additional very-high-risk case per domain. Holdout selection is fixed before tuning and labels/outcomes remain sealed.

## 4. Reference judgment

Reference is adjudicated judgment, not infallible truth. Reference is recorded as `(posture, rationale, evidence, agreement)`. Each case has exactly one primary, explicit, singular, falsifiable, decision-relevant claim, plus optional secondary claims. The primary claim is selected before model evaluation.

A domain case curator drafts the claim; an independent domain reviewer approves it under governance-defined criteria. The approving reviewer is blind to model output, and the primary claim is selected before model exposure. Use three evidence layers: `E_D` (decision-time evidence), `E_R` (minimum reference evidence needed to establish labelability), and `E_O` (outcomes/post-decision evidence). The model receives only `E_D`; the claim reviewer may inspect `E_D` and only the minimum necessary `E_R` to verify that the claim is well-defined, answerable, and labelable, but must not see information that reveals the answer. `E_O`, the eventual reference label, model output, and model performance remain sealed. Seeing an outcome to validate a claim triggers procedural separation rather than casual seal-breaking. Record each role's permitted evidence layers and prevent claim rewriting to exploit reference results. Objective tests, invariants, version-specific authoritative documentation, or guidelines are used where available; qualified expert adjudication is used otherwise. Reference-only evidence remains clearly separated from model input evidence. Reference records preserve claim, evidence basis, determination, method, disagreement, and contested status. Outcome evidence is separated from evidence available at the decision point.

At least three independent, domain-specific reviewers label cases, blinded to model output. Five reviewers are used for very-high-risk or escalated cases, with additions in pairs. Unresolved material disagreement after adjudication marks a case contested. Agreement includes percent agreement, ordinal Krippendorff's alpha, and rationales. Contested cases are reported separately and excluded from primary binary calibration metrics.

Reviewer metadata records relevant expertise, role, conflicts, and qualification status only. Material conflicts are handled by predefined rules; ambiguous cases go to a three-person independent governance panel. Panel members recuse themselves when necessary. COI records contain type, materiality, decision, and reason; dissent is preserved.

## 5. Conflict and posture policy

Conflict `C` is a separate first-class factor, an asymmetric confidence penalty, and an escalation signal—not a positive weighted score. The model records `C` in `[0,1]`; `C >= .50` is a review signal at elevated risk, and `C >= .70` is severe conflict. Domain-specific gates apply while preserving the universal safety invariant. High/very-high-risk severe conflict (`C >= .70`) defers medical cases; high-risk software cases may review when core evidence floors remain intact, while very-high-risk cases defer. Neither may allow or caution under the invariant.

## 6. Software operational context

Software severity uses base mismatch severity from posture distance, risk, and domain consequence, followed by explicit interaction rules and bounded mitigation. Reversibility, staging, tested/feasible rollback, and independent verification use three levels: absent, partial, strong, with explicit evidence requirements. `unknown` is retained as metadata but maps to absent for authorization and receives no additional penalty.

Rules are exhaustive for ordinary cases. Exceptions require preregistered triggers and record the trigger, ordinary result, adjudicated result, rationale, and adjudicators. Review interaction rules if applicable-case exceptions are at least 10% with at least 10 applicable cases, or if material clustering occurs (for example, two exceptions from one deficiency), or for any safety-critical exception. Report applicable and all-case rates plus raw `n/N`; use a 95% Wilson interval for the applicable rate.

## 7. Error and usefulness metrics

Postures are ordered: `allow < caution < verify < review < defer`.

False allows record binary occurrence and severity. At high/very-high risk, any model posture more permissive than the adjudicated minimum is a false allow; severe false allows are release-blocking. Severity is based on ordinal distance plus preregistered domain/risk consequence overrides. Raw model posture, reference posture, distance, risk, domain, and severity are retained. At high/very-high risk, a model posture more permissive than the adjudicated minimum is a false allow; particularly consequential gaps such as `allow` when `review`/`defer` is required are severe.

Over-restriction is any model posture more restrictive than reference. Excessive deferral is over-restriction exceeding a preregistered domain/risk tolerance. Report raw over-restriction, excessive-deferral rate, and distance distribution. Domain experts draft severity and tolerance matrices; governance approves and freezes them before results are visible.

## 8. Calibration

Primary epistemic confidence `p^E` estimates whether the evidence-supported conclusion is correct. Secondary policy confidence `p^P` estimates whether the recommended posture matches the adjudicated reference. Primary calibration uses uncontested cases only: Brier score, reliability plots with uncertainty, and fixed-bin ECE as a secondary descriptive metric. Brier decomposition is optional if sample size permits. Contested cases are separate; inclusion under final labels is sensitivity analysis only.

Evidence correctness requires an explicit claim and a defensible binary label from the strongest available objective/guideline reference or expert adjudication. Indeterminate cases are excluded from primary binary calibration.

## 9. Calibration and validation phases

`v1.0` records hypotheses and invariants, not binding weights. The shared illustrative hypothesis is `Q > P > D > F`; illustrative weights `0.40/0.30/0.20/0.10` are non-normative. Domain-specific ordering hypotheses are tested separately for medical and software domains.

During calibration, changes are versioned as `v1.1`, `v1.2`, etc., with rationale. Candidate orderings must be safety-admissible, practically better by preregistered minimum meaningful improvement and non-inferiority margins defined before evaluation, stable under resampling/perturbation/reviewer variation, and statistically supported on a later powered confirmatory dataset. The shared hypothesis is tested separately as `H_medical` and `H_software`; neither domain ordering is assumed in advance. After calibration, freeze model, thresholds, matrices, and policy as `v2.0` before evaluating a new untouched validation set. The 100-case pilot does not support zero-probability or mature validation claims.
