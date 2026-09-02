import json


def fe_pending_instructs(mode=None):
    cmd = '''python3 - <<'PY'
import json, sqlite3
from pathlib import Path
root = Path.cwd()
for candidate in [root / 'chat.db', root.parent / 'chat.db']:
    if candidate.exists():
        db_path = candidate
        break
else:
    db_path = root / 'chat.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
fe_row = cur.execute("select value from variables where name='fe'").fetchone()
fe = bool(fe_row and str(fe_row[0]).lower() in ('1','true','yes','on'))
pending = [
    {'id': row[0], 'content': row[1], 'status': row[2]}
    for row in cur.execute("select id, content, status from instruct where status='pending' order by id")
]
if mode == 'done' or (fe and pending):
    cur.execute("update instruct set status='done' where status='pending'")
    conn.commit()
print(json.dumps({'fe': fe, 'pending': pending}))
conn.close()
PY'''
    return bash(cmd)
