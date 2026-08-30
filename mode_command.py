#!/usr/bin/env python3
import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'continuity.db'

SCIENTIST_FLAG_KEY = 'scientist_mode'
ROLE_STATE_KEY = 'active_role_mode'


def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def ensure_scientist_mode_support(cur):
    cur.execute(
        '''
        INSERT INTO feature_flags(feature_key, enabled, switchable, scope, updated_by)
        VALUES(?,?,?,?,?)
        ON CONFLICT(feature_key) DO UPDATE SET
            switchable=excluded.switchable,
            scope=excluded.scope
        ''',
        (
            SCIENTIST_FLAG_KEY,
            0,
            1,
            'Role-specific scientist mode: structured evidence, hypotheses, uncertainty, and experiments.',
            'system',
        ),
    )
    row = cur.execute("select 1 from metacognitive_state where state_key=?", (ROLE_STATE_KEY,)).fetchone()
    if not row:
        cur.execute(
            '''
            INSERT INTO metacognitive_state(state_key, category, value, confidence, provenance, version)
            VALUES(?,?,?,?,?,?)
            ''',
            (ROLE_STATE_KEY, 'roles', 'general', 1.0, 'system', 1),
        )


def toggle_scientist_mode(conn, enabled, actor='Peter', reason='Explicit mode command'):
    cur = conn.cursor()
    ensure_scientist_mode_support(cur)
    current = cur.execute(
        'select enabled from feature_flags where feature_key=?',
        (SCIENTIST_FLAG_KEY,),
    ).fetchone()[0]
    if current == enabled:
        role = cur.execute(
            'select value from metacognitive_state where state_key=?',
            (ROLE_STATE_KEY,),
        ).fetchone()[0]
        return {
            'feature_key': SCIENTIST_FLAG_KEY,
            'enabled': bool(current),
            'changed': False,
            'active_role_mode': role,
            'message': f'scientist mode already {"on" if enabled else "off"}',
        }

    cur.execute(
        '''
        UPDATE feature_flags
        SET enabled=?, updated_by=?, updated_at=CURRENT_TIMESTAMP
        WHERE feature_key=?
        ''',
        (enabled, actor, SCIENTIST_FLAG_KEY),
    )
    conn.commit()
    role = cur.execute(
        'select value from metacognitive_state where state_key=?',
        (ROLE_STATE_KEY,),
    ).fetchone()[0]
    return {
        'feature_key': SCIENTIST_FLAG_KEY,
        'enabled': bool(enabled),
        'changed': True,
        'active_role_mode': role,
        'message': f'scientist mode {"enabled" if enabled else "disabled"}',
    }


def scientist_status(conn):
    cur = conn.cursor()
    ensure_scientist_mode_support(cur)
    row = cur.execute(
        '''
        select ff.enabled, ff.switchable, ff.updated_by, ff.updated_at,
               ms.value, ms.confidence, ms.version
        from feature_flags ff
        join metacognitive_state ms on ms.state_key=?
        where ff.feature_key=?
        ''',
        (ROLE_STATE_KEY, SCIENTIST_FLAG_KEY),
    ).fetchone()
    if not row:
        raise RuntimeError('scientist mode support missing')
    enabled, switchable, updated_by, updated_at, role_value, role_confidence, role_version = row
    return {
        'feature_key': SCIENTIST_FLAG_KEY,
        'enabled': bool(enabled),
        'switchable': bool(switchable),
        'updated_by': updated_by,
        'updated_at': updated_at,
        'active_role_mode': role_value,
        'active_role_confidence': role_confidence,
        'active_role_version': role_version,
    }


def run_mode_command(argv=None, db_path=DB_PATH):
    argv = list(argv or [])
    if argv[:1] == ['mode']:
        argv = argv[1:]
    if not argv:
        raise ValueError('expected: scientist on|off|status')

    role = argv[0]
    action = argv[1] if len(argv) > 1 else 'status'
    if role != 'scientist':
        raise ValueError('only scientist mode is supported right now')

    conn = connect(db_path)
    try:
        if action == 'on':
            result = toggle_scientist_mode(conn, 1)
        elif action == 'off':
            result = toggle_scientist_mode(conn, 0)
        elif action == 'status':
            result = scientist_status(conn)
            result['changed'] = False
            result['message'] = 'scientist mode status'
        else:
            raise ValueError('expected on, off, or status')
    finally:
        conn.close()

    return json.dumps(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('args', nargs='*')
    parser.add_argument('--db', default=str(DB_PATH))
    parsed = parser.parse_args()
    print(run_mode_command(parsed.args, db_path=Path(parsed.db)))


if __name__ == '__main__':
    main()
