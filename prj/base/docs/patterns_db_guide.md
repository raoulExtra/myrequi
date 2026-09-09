# Pattern Library: Working with continuity.db

> **Goal**: Provide reusable patterns for adding meta-learning tracking without
> breaking the database. These patterns are generalized across projects, not
> Mesa-specific.

---
## 🔍 Quick Start: Explore the Schema

Before making any changes, understand what you're working with:

```bash
# List all tables
sqlite3 continuity.db "SELECT name FROM sqlite_master WHERE type='table';"

# Show schema for any table
sqlite3 continuity.db "PRAGMA table_info(your_table_name);"

# Check distinct values for enum columns
sqlite3 continuity.db "SELECT DISTINCT status FROM reasoning_episodes;"
sqlite3 continuity.db "SELECT DISTINCT confidence FROM reasoning_episodes;"

# Show existing data patterns
sqlite3 continuity.db "SELECT * FROM metacognitive_state WHERE state_key='self_learn_meta_trace' LIMIT 1;"
```

---
## 📦 Pattern 1: Add a Meta-Trace Correction

Use when recording that a new requirement/AC was added and how it was integrated.

### Steps

```python
import sqlite3
import json

conn = sqlite3.connect('continuity.db')
cursor = conn.cursor()

# 1. Read current meta-trace
cursor.execute("SELECT value FROM metacognitive_state WHERE state_key='self_learn_meta_trace'")
row = cursor.fetchone()
trace = json.loads(row[0]) if row else {'corrections': [], 'active_plan_count': 0}

# 2. Append new correction
new_correction = {
    'action': 'Describe what you did',
    'details': 'Optional: extra context',
    'timestamp': 'YYYY-MM-DD',
    'generalisable': True,  # Set to True for reusable patterns
    'principle': 'New things count; requi & acc must remain consistent across projects'
}
trace['corrections'].append(new_correction)

# 3. Build updated trace (keep active_plan_count unchanged unless changed)
new_trace = {
    'active_plan_count': trace['active_plan_count'],
    'corrections': trace['corrections']
}

# 4. Get current version and increment
cursor.execute("SELECT version FROM metacognitive_state WHERE state_key='self_learn_meta_trace'")
cur_ver = cursor.fetchone()[0]
new_ver = cur_ver + 1

# 5. Update with version increment (CRITICAL)
cursor.execute(
    "UPDATE metacognitive_state SET value = ?, version = ?, updated_at = 'YYYY-MM-DD' "
    "WHERE state_key = 'self_learn_meta_trace'",
    (json.dumps(new_trace), new_ver)
)

conn.commit()
conn.close()
```

### Anti-Patterns to Avoid

❌ **Don't forget to increment version** → `IntegrityError: metacognitive_state version must increment by 1 on change`

❌ **Don't use `json.append()`** → SQLite JSON functions are limited; manipulate in Python

❌ **Don't forget `conn.commit()`** → Changes are lost on disconnect

❌ **Don't use version 0** → First entry should start from existing version + 1

### Verification

```bash
# Check the update worked
sqlite3 continuity.db "SELECT version FROM metacognitive_state WHERE state_key='self_learn_meta_trace';"

# Check the correction was added
sqlite3 continuity.db "SELECT json_extract(value, '$.corrections[-1].action') FROM metacognitive_state WHERE state_key='self_learn_meta_trace';"
```

---
## 📝 Pattern 2: Add a Reasoning Episode

Use when recording the reasoning behind a design decision.

### Constraints (must respect these!)

| Column | Type | Allowed Values |
|--------|------|----------------|
| `confidence` | REAL | 0.0 to 1.0 (0.95 is safe default) |
| `status` | TEXT | 'active', 'superseded', or 'archived' (currently only 'active' has entries) |
| `mode_trail` | TEXT | Free text, but match existing pattern like `"scientist -> builder -> skeptic"` |
| `source_mode` | TEXT | 'derived' or 'user' |

### Steps

```python
episode_sql = (
    "INSERT INTO reasoning_episodes "
    "(episode_key, title, claim, evidence_summary, inference, "
    "rejected_alternatives, uncertainty, confidence, mode_trail, "
    "next_action, status, source_mode, created_at) "
    "VALUES (?, ?, ?, ?, ?, ?, 0.95, 0.95, 'scientist -> builder -> skeptic', "
    "'completed', 'active', 'user', 'YYYY-MM-DD')"
)

episode_vals = (
    'your-episode-key',  # lowercase-hyphenated, unique
    'Title of the episode',
    'The claim being argued',
    'Evidence summary',
    'What was inferred',
    'What was rejected',
    'delegated_to',  # or 'completed'
    'user',  # or 'user'
    '2026-09-06'
)

cursor.execute(episode_sql, episode_vals)
conn.commit()
```

### Episode Key Naming Convention

- `lowercase-hyphenated`
- `unique-per-project-or-feature`
- `example: mesa-sim-req-20260906`, `req-ac-integration-20260906`

### Verification

```bash
# Check it was added
sqlite3 continuity.db "SELECT id, title, status, confidence FROM reasoning_episodes WHERE episode_key='your-episode-key';"
```

---
## ⚠️ Common Pitfalls & Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| `CHECK constraint failed: confidence BETWEEN 0 AND 1` | Confidence outside 0-1 range | Use 0.95 as safe default (see existing episodes) |
| `CHECK constraint failed: status IN ('active','superseded','archived')` | Status not enum value | Use exactly `'active'` (most common) or `'superseded'` |
| `IntegrityError: metacognitive_state version must increment by 1 on change` | Version not incremented | Always read current version + 1 |
| `UNIQUE constraint failed: episode_key` | Duplicate episode key | Use unique key per feature/project |
| `NOT NULL constraint failed: reasoning_episodes.claim` | Missing claim field | Always provide claim (it's required) |

### Quick Test Before Full Operation

```bash
# 1. Test reading schema
sqlite3 continuity.db "PRAGMA table_info(metacognitive_state);"

# 2. Test a minimal change first
sqlite3 continuity.db "SELECT version FROM metacognitive_state WHERE state_key='self_learn_meta_trace';"

# 3. Then proceed with full operation
```

---
## 💡 General Principles (the "Meta-Learning")

These principles should guide ALL work with continuity.db:

1. **New things count** - Every new requirement, AC, episode, or conviction is recorded
2. **Requirements & ACs must remain consistent across projects** - Patterns should generalize
3. **Version always increments** - Never skip this, even if it seems unnecessary
4. **Enums have exact values** - Check `SELECT DISTINCT column_name FROM table_name` before using
5. **JSON in Python, not SQL** - SQLite JSON functions are limited; manipulate in Python
6. **Test before committing** - Verify with SELECT before UPDATE/INSERT

---
## 📋 When to Add a Correction vs. a Reasoning Episode

| Add Correction When... | Add Reasoning Episode When... |
|------------------------|-------------------------------|
| New requirement or AC added | Design decision recorded |
| Scope clarified | Trade-offs documented |
| Conflict resolved | Alternative approaches rejected |
| Principle established | Pattern for future reuse |
| Version/boundary change | Specific implementation detail |

---
## 🔧 Need Help?

If you're unsure:
1. `sqlite3 continuity.db "SELECT * FROM pragma_table_info('metacognitive_state');"` - see exact schema
2. `sqlite3 continuity.db "SELECT * FROM reasoning_episodes LIMIT 1;"` - see exact episode format
3. Ask the community or check `prj/self_learn/docs/000_phase/` for related patterns

---
*This guide was created to make working with continuity.db more predictable and less error-prone. Contributions of new patterns welcome!*

---
*Last updated: 2026-09-06*
*Related: 000-P-MESA-003-RC, 000-P-MESA-004-RC (Mesa simulation requirement patterns)*