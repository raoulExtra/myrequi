#!/usr/bin/env python3
"""Set the active phase for a project."""
import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'continuity.db'

PHASES = {
    1: 'Frame',
    2: 'Elicit',
    3: 'Analyze',
    4: 'Specify',
    5: 'Validate',
    6: 'Manage',
}


def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def get_project_by_name(conn, name):
    row = conn.execute(
        'SELECT id, project_name, active_phase FROM projects WHERE project_name=?',
        (name,),
    ).fetchone()
    if not row:
        raise ValueError(f"Project not found: {name!r}")
    return row


def set_phase(conn, project_name, phase, actor='system', reason=''):
    """Set active_phase for a project. phase can be int or phase name."""
    if isinstance(phase, str):
        phase = phase.strip()
        # Accept name or number
        if phase.isdigit():
            phase = int(phase)
        else:
            # Match phase by name (case-insensitive)
            matched = {v.lower(): k for k, v in PHASES.items()}.get(phase.lower())
            if matched is None:
                valid = ', '.join(f"{k}={v}" for k, v in PHASES.items())
                raise ValueError(f"Unknown phase {phase!r}. Valid: {valid}")
            phase = matched

    if phase not in PHASES:
        valid = ', '.join(f"{k}={v}" for k, v in PHASES.items())
        raise ValueError(f"Phase must be 1-6. Valid: {valid}")

    row = get_project_by_name(conn, project_name)
    project_id, proj_name, prev_phase = row

    if prev_phase == phase:
        return {
            'project': proj_name,
            'previous_phase': prev_phase,
            'new_phase': phase,
            'phase_name': PHASES[phase],
            'changed': False,
            'message': f"Project {proj_name!r} already at phase {phase} ({PHASES[phase]})",
        }

    conn.execute(
        'UPDATE projects SET active_phase=?, updated_by=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',
        (phase, actor, project_id),
    )
    conn.commit()
    return {
        'project': proj_name,
        'previous_phase': prev_phase,
        'new_phase': phase,
        'phase_name': PHASES[phase],
        'changed': True,
        'message': f"Project {proj_name!r} moved from phase {prev_phase} ({PHASES[prev_phase]}) → {phase} ({PHASES[phase]})",
    }


def run_set_phase(argv=None, db_path=DB_PATH):
    parser = argparse.ArgumentParser(description='Set a project\'s active phase.')
    parser.add_argument('project', nargs='?', help='Project name')
    parser.add_argument('phase', nargs='?', help='Phase: 1-6 or name')
    parser.add_argument('--project', dest='project_flag', default=None, help='Project name')
    parser.add_argument('--phase', dest='phase_flag', default=None, help='Phase')
    parser.add_argument('--db', default=str(DB_PATH))
    parsed = parser.parse_args(argv)
    if parsed.project_flag: parsed.project = parsed.project_flag
    if parsed.phase_flag: parsed.phase = parsed.phase_flag
    if not parsed.project or not parsed.phase:
        parser.error('project and phase required')
        parser.error('project and phase required (e.g. set demo 3)')

    conn = connect(Path(parsed.db))
    try:
        result = set_phase(conn, parsed.project, parsed.phase, actor=getattr(parsed, 'actor', 'system'), reason=getattr(parsed, 'reason', ''))
    finally:
        conn.close()

    print(json.dumps(result))
    return result


if __name__ == '__main__':
    run_set_phase()

def get_active_project(conn) -> str | None:
    """Query the active/current project from the projects table only."""
    row = conn.execute(
        "SELECT project_name FROM projects WHERE local_active = 1 ORDER BY updated_at DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else None
