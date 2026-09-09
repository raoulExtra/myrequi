#!/usr/bin/env python3
import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
DB_PATH = ROOT / 'continuity.db'
__version__ = '0.0.0-placeholder'


def get_version():
    return __version__


def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def tokenize(text):
    return [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9_'-]+", text)]


def ensure_memory_conditions_table(cur):
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS memory_conditions (
            source_type TEXT NOT NULL,
            source_key TEXT NOT NULL,
            condition TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source_type, source_key)
        )
        '''
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_conditions_condition ON memory_conditions(condition)")


def ensure_work_plan_prompt_column(cur):
    table = cur.execute("select 1 from sqlite_master where type='table' and name='work_plans'").fetchone()
    if not table:
        return
    cols = [row[1] for row in cur.execute('pragma table_info(work_plans)')]
    if 'prompt' not in cols:
        cur.execute("alter table work_plans add column prompt TEXT NOT NULL DEFAULT ''")


def ensure_memory_index_view(cur):
    cur.execute('DROP VIEW IF EXISTS v_memory_index')
    cur.execute(
        '''
        CREATE VIEW v_memory_index AS
        SELECT 'belief' AS source_type, CAST(id AS TEXT) AS source_key, slug AS title,
               current_statement AS body, confidence, current_version AS version, updated_at AS recorded_at
        FROM beliefs
        UNION ALL SELECT 'belief_version', CAST(bv.id AS TEXT), COALESCE(b.slug, CAST(bv.belief_id AS TEXT)),
               bv.statement, bv.confidence, bv.version, bv.created_at
        FROM belief_versions bv
        LEFT JOIN beliefs b ON b.id = bv.belief_id
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
        UNION ALL SELECT 'concept_search', concept_key || ':search', name,
               description || COALESCE(char(10) || 'Links: ' || linked_items, '') || COALESCE(char(10) || 'Tags: ' || tagged_terms, ''), confidence, NULL, updated_at
        FROM v_concept_search
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
               COALESCE(prompt || char(10), '') || objective || ' ' || status, NULL, NULL, created_at
        FROM work_plans
        UNION ALL SELECT 'work_plan_step', CAST(s.id AS TEXT), p.plan_key || ' #' || CAST(s.step_order AS TEXT) || ' ' || s.step_key,
               s.description || COALESCE(' ' || s.evidence, ''), NULL, NULL, COALESCE(s.started_at, s.completed_at)
        FROM work_plan_steps s
        JOIN work_plans p ON p.id = s.plan_id
        UNION ALL SELECT 'project', project_name, display_name,
               description || ' ' || CASE WHEN local_active=1 THEN 'active' ELSE 'inactive' END, NULL, NULL, created_at
        FROM projects
        UNION ALL SELECT 'code_artifact', ca.name, ca.name,
               ca.description || COALESCE(' ' || cv.approval_status, ''), NULL, cv.version, ca.updated_at
        FROM code_artifacts ca
        JOIN code_versions cv ON cv.artifact_id = ca.id AND cv.version = ca.active_version
        UNION ALL SELECT 'code_version', CAST(cv.id AS TEXT), ca.name || ' v' || cv.version,
               cv.source || COALESCE(' ' || cv.validation_notes, '') || ' ' || cv.approval_status, NULL, cv.version, cv.created_at
        FROM code_versions cv
        JOIN code_artifacts ca ON ca.id = cv.artifact_id
        UNION ALL SELECT 'research_job', CAST(id AS TEXT), query,
               COALESCE(result_summary, '') || COALESCE(' ' || error, ''), NULL, NULL, requested_at
        FROM research_jobs
        UNION ALL SELECT 'epistemic_receipt', CAST(receipt_id AS TEXT), object_type || ':' || object_key,
               change_summary || COALESCE(' | provenance=' || provenance_json, '') || COALESCE(' | kind=' || receipt_kind, '') || COALESCE(' | complete=' || CAST(provenance_complete AS TEXT), ''),
               confidence, NULL, recorded_at
        FROM epistemic_receipts
        UNION ALL SELECT 'synthesis', synthesis_key, topic,
               summary || COALESCE(' ' || claim, ''), confidence, NULL, updated_at
        FROM syntheses
        WHERE status='active'
        UNION ALL SELECT 'synthesis_conflict', CAST(c.id AS TEXT), s.synthesis_key || ': ' || c.issue,
               c.resolution_note || COALESCE(' ' || c.issue, ''), NULL, NULL, c.created_at
        FROM synthesis_conflicts c JOIN syntheses s ON s.id = c.synthesis_id
        WHERE s.status='active'
        ORDER BY recorded_at DESC
        '''
    )


def ensure_support(conn):
    cur = conn.cursor()
    ensure_memory_conditions_table(cur)
    ensure_work_plan_prompt_column(cur)
    ensure_memory_index_view(cur)
    conn.commit()


SOURCE_LAYER = {
    'decision': 'episodic',
    'belief_version': 'semantic',
    'decision_version': 'episodic',
    'journal': 'episodic',
    'observation': 'episodic',
    'open_question': 'episodic',
    'reasoning_episode': 'episodic',
    'belief': 'semantic',
    'belief_version': 'semantic',
    'concept': 'semantic',
    'concept_search': 'semantic',
    'continuity_requirement': 'semantic',
    'ethical_conflict_rule': 'semantic',
    'ethical_principle': 'semantic',
    'synthesis': 'semantic',
    'synthesis_conflict': 'semantic',
    'tool_guide': 'procedural',
    'code_artifact': 'procedural',
    'code_version': 'procedural',
    'work_plan': 'procedural',
    'work_plan_step': 'procedural',
    'project': 'procedural',
    'research_job': 'procedural',
    'metacognitive_state': 'metacognitive',
}


def layer_for_source(source_type):
    return SOURCE_LAYER.get(source_type, 'semantic')


LAYER_PRIORITY = {
    'semantic': 3,
    'episodic': 2,
    'procedural': 1,
    'metacognitive': 0,
}


def recency_bonus(recorded_at):
    if not recorded_at:
        return 0.0
    try:
        stamp = datetime.fromisoformat(str(recorded_at).replace('Z', '+00:00'))
    except ValueError:
        return 0.0
    now = datetime.now(timezone.utc)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    age_seconds = max(0.0, (now - stamp).total_seconds())
    return max(0.0, 1.0 - min(age_seconds / (60.0 * 60.0 * 24.0 * 90.0), 1.0))


def score_hit(query_tokens, row):
    text = ' '.join(str(x or '') for x in row.values()).lower()
    counts = Counter(query_tokens)
    overlap = 0
    for token, weight in counts.items():
        if token in text:
            overlap += weight
    title = str(row.get('title') or '').lower()
    body = str(row.get('body') or '').lower()
    condition = str(row.get('condition') or '').lower()
    source_key = str(row.get('source_key') or '').lower()
    source_type = str(row.get('source_type') or '').lower()
    if query_tokens and any(t in title for t in query_tokens):
        overlap += 2
    if query_tokens and any(t in body for t in query_tokens):
        overlap += 1
    if query_tokens and any(t in condition for t in query_tokens):
        overlap += 1
    if query_tokens and any(t in source_key for t in query_tokens):
        overlap += 1
    confidence = float(row.get('confidence') or 0.0)
    if source_type in ('code_artifact', 'code_version'):
        # Derive confidence from embedded approval/validation text in body
        body_text = str(row.get('body') or '').lower()
        if 'approved' in body_text and 'failed' not in body_text:
            confidence = 1.0
        elif 'pending' in body_text:
            confidence = 0.6
        elif 'failed' in body_text or 'rejected' in body_text:
            confidence = 0.05
        else:
            confidence = 0.35
    elif confidence <= 0:
        confidence = 0.35
    score = overlap + confidence + recency_bonus(row.get('recorded_at'))
    if source_type == 'epistemic_receipt':
        score += 1.25
    if source_type == 'metacognitive_state' and query_tokens and any(t in source_key for t in query_tokens):
        score += 1.0
    return score


def load_memory_rows(cur):
    try:
        rows = cur.execute(
            '''
            select p.memory_layer, p.source_type, p.source_key, p.title, p.body,
                   COALESCE(mc.condition, '') as condition, p.confidence, p.version, p.recorded_at
            from v_memory_packet p
            left join memory_conditions mc
              on mc.source_type = p.source_type and mc.source_key = p.source_key
            '''
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        rows = cur.execute(
            '''
            select i.source_type, i.source_key, i.title, i.body,
                   COALESCE(mc.condition, '') as condition, i.confidence, i.version, i.recorded_at
            from v_memory_index i
            left join memory_conditions mc
              on mc.source_type = i.source_type and mc.source_key = i.source_key
            '''
        ).fetchall()
        return [
            {**dict(r), 'memory_layer': layer_for_source(r['source_type'])}
            for r in rows
        ]


def load_writeback_policy(cur):
    try:
        rows = cur.execute(
            'select policy_trigger, enabled, description, storage_policy_version, policy_summary from v_writeback_policy order by policy_trigger'
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        rows = cur.execute(
            'select trigger as policy_trigger, enabled, description from recording_policy where enabled=1 order by trigger'
        ).fetchall()
        return [dict(r) for r in rows]


def layer_priority(layer):
    return LAYER_PRIORITY.get(layer, -1)


def build_working_packet(query, hits, focus=None, policy=None):
    sections = defaultdict(list)
    active_claims = []
    evidence = []
    open_questions = []
    next_actions = []
    conflicts = []

    for hit in hits:
        layer = hit.get('memory_layer') or layer_for_source(hit.get('source_type'))
        compact = {
            'source_type': hit.get('source_type'),
            'source_key': hit.get('source_key'),
            'title': hit.get('title'),
            'condition': hit.get('condition'),
            'confidence': hit.get('confidence'),
            'recorded_at': hit.get('recorded_at'),
            'score': hit.get('score'),
        }
        sections[layer].append(compact)
        if layer == 'semantic':
            active_claims.append(compact)
        elif layer == 'episodic':
            evidence.append(compact)
            if hit.get('source_type') == 'open_question':
                open_questions.append(compact)
        elif layer == 'procedural':
            next_actions.append(compact)
        elif layer == 'metacognitive':
            conflicts.append(compact)

    return {
        'query': query,
        'focus': focus,
        'sections': {k: v for k, v in sections.items()},
        'active_claims': active_claims,
        'evidence': evidence,
        'open_questions': open_questions,
        'next_actions': next_actions,
        'conflicts': conflicts,
        'policy': policy or [],
    }


def retrieve_memory(query, db_path=DB_PATH, limit=5, layer=None):
    conn = connect(db_path)
    try:
        ensure_support(conn)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = load_memory_rows(cur)
        requested_layer = layer.lower() if layer else None
        focus_row = cur.execute(
            "select value from metacognitive_state where state_key in ('current_focus', 'primary_goal') order by case state_key when 'current_focus' then 0 else 1 end limit 1"
        ).fetchone()
        policy_rows = load_writeback_policy(cur)
        qtokens = tokenize(query)
        scored = []
        for row in rows:
            if requested_layer and (row.get('memory_layer') or layer_for_source(row.get('source_type'))) != requested_layer:
                continue
            score = score_hit(qtokens, row)
            if score > 0:
                scored.append((score, row))
        scored.sort(
            key=lambda item: (
                item[0],
                layer_priority(item[1].get('memory_layer') or layer_for_source(item[1].get('source_type'))),
                float(item[1].get('confidence') or 0.0),
                str(item[1].get('recorded_at') or ''),
            ),
            reverse=True,
        )
        hits = []
        for score, row in scored[:limit]:
            row = dict(row)
            row['score'] = round(score, 3)
            # Derive visible confidence for procedural/code rows
            if row.get('source_type') in ('code_artifact', 'code_version'):
                bt = str(row.get('body') or '').lower()
                if 'approved' in bt and 'failed' not in bt:
                    row['confidence'] = 1.0
                elif 'pending' in bt:
                    row['confidence'] = 0.6
                elif 'failed' in bt or 'rejected' in bt:
                    row['confidence'] = 0.05
                else:
                    row['confidence'] = 0.35
            hits.append(row)
        return {
            'query': query,
            'layer': requested_layer,
            'hit_count': len(hits),
            'hits': hits,
            'working_packet': build_working_packet(
                query,
                hits,
                focus=focus_row[0] if focus_row else None,
                policy=policy_rows,
            ),
        }
    finally:
        conn.close()


def retrieve_table_context(query, db_path=DB_PATH, limit=5):
    """Return table metadata first when the query appears to refer to an existing table."""
    conn = connect(db_path)
    try:
        ensure_support(conn)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        q = re.sub(r'\s+', ' ', (query or '')).strip().strip(' ?!.,;:\t\n\r')
        if not q:
            return {'query': q, 'hit_count': 0, 'tables': []}
        like = f'%{q}%'
        rows = cur.execute(
            '''
            SELECT s.name AS table_name, COALESCE(c.role, 'table') AS role,
                   COALESCE(c.write_mode, 'mutable') AS write_mode,
                   COALESCE(c.paired_table, '') AS paired_table,
                   COALESCE(c.notes, '') AS notes,
                   COALESCE(w.row_count, 0) AS row_count,
                   COALESCE(w.last_changed_at, '') AS last_changed_at,
                   CASE
                       WHEN lower(s.name) = lower(?) THEN 0
                       WHEN lower(s.name) LIKE lower(?) THEN 1
                       WHEN lower(?) LIKE '%' || lower(s.name) || '%' THEN 2
                       ELSE 3
                   END AS rank
            FROM sqlite_master s
            LEFT JOIN continuity_table_contracts c ON c.table_name = s.name
            LEFT JOIN workspace_table_stats w ON w.table_name = s.name
            WHERE s.type IN ('table', 'view')
              AND (
                   lower(s.name) = lower(?)
                   OR lower(s.name) LIKE lower(?)
                   OR lower(?) LIKE '%' || lower(s.name) || '%'
              )
            ORDER BY rank, s.name
            LIMIT ?
            ''',
            (q, like, q, q, like, q, limit),
        ).fetchall()
        tables = []
        for row in rows:
            table_name = row['table_name']
            write_mode = row['write_mode']
            commands = [
                f"SELECT * FROM {table_name} LIMIT 10;",
                f"SELECT * FROM {table_name};",
                f"PRAGMA table_info({table_name});",
                f"SELECT count(*) FROM {table_name};",
            ]
            if write_mode == 'mutable':
                commands.extend([
                    f"INSERT INTO {table_name} (...) VALUES (...);",
                    f"UPDATE {table_name} SET ... WHERE ...;",
                    f"DELETE FROM {table_name} WHERE ...;",
                ])
            elif write_mode == 'append_only':
                commands.append(f"INSERT INTO {table_name} (...) VALUES (...);")
            tables.append({
                'table_name': table_name,
                'role': row['role'],
                'write_mode': write_mode,
                'paired_table': row['paired_table'],
                'notes': row['notes'],
                'row_count': row['row_count'],
                'last_changed_at': row['last_changed_at'],
                'commands': commands,
            })
        return {
            'query': q,
            'hit_count': len(tables),
            'tables': tables,
        }
    finally:
        conn.close()


def format_table_context(packet):
    query = packet.get('query') or ''
    tables = packet.get('tables') or []
    lines = [f"Table recall: {query}  (hits: {len(tables)})"]
    if not tables:
        lines.append('No matching tables found.')
        return '\n'.join(lines)
    lines.append('')
    for idx, table in enumerate(tables, start=1):
        lines.append(f"{idx}. {table.get('table_name')} [{table.get('role')}/{table.get('write_mode')}]")
        meta = []
        if table.get('row_count') is not None:
            meta.append(f"rows={table.get('row_count')}")
        if table.get('paired_table'):
            meta.append(f"pair={table.get('paired_table')}")
        if table.get('last_changed_at'):
            meta.append(f"updated={table.get('last_changed_at')}")
        if meta:
            lines.append('   ' + ' | '.join(meta))
        notes = _one_line(table.get('notes') or '', 160)
        if notes:
            lines.append(f"   {notes}")
        lines.append('   Commands:')
        for n, cmd in enumerate(table.get('commands') or [], start=1):
            if n in (5, 6) and ('UPDATE ' in cmd or 'DELETE FROM' in cmd):
                cmd = f"{cmd} [refine target rows first, then confirm exact SQL before exec]"
            lines.append(f"     {n}. {cmd}")
    lines.append('Before showing exact SQL for destructive commands, refine the target query/filter first.')
    lines.append('Choose a table and command number if you want me to run one.')
    return '\n'.join(lines)


def run_memory_recall(query, db_path=DB_PATH, limit=5, layer=None):
    return json.dumps(retrieve_memory(query, db_path=db_path, limit=limit, layer=layer))


def _one_line(text, max_len=180):
    text = re.sub(r'\s+', ' ', str(text or '')).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + '…'


def format_memory_recall(packet):
    """Render a recall packet as compact, readable terminal output."""
    query = packet.get('query') or ''
    layer = packet.get('layer') or 'all'
    hits = packet.get('hits') or []
    lines = [f"Memory recall: {query}  (layer: {layer}, hits: {len(hits)})"]

    focus = ((packet.get('working_packet') or {}).get('focus') or '').strip()
    if focus:
        lines.append(f"Focus: {_one_line(focus, 140)}")

    if not hits:
        lines.append("No matching memory items found.")
        return '\n'.join(lines)

    lines.append("")
    for idx, hit in enumerate(hits, start=1):
        source_type = hit.get('source_type') or '?'
        source_key = hit.get('source_key') or '?'
        title = _one_line(hit.get('title') or source_key, 120)
        score = hit.get('score')
        confidence = hit.get('confidence')
        recorded_at = hit.get('recorded_at') or ''
        layer_name = hit.get('memory_layer') or layer_for_source(source_type)
        meta = [layer_name, f"{source_type}:{source_key}"]
        if score is not None:
            meta.append(f"score={score}")
        if confidence is not None:
            meta.append(f"conf={confidence}")
        if recorded_at:
            meta.append(f"at={recorded_at}")
        lines.append(f"{idx}. {title}")
        lines.append(f"   {' | '.join(str(x) for x in meta)}")
        body = _one_line(hit.get('body'), 240)
        if body:
            lines.append(f"   {body}")
        condition = _one_line(hit.get('condition'), 180)
        if condition:
            lines.append(f"   condition: {condition}")

    working_packet = packet.get('working_packet') or {}
    sections = working_packet.get('sections') or {}
    if sections:
        counts = ', '.join(f"{name}={len(items)}" for name, items in sorted(sections.items()))
        lines.extend(["", f"Sections: {counts}"])
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['recall'])
    parser.add_argument('query')
    parser.add_argument('--db', default=str(DB_PATH))
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--layer', choices=['episodic', 'semantic', 'procedural', 'metacognitive'])
    parser.add_argument('--format', choices=['pretty', 'json'], default='pretty')
    args = parser.parse_args()
    packet = retrieve_memory(args.query, db_path=Path(args.db), limit=args.limit, layer=args.layer)
    if args.format == 'json':
        print(json.dumps(packet))
    else:
        print(format_memory_recall(packet))


if __name__ == '__main__':
    main()
