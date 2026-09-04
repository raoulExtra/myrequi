# Meta optimization trace

Meta actions

- ready: False
- phase count: 3
- active plan count: 1
- done plan count: 6
- modularity issue count: 1
- phase gap count: 0

## signals
- modularity_budget_not_clean
- phase_definitions_clear
- active_plan_present
- history_available

## recommendations
- modularity: modularize oversized files before the next checkpoint

## corrections
- auto-heal: modularity -> split or move the oversized files into smaller modules now
- preventive: phase_requirements -> rechallenge the phase definitions whenever a new phase appears
- preventive: planning -> keep the active plan small and reviewable

## raw trace
```json
{
  "active_plan_count": 1,
  "corrections": [
    {
      "action": "split or move the oversized files into smaller modules now",
      "area": "modularity",
      "kind": "auto-heal"
    },
    {
      "action": "rechallenge the phase definitions whenever a new phase appears",
      "area": "phase_requirements",
      "kind": "preventive"
    },
    {
      "action": "keep the active plan small and reviewable",
      "area": "planning",
      "kind": "preventive"
    }
  ],
  "done_plan_count": 6,
  "missing_phases": [],
  "modularity_issue_count": 1,
  "phase_count": 3,
  "phase_gap_count": 0,
  "ready": false,
  "recommendations": [
    {
      "action": "modularize oversized files before the next checkpoint",
      "area": "modularity",
      "count": 1
    }
  ],
  "root": "prj/self_learn",
  "signals": [
    "modularity_budget_not_clean",
    "phase_definitions_clear",
    "active_plan_present",
    "history_available"
  ],
  "summary": "Meta actions",
  "version": 1
}
```
