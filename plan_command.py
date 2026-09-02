#!/usr/bin/env python3
import argparse
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'continuity.db'


def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys=ON')
    ensure_plan_schema(conn)
    return conn


def now_stamp():
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(sep=' ', timespec='seconds')


def ensure_plan_schema(conn):
    cur = conn.cursor()
    table = cur.execute("select 1 from sqlite_master where type='table' and name='work_plans'").fetchone()
    if not table:
        return
    cols = [row[1] for row in cur.execute('pragma table_info(work_plans)')]
    if 'prompt' not in cols:
        cur.execute("alter table work_plans add column prompt TEXT NOT NULL DEFAULT ''")
        conn.commit()


def _fetch_state(cur, key):
    return cur.execute(
        'select state_key, category, value, confidence, provenance, version from metacognitive_state where state_key=?',
        (key,),
    ).fetchone()


def upsert_state(cur, state_key, category, value, confidence=0.98, provenance='planning_command'):
    row = _fetch_state(cur, state_key)
    if row is None:
        cur.execute(
            'insert into metacognitive_state(state_key, category, value, confidence, provenance, version) values(?,?,?,?,?,?)',
            (state_key, category, value, confidence, provenance, 1),
        )
        return 1
    if row[2] == value and row[1] == category and float(row[3]) == float(confidence) and row[4] == provenance:
        return row[5]
    cur.execute(
        'update metacognitive_state set category=?, value=?, confidence=?, provenance=?, version=?, updated_at=CURRENT_TIMESTAMP where state_key=?',
        (category, value, confidence, provenance, int(row[5]) + 1, state_key),
    )
    return int(row[5]) + 1


def ensure_journal(cur, category, summary, status='active'):
    cur.execute(
        'insert into journal(category, summary, status) values(?,?,?)',
        (category, summary, status),
    )


def ensure_reasoning_episode(cur, goal, reason, old_goal=None):
    episode_key = f'goal_update_{datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")}_{uuid.uuid4().hex[:8]}'
    evidence = f'Primary goal changed from {old_goal!r} to {goal!r}.' if old_goal else f'Primary goal set to {goal!r}.'
    if reason:
        evidence += f' Reason: {reason}'
    cur.execute(
        '''
        insert into reasoning_episodes(
            episode_key, title, claim, evidence_summary, inference,
            rejected_alternatives, uncertainty, confidence, mode_trail,
            next_action, status, source_mode
        ) values(?,?,?,?,?,?,?,?,?,?,?,?)
        ''',
        (
            episode_key,
            'Update primary goal',
            f'Primary goal should be {goal}',
            evidence,
            'Write the revised goal into persistent planning state and keep the active plan aligned with it.',
            'Do not store the new goal; keep only transient chat context.',
            'The exact downstream plan may need refinement after the new goal is used.',
            0.95,
            'planning',
            'Review current active plan against the revised goal.',
            'active',
            'derived',
        ),
    )
    episode_id = cur.lastrowid
    cur.execute(
        '''
        insert into reasoning_episode_inputs(episode_id, source_type, source_key, relation, weight, note)
        values(?,?,?,?,?,?)
        ''',
        (
            episode_id,
            'metacognitive_state',
            'primary_goal',
            'grounds',
            0.95,
            f'Persistent planning goal update: {goal}',
        ),
    )
    if old_goal:
        cur.execute(
            '''
            insert into reasoning_episode_inputs(episode_id, source_type, source_key, relation, weight, note)
            values(?,?,?,?,?,?)
            ''',
            (
                episode_id,
                'metacognitive_state',
                'primary_goal_previous',
                'refines',
                0.8,
                f'Previous goal was: {old_goal}',
            ),
        )
    return episode_key


def set_primary_goal(conn, goal, reason=None):
    cur = conn.cursor()
    row = _fetch_state(cur, 'primary_goal')
    old_goal = row[2] if row else None
    version = upsert_state(cur, 'primary_goal', 'goals', goal, confidence=0.98, provenance='planning_command')
    if old_goal != goal:
        ensure_journal(cur, 'planning', f'Primary goal set to: {goal}')
        ensure_reasoning_episode(cur, goal, reason or '', old_goal=old_goal)
    conn.commit()
    return version


GENERAL_PLAN_HINTS = {
    'general', 'baseline', 'overview', 'system', 'core', 'default', 'meta', 'shared', 'global', 'always'
}


def _plan_text(title, objective='', prompt=''):
    return ' '.join(part for part in (title, objective, prompt) if part).lower()


def is_general_plan(title, objective='', prompt=''):
    text = _plan_text(title, objective, prompt)
    return any(hint in text for hint in GENERAL_PLAN_HINTS)


def infer_plan_condition(title, objective='', prompt=''):
    if is_general_plan(title, objective, prompt):
        return ''
    clean_title = re.sub(r'\s+', ' ', (title or '').strip()).strip(' .:;-')
    if not clean_title:
        clean_title = re.sub(r'\s+', ' ', (objective or '').strip()).strip(' .:;-')[:80]
    if not clean_title:
        clean_title = 'this plan'
    return f'surface when discussing {clean_title.lower()} or related planning topics'


def start_plan(conn, plan_key, title, objective, prompt='', status='active'):
    cur = conn.cursor()
    cur.execute(
        '''
        insert into work_plans(plan_key, title, objective, prompt, status, created_by)
        values(?,?,?,?,?,?)
        on conflict(plan_key) do update set
            title=excluded.title,
            objective=excluded.objective,
            prompt=excluded.prompt,
            status=excluded.status,
            updated_at=CURRENT_TIMESTAMP
        ''',
        (plan_key, title, objective, prompt, status, 'Peter'),
    )
    row = cur.execute(
        'select 1 from memory_conditions where source_type=? and source_key=?',
        ('work_plan', plan_key),
    ).fetchone()
    if row is None:
        condition = infer_plan_condition(title, objective, prompt)
        if condition:
            cur.execute(
                '''
                insert into memory_conditions(source_type, source_key, condition, updated_at)
                values(?,?,?,CURRENT_TIMESTAMP)
                ''',
                ('work_plan', plan_key, condition),
            )
            ensure_journal(cur, 'planning', f'Auto-conditioned work plan {plan_key}')
    ensure_journal(cur, 'planning', f'Work plan {plan_key} is {status}: {title}')
    conn.commit()
    return plan_key


def _plan_id(cur, plan_key):
    row = cur.execute('select id from work_plans where plan_key=?', (plan_key,)).fetchone()
    if row is None:
        raise ValueError(f'unknown plan_key: {plan_key}')
    return row[0]


def add_step(conn, plan_key, step_key, description):
    cur = conn.cursor()
    plan_id = _plan_id(cur, plan_key)
    row = cur.execute(
        'select id, step_order from work_plan_steps where plan_id=? and step_key=?',
        (plan_id, step_key),
    ).fetchone()
    if row is None:
        next_order = cur.execute(
            'select coalesce(max(step_order), 0) + 1 from work_plan_steps where plan_id=?',
            (plan_id,),
        ).fetchone()[0]
        cur.execute(
            '''
            insert into work_plan_steps(plan_id, step_order, step_key, description, status, evidence)
            values(?,?,?,?,?,?)
            ''',
            (plan_id, next_order, step_key, description, 'pending', ''),
        )
    else:
        cur.execute(
            '''
            update work_plan_steps
            set description=?, status='pending', updated_at=CURRENT_TIMESTAMP
            where id=?
            ''',
            (description, row[0]),
        )
    ensure_journal(cur, 'planning', f'Added step {step_key} to {plan_key}')
    conn.commit()
    return step_key


def set_step_status(conn, plan_key, step_key, status, evidence=''):
    cur = conn.cursor()
    plan_id = _plan_id(cur, plan_key)
    row = cur.execute(
        'select id, status from work_plan_steps where plan_id=? and step_key=?',
        (plan_id, step_key),
    ).fetchone()
    if row is None:
        raise ValueError(f'unknown step_key: {step_key}')
    if status == 'completed':
        cur.execute(
            '''
            update work_plan_steps
            set status=?, evidence=?, completed_at=CURRENT_TIMESTAMP, started_at=coalesce(started_at, CURRENT_TIMESTAMP)
            where id=?
            ''',
            (status, evidence, row[0]),
        )
    else:
        cur.execute(
            '''
            update work_plan_steps
            set status=?, evidence=?, started_at=coalesce(started_at, CURRENT_TIMESTAMP)
            where id=?
            ''',
            (status, evidence, row[0]),
        )
    if status == 'completed':
        ensure_journal(cur, 'planning', f'Completed step {step_key} in {plan_key}')
    conn.commit()
    return status


def block_step(conn, plan_key, step_key, question):
    cur = conn.cursor()
    set_step_status(conn, plan_key, step_key, 'pending', evidence=f'Blocked by question: {question}')
    cur = conn.cursor()
    cur.execute(
        'insert into open_questions(question, status, resolution_note) values(?,?,?)',
        (question, 'open', ''),
    )
    ensure_journal(cur, 'planning', f'Step {step_key} in {plan_key} blocked by open question')
    conn.commit()
    return question


def _words(text):
    return set(re.findall(r"[A-Za-z][A-Za-z0-9_'-]+", (text or '').lower()))


def _plan_priority_score(plan, goal_words=None, focus_words=None, aspect_words=None):
    goal_words = goal_words or set()
    focus_words = focus_words or set()
    aspect_words = aspect_words or set()
    text_words = _words(plan['title']) | _words(plan['objective']) | _words(plan.get('prompt', ''))
    overlap = (
        len(text_words & goal_words) * 5
        + len(text_words & focus_words) * 3
        + len(text_words & aspect_words) * 4
    )
    active_bonus = 100 if plan['status'] == 'active' else 0
    recent_bonus = 0
    if plan.get('updated_at'):
        recent_bonus = int(plan['updated_at'].replace('-', '').replace(':', '').replace(' ', '')[:14] or 0)
    step_bonus = min(len(plan.get('steps') or []), 7)
    return active_bonus + overlap + step_bonus, recent_bonus


def planning_status(conn):
    cur = conn.cursor()
    goal_row = cur.execute(
        "select value, confidence, version, updated_at from metacognitive_state where state_key='primary_goal'"
    ).fetchone()
    focus_row = cur.execute(
        "select value, confidence, version, updated_at from metacognitive_state where state_key='current_focus'"
    ).fetchone()
    aspect_row = cur.execute(
        "select value, confidence, version, updated_at from metacognitive_state where state_key='current_aspect'"
    ).fetchone()
    goal_words = _words(goal_row[0]) if goal_row else set()
    focus_words = _words(focus_row[0]) if focus_row else set()
    aspect_words = _words(aspect_row[0]) if aspect_row else set()
    plans = []
    for plan in cur.execute(
        "select id, plan_key, title, objective, prompt, status, created_at, updated_at from work_plans where status='active'"
    ).fetchall():
        steps = [
            {
                'step_order': row[0],
                'step_key': row[1],
                'description': row[2],
                'status': row[3],
                'evidence': row[4],
            }
            for row in cur.execute(
                '''
                select step_order, step_key, description, status, coalesce(evidence, '')
                from work_plan_steps
                where plan_id=?
                order by step_order
                ''',
                (plan[0],),
            ).fetchall()
        ]
        plan_dict = {
            'plan_key': plan[1],
            'title': plan[2],
            'objective': plan[3],
            'prompt': plan[4],
            'status': plan[5],
            'created_at': plan[6],
            'updated_at': plan[7],
            'steps': steps,
        }
        score, recency = _plan_priority_score(
            plan_dict,
            goal_words=goal_words,
            focus_words=focus_words,
            aspect_words=aspect_words,
        )
        plan_dict['priority_score'] = score
        plan_dict['_recency'] = recency
        plans.append(plan_dict)
    plans.sort(key=lambda p: (p['priority_score'], p['_recency'], p['updated_at'], p['plan_key']), reverse=True)
    for plan in plans:
        plan.pop('_recency', None)
    blockers = [
        {
            'id': row[0],
            'question': row[1],
            'status': row[2],
            'created_at': row[3],
        }
        for row in cur.execute(
            "select id, question, status, created_at from open_questions where status in ('open','deferred','partially_answered') order by created_at desc, id desc limit 10"
        ).fetchall()
    ]
    return {
        'primary_goal': None if goal_row is None else {
            'value': goal_row[0],
            'confidence': goal_row[1],
            'version': goal_row[2],
            'updated_at': goal_row[3],
        },
        'current_focus': None if focus_row is None else {
            'value': focus_row[0],
            'confidence': focus_row[1],
            'version': focus_row[2],
            'updated_at': focus_row[3],
        },
        'current_aspect': None if aspect_row is None else {
            'value': aspect_row[0],
            'confidence': aspect_row[1],
            'version': aspect_row[2],
            'updated_at': aspect_row[3],
        },
        'active_plans': plans,
        'blockers': blockers,
    }


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)

    status_p = sub.add_parser('status')
    status_p.add_argument('--db', default=str(DB_PATH))

    goal_p = sub.add_parser('goal')
    goal_sub = goal_p.add_subparsers(dest='action', required=True)
    goal_set = goal_sub.add_parser('set')
    goal_set.add_argument('text')
    goal_set.add_argument('--reason', default='')
    goal_set.add_argument('--db', default=str(DB_PATH))

    plan_p = sub.add_parser('plan')
    plan_sub = plan_p.add_subparsers(dest='action', required=True)
    plan_start = plan_sub.add_parser('start')
    plan_start.add_argument('plan_key')
    plan_start.add_argument('title')
    plan_start.add_argument('objective')
    plan_start.add_argument('--prompt', default='')
    plan_start.add_argument('--status', default='active')
    plan_start.add_argument('--db', default=str(DB_PATH))

    step_p = sub.add_parser('step')
    step_sub = step_p.add_subparsers(dest='action', required=True)
    step_add = step_sub.add_parser('add')
    step_add.add_argument('plan_key')
    step_add.add_argument('step_key')
    step_add.add_argument('description')
    step_add.add_argument('--db', default=str(DB_PATH))

    step_done = step_sub.add_parser('done')
    step_done.add_argument('plan_key')
    step_done.add_argument('step_key')
    step_done.add_argument('--evidence', default='')
    step_done.add_argument('--db', default=str(DB_PATH))

    step_block = step_sub.add_parser('block')
    step_block.add_argument('plan_key')
    step_block.add_argument('step_key')
    step_block.add_argument('question')
    step_block.add_argument('--db', default=str(DB_PATH))

    args = parser.parse_args()

    if args.command == 'status':
        conn = connect(Path(args.db))
        try:
            print(json.dumps(planning_status(conn)))
        finally:
            conn.close()
    elif args.command == 'goal' and args.action == 'set':
        conn = connect(Path(args.db))
        try:
            print(json.dumps({'primary_goal_version': set_primary_goal(conn, args.text, reason=args.reason)}))
        finally:
            conn.close()
    elif args.command == 'plan' and args.action == 'start':
        conn = connect(Path(args.db))
        try:
            print(json.dumps({'plan_key': start_plan(conn, args.plan_key, args.title, args.objective, prompt=args.prompt, status=args.status)}))
        finally:
            conn.close()
    elif args.command == 'step' and args.action == 'add':
        conn = connect(Path(args.db))
        try:
            print(json.dumps({'step_key': add_step(conn, args.plan_key, args.step_key, args.description)}))
        finally:
            conn.close()
    elif args.command == 'step' and args.action == 'done':
        conn = connect(Path(args.db))
        try:
            print(json.dumps({'status': set_step_status(conn, args.plan_key, args.step_key, 'completed', evidence=args.evidence)}))
        finally:
            conn.close()
    elif args.command == 'step' and args.action == 'block':
        conn = connect(Path(args.db))
        try:
            print(json.dumps({'question': block_step(conn, args.plan_key, args.step_key, args.question)}))
        finally:
            conn.close()
    else:
        raise SystemExit('unsupported command')


if __name__ == '__main__':
    main()
