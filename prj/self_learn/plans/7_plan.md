# Self-learn meta optimization plan

status: active

## objective
Automate the trace of self-learning optimization so the project can see its own improvement signals.

## when to run
- run when a new active plan appears or an active plan changes.
- run after refresh, checkpoint, or phase updates that change plan/state visibility.
- run before using the meta trace to decide the next automation move.

## steps
1. Generate a meta optimization trace from phase state and modularity signals.
2. Persist the trace in docs and continuity.db.
3. Use the trace to guide the next self-learning review.
4. Keep the trace format small and durable.
