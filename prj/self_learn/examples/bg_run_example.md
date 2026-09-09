# bg_run Example Reference

## Quick Usage

### From Interactive Pi Session

When Pi shows the tool selection prompt, paste the JSON:

```json
{
  "name": "Queue manager",
  "command": "python3 pi_queue.py run-all",
  "isAgent": false
}
```

### From Command Line

Use the `/bg` command:

```text
/bg --name "Queue runner" python3 pi_queue.py run-all
/bg --agent --name "Background pi" pi -p "what is my goal?"
/bg --name="Server" -- npm run dev
```

## JSON Schema

```json
{
  "name": "string (required) - 2-6 word task name",
  "command": "string (required) - shell command",
  "isAgent": "boolean (required) - true for pi/LLM processes",
  "description": "string (optional) - human context",
  "timeoutSeconds": "number (optional) - max execution time",
  "notifyOnCompletion": "boolean (optional) - send notification",
  "triggerOnCompletion": "boolean (optional) - auto follow-up turn"
}
```

## Common Patterns

### Sequential Prompt Queue
```json
{
  "name": "Process queue",
  "command": "python3 pi_queue.py run-all",
  "isAgent": false
}
```

### Interactive Pi Query
```json
{
  "name": "Query pi",
  "command": "pi -p \"analyze plans folder\"",
  "isAgent": true
}
```

### File-Based Processing (Read-Only)
```json
{
  "name": "Read-only plan analysis",
  "command": "pi --exclude-tools bash,edit,write -p @plans/plan_0.md",
  "isAgent": true
}
```

### File-Based Processing (Inspect-Only Tools)
```json
{
  "name": "Inspect plan file",
  "command": "pi --tools read,ls,find,grep,pydoc -p @plans/plan_0.md",
  "isAgent": true
}
```

## Output Location

Results are written to:
```
.pi/tasks/<session>-<pid>/<task-id>.output
.pi/tasks/<session>-<pid>/<task-id>.json
```

View with:
- `bg_status` / `pi bg status`
- `bg_logs` / `pi bg logs <task-id>`