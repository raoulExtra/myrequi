# Context and gate contract

Check context usage before each step and during long execution. At 30% or greater, compact before continuing. After compaction, wait for `Compaction completed.`, issue `continue`, reread active state, and resume from the last committed checkpoint.

Approval, pytest, and Git gates must be independently testable. Subprocess and Git behavior must be behind injectable adapters. No step advances until its tests are green and its commit succeeds.
