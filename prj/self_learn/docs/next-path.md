# Next path

This phase focuses on AI suggesting the first useful self-learn path.

## terms

| Term | Meaning |
| --- | --- |
| path | An ordered route from current state to a desired next state. |
| candidate | One possible path that may become the next step. |
| suggestion | An AI proposal for which path to take next. |
| recommendation | A suggestion ranked with reasons and confidence. |
| criteria | A rule or reason used to compare candidate paths. |
| priority | A ranking signal that helps choose among candidates. |
| feedback | Observed outcome data that changes the next suggestion. |
| review | A check that evaluates whether the chosen path worked. |

## selection rules

1. Prefer the highest-priority candidate that matches the glossary and current project state.
2. Require explicit criteria for every ranked suggestion.
3. Review the result before promoting the next path to a plan.
4. Feed feedback back into the next suggestion.
