#!/usr/bin/env python3
import argparse
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'continuity.db'


def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def tokenize(text):
    return [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9_'-]+", text)]


def ensure_memory_index_view(cur):
    cur.execute('DROP VIEW IF EXISTS v_memory_index')
    cur.execute(
        '''
        CREATE VIEW v_memory_index AS
        SELECT 'belief' AS source_type, CAST(id AS TEXT) AS source_key, slug AS title,
               current_statement AS body, confidence, current_version AS version, updated_at AS recorded_at
        FROM beliefs
        UNION ALL SELECT 'decision', CAST(id AS TEXT), decision,
               rationale_summary || COALESCE(' ' || uncertainty, ''), NULL, NULL, created_at
        FROM decisions
        UNION ALL SELECT 'open_question', CAST(id AS TEXT), question,
               status, NULL, NULL, created_at
        FROM open_questions
        UNION ALL SELECT 'journal', CAST(id AS TEXT), category || ': ' || summary,
               summary, NULL, NULL, created_at
        FROM journal
        UNION ALL SELECT 'observation', CAST(id AS TEXT), source,
               observation, reliability, NULL, created_at
        FROM observations
        UNION ALL SELECT 'metacognitive_state', state_key, state_key,
               value, confidence, version, updated_at
        FROM metacognitive_state
        UNION ALL SELECT 'continuity_requirement', requirement_key, title,
               statement || ' ' || rationale || ' ' || acceptance_summary, confidence, current_version, updated_at
        FROM continuity_requirements
        WHERE status='active'
        UNION ALL SELECT 'concept', concept_key, name,
               description, confidence, NULL, updated_at
        FROM concepts
        UNION ALL SELECT 'concept_link', CAST(id AS TEXT), concept_key || ' → ' || object_type || ':' || object_key,
               relation || ': ' || note, NULL, NULL, created_at
        FROM concept_links
        UNION ALL SELECT 'ethical_principle', principle_key, principle_key,
               statement || ' ' || rationale, NULL, NULL, created_at
        FROM ethical_principles
        WHERE status='active'
        UNION ALL SELECT 'ethical_conflict_rule', CAST(priority AS TEXT), rule,
               explanation, NULL, NULL, NULL
        FROM ethical_conflict_rules
        UNION ALL SELECT 'tool_guide', CAST(id AS TEXT), tool_name || ': ' || title,
               command || COALESCE(char(10) || explanation, '') || COALESCE(char(10) || safety_note, ''), NULL, NULL, created_at
        FROM tool_command_guide
        UNION ALL SELECT 'work_plan', plan_key, title,
               objective || ' ' || status, NULL, NULL, created_at
        FROM work_plans
        UNION ALL SELECT 'work_plan_step', CAST(s.id AS TEXT), p.plan_key || ' #' || CAST(s.step_order AS TEXT) || ' ' || s.step_key,
               s.description || COALESCE(' ' || s.evidence, ''), NULL, NULL, COALESCE(s.started_at, s.completed_at)
        FROM work_plan_steps s
        JOIN work_plans p ON p.id = s.plan_id
        UNION ALL SELECT 'project', project_name, display_name,
               description || ' ' || CASE WHEN local_active=1 THEN 'active' ELSE 'inactive' END, NULL, NULL, created_at
        FROM projects
        UNION ALL SELECT 'research_job', CAST(id AS TEXT), query,
               COALESCE(result_summary, '') || COALESCE(' ' || error, ''), NULL, NULL, requested_at
        FROM research_jobs
        UNION ALL SELECT 'synthesis', synthesis_key, topic,
               summary || COALESCE(' ' || claim, ''), confidence, NULL, updated_at
        FROM syntheses
        UNION ALL SELECT 'synthesis_conflict', CAST(c.id AS TEXT), s.synthesis_key || ': ' || c.issue,
               c.resolution_note || COALESCE(' ' || c.issue, ''), NULL, NULL, c.created_at
        FROM synthesis_conflicts c JOIN syntheses s ON s.id = c.synthesis_id
        ORDER BY recorded_at DESC
        '''
    )


def ensure_support(conn):
    cur = conn.cursor()
    ensure_memory_index_view(cur)
    conn.commit()


def score_hit(query_tokens, row):
    text = ' '.join(str(x or '') for x in row.values()).lower()
    counts = Counter(query_tokens)
    score = 0
    for token, weight in counts.items():
        if token in text:
            score += weight
    if row['source_type'] in ('belief', 'synthesis') and query_tokens and any(t in row['title'].lower() for t in query_tokens):
        score += 2
    if row['source_type'] == 'metacognitive_state' and any(t in row['source_key'].lower() for t in query_tokens):
        score += 1
    return score


def retrieve_memory(query, db_path=DB_PATH, limit=5):
    conn = connect(db_path)
    try:
        ensure_support(conn)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = cur.execute(
            'select source_type, source_key, title, body, confidence, version, recorded_at from v_memory_index'
        ).fetchall()
        qtokens = tokenize(query)
        scored = []
        for row in rows:
            row = dict(row)
            score = score_hit(qtokens, row)
            if score > 0:
                scored.append((score, row))
        scored.sort(key=lambda item: (item[0], str(item[1].get('recorded_at', ''))), reverse=True)
        hits = []
        for score, row in scored[:limit]:
            hits.append({
                'score': score,
                'source_type': row['source_type'],
                'source_key': row['source_key'],
                'title': row['title'],
                'body': row['body'],
                'confidence': row['confidence'],
                'version': row['version'],
                'recorded_at': row['recorded_at'],
            })
        return {'query': query, 'hit_count': len(hits), 'hits': hits}
    finally:
        conn.close()


def run_memory_recall(query, db_path=DB_PATH, limit=5):
    return json.dumps(retrieve_memory(query, db_path=db_path, limit=limit))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['recall'])
    parser.add_argument('query')
    parser.add_argument('--db', default=str(DB_PATH))
    parser.add_argument('--limit', type=int, default=5)
    args = parser.parse_args()
    print(run_memory_recall(args.query, db_path=Path(args.db), limit=args.limit))


if __name__ == '__main__':
    main()
