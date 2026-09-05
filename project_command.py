#!/usr/bin/env python3
import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'continuity.db'

THINKING_PROJECT_OBJECT_TYPE = 'concept'
THINKING_PROJECT_OBJECT_KEY = 'thinking_project'
THINKING_PROJECT_RELATIONSHIP = 'tracks'
THINKING_PROJECT_NOTE = 'This project is a thinking/project-reflection workspace'


def project_goal_state_key(project_name):
    return f'project_goal__{project_name}'


def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def get_project_id(cur, project_name):
    row = cur.execute(
        'select id from projects where project_name=?',
        (project_name,),
    ).fetchone()
    if row is None:
        raise ValueError(f'unknown project_name: {project_name}')
    return row[0]


def upsert_project_goal(cur, project_name, goal, confidence=0.97, provenance='project_command'):
    state_key = project_goal_state_key(project_name)
    row = cur.execute(
        'select value, confidence, provenance, version from metacognitive_state where state_key=?',
        (state_key,),
    ).fetchone()
    if row is None:
        cur.execute(
            'insert into metacognitive_state(state_key, category, value, confidence, provenance, version) values(?,?,?,?,?,?)',
            (state_key, 'goals', goal, confidence, provenance, 1),
        )
        return 1
    if row[0] == goal and float(row[1]) == float(confidence) and row[2] == provenance:
        return int(row[3])
    cur.execute(
        'update metacognitive_state set category=?, value=?, confidence=?, provenance=?, version=?, updated_at=CURRENT_TIMESTAMP where state_key=?',
        ('goals', goal, confidence, provenance, int(row[3]) + 1, state_key),
    )
    return int(row[3]) + 1


def set_project_goal(project_name, goal, db_path=DB_PATH):
    conn = connect(db_path)
    try:
        cur = conn.cursor()
        project_id = get_project_id(cur, project_name)
        version = upsert_project_goal(cur, project_name, goal, provenance=f'project:{project_name}')
        state_key = project_goal_state_key(project_name)
        cur.execute(
            'delete from project_objects where project_id=? and object_type=? and object_key=?',
            (project_id, 'metacognitive_state', state_key),
        )
        cur.execute(
            'insert into project_objects(project_id, object_type, object_key, relationship, note) values(?,?,?,?,?)',
            (project_id, 'metacognitive_state', state_key, 'tracks', 'Project-specific goal for the mission.'),
        )
        conn.commit()
        return json.dumps({'project_name': project_name, 'goal': goal, 'state_key': state_key, 'version': version})
    finally:
        conn.close()


def mark_thinking_project(project_name, db_path=DB_PATH):
    conn = connect(db_path)
    try:
        cur = conn.cursor()
        project_id = get_project_id(cur, project_name)
        existing = cur.execute(
            '''
            select relationship, note
            from project_objects
            where project_id=? and object_type=? and object_key=?
            ''',
            (project_id, THINKING_PROJECT_OBJECT_TYPE, THINKING_PROJECT_OBJECT_KEY),
        ).fetchone()

        cur.execute(
            '''
            insert into project_objects(project_id, object_type, object_key, relationship, note)
            values(?,?,?,?,?)
            on conflict(project_id, object_type, object_key) do update set
                relationship=excluded.relationship,
                note=excluded.note
            ''',
            (
                project_id,
                THINKING_PROJECT_OBJECT_TYPE,
                THINKING_PROJECT_OBJECT_KEY,
                THINKING_PROJECT_RELATIONSHIP,
                THINKING_PROJECT_NOTE,
            ),
        )
        conn.commit()
        changed = existing is None or existing[0] != THINKING_PROJECT_RELATIONSHIP or existing[1] != THINKING_PROJECT_NOTE
        return json.dumps(
            {
                'project_name': project_name,
                'project_id': project_id,
                'object_type': THINKING_PROJECT_OBJECT_TYPE,
                'object_key': THINKING_PROJECT_OBJECT_KEY,
                'relationship': THINKING_PROJECT_RELATIONSHIP,
                'note': THINKING_PROJECT_NOTE,
                'changed': changed,
            }
        )
    finally:
        conn.close()


def run_project_command(argv=None, db_path=DB_PATH):
    argv = list(argv or [])
    if argv[:1] == ['project']:
        argv = argv[1:]
    if not argv:
        raise ValueError('expected: mark-thinking <project_name> | goal set <project_name> <goal>')

    action = argv[0]
    if action == 'mark-thinking':
        if len(argv) < 2:
            raise ValueError('mark-thinking requires a project_name')
        return mark_thinking_project(argv[1], db_path=db_path)
    if action == 'goal':
        if len(argv) < 2 or argv[1] != 'set':
            raise ValueError('expected: goal set <project_name> <goal>')
        if len(argv) < 4:
            raise ValueError('goal set requires a project_name and a goal')
        return set_project_goal(argv[2], ' '.join(argv[3:]), db_path=db_path)
    raise ValueError('expected: mark-thinking <project_name> | goal set <project_name> <goal>')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('args', nargs='*')
    parser.add_argument('--db', default=str(DB_PATH))
    parsed = parser.parse_args()
    print(run_project_command(parsed.args, db_path=Path(parsed.db)))


if __name__ == '__main__':
    main()
