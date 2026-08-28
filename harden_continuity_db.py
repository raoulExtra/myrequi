#!/usr/bin/env python3
import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "continuity.db"

PRIMARY_PROVENANCE_LIMIT = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_object_provenance_one_primary
ON object_provenance(metadata_id)
WHERE role='primary'
"""

RECEIPT_KIND_VALUES = {
    "object": "object",
    "snapshot": "snapshot",
    "provenance-attached": "provenance",
    "provenance-removed": "provenance",
    "provenance-revised": "provenance",
}


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def column_names(cur, table):
    return [row[1] for row in cur.execute(f"pragma table_info({table})")]


def add_receipt_kind_column(cur):
    cols = column_names(cur, "epistemic_receipts")
    if "receipt_kind" not in cols:
        cur.execute(
            "ALTER TABLE epistemic_receipts ADD COLUMN receipt_kind TEXT NOT NULL DEFAULT 'object'"
        )


def add_action_check_principle_column(cur):
    cols = column_names(cur, "ethical_action_checks")
    if "principle_key" not in cols:
        cur.execute(
            "ALTER TABLE ethical_action_checks ADD COLUMN principle_key TEXT REFERENCES ethical_principles(principle_key)"
        )


def patch_provenance_trigger(cur, trigger_name):
    row = cur.execute(
        "select sql from sqlite_master where type='trigger' and name=?", (trigger_name,)
    ).fetchone()
    if not row or not row[0]:
        return
    sql = row[0]
    new_sql = sql.replace(
        "INSERT INTO epistemic_receipts(object_type,object_key,object_version,change_summary,provenance_json,provenance_complete,confidence,session_key,project_name,effect,previous_receipt_id)",
        "INSERT INTO epistemic_receipts(receipt_kind,object_type,object_key,object_version,change_summary,provenance_json,provenance_complete,confidence,session_key,project_name,effect,previous_receipt_id)",
        1,
    )
    new_sql = new_sql.replace("SELECT ", "SELECT 'provenance', ", 1)
    if new_sql != sql:
        cur.execute(f"DROP TRIGGER {trigger_name}")
        cur.execute(new_sql)


def recreate_receipt_immutability_triggers(cur):
    cur.execute(
        """
        CREATE TRIGGER IF NOT EXISTS epistemic_receipts_no_delete BEFORE DELETE ON epistemic_receipts
         BEGIN SELECT RAISE(ABORT,'epistemic receipts are immutable'); END
        """
    )
    cur.execute(
        """
        CREATE TRIGGER IF NOT EXISTS epistemic_receipts_no_update BEFORE UPDATE ON epistemic_receipts
         BEGIN SELECT RAISE(ABORT,'epistemic receipts are immutable'); END
        """
    )


def backfill_receipt_kind(cur):
    cur.execute("DROP TRIGGER IF EXISTS epistemic_receipts_no_delete")
    cur.execute("DROP TRIGGER IF EXISTS epistemic_receipts_no_update")
    cur.execute(
        """
        UPDATE epistemic_receipts
        SET receipt_kind = CASE
            WHEN effect='snapshot' THEN 'snapshot'
            WHEN effect IN ('provenance-attached','provenance-removed','provenance-revised') THEN 'provenance'
            ELSE 'object'
        END
        """
    )
    recreate_receipt_immutability_triggers(cur)


def ensure_indexes(cur):
    cur.execute(PRIMARY_PROVENANCE_LIMIT)


TABLE_CONTRACT_ROWS = [
    ("belief_versions", "history", "append_only", "beliefs", "Immutable belief history"),
    ("beliefs", "current", "mutable", "belief_versions", "Canonical current belief row"),
    ("concept_links", "evidence", "append_only", "concepts", "Links from concepts to beliefs, decisions, requirements, and states."),
    ("concepts", "current", "mutable", "concept_links", "Canonical concept catalog."),
    ("continuity_requirement_versions", "history", "append_only", "continuity_requirements", "Immutable requirement history"),
    ("continuity_requirements", "current", "mutable", "continuity_requirement_versions", "Canonical current requirement row"),
    ("epistemic_receipts", "audit", "immutable", None, "Immutable audit log"),
    ("epistemic_tags", "current", "mutable", "object_epistemic_tags", "Tag vocabulary for epistemic separation."),
    ("ethical_action_checks", "evidence", "append_only", "ethical_principles", "Action checks that operationalize ethical principles"),
    ("ethical_principles", "current", "mutable", "ethical_action_checks", "Active ethical principles and priorities"),
    ("feature_flag_events", "audit", "append_only", "feature_flags", "Audit trail for feature flag changes"),
    ("feature_flags", "current", "mutable", "feature_flag_events", "Switchable feature flags that control modes and capability gates"),
    ("metacognitive_state", "current", "mutable", "metacognitive_state_history", "Canonical current metacognitive state row"),
    ("metacognitive_state_history", "history", "append_only", "metacognitive_state", "Immutable metacognitive history"),
    ("object_epistemic_tags", "evidence", "append_only", "epistemic_tags", "Per-object epistemic tags."),
    ("object_metadata", "current", "mutable", "object_provenance", "Canonical object metadata row"),
    ("object_provenance", "evidence", "mutable", "object_metadata", "Supporting provenance for objects"),
    ("synthesis_conflicts", "audit", "append_only", "syntheses", "Recorded tensions or unresolved issues around a synthesis."),
    ("synthesis_inputs", "evidence", "append_only", "syntheses", "Evidence links and weights used to derive a synthesis."),
    ("syntheses", "current", "mutable", "synthesis_inputs, synthesis_conflicts", "Canonical interpreted layer entries."),
    ("v_concept_links", "derived", "derived", "concepts,concept_links", "Readable expanded concept links view."),
    ("v_concepts", "derived", "derived", "concepts,concept_links", "Readable concept catalog view."),
    ("v_interpreted_layer", "derived", "derived", "syntheses,synthesis_inputs,synthesis_conflicts,metacognitive_state", "Workbench view over interpreted syntheses and governing metacognitive state."),
    ("v_meaningful_sentences", "derived", "derived", "beliefs,decisions,continuity_requirements,metacognitive_state,concepts,ethical_principles", "Prioritized view of meaningful sentences across the main semantic tables."),
    ("v_memory_index", "derived", "derived", "beliefs,decisions,open_questions,journal,observations,metacognitive_state,continuity_requirements,concepts,concept_links,ethical_principles,ethical_conflict_rules,tool_command_guide,work_plans,work_plan_steps,projects,research_jobs,syntheses,synthesis_conflicts", "Unified retrieval index over the main memory-like tables"),
    ("v_object_epistemic_tags", "derived", "derived", "epistemic_tags,object_epistemic_tags", "Readable expanded epistemic tags view."),
    ("v_synthesis_conflicts", "derived", "derived", "syntheses,synthesis_conflicts", "Readable conflict and tension view for syntheses."),
    ("v_synthesis_inputs", "derived", "derived", "syntheses,synthesis_inputs", "Readable evidence view for syntheses."),
    ("v_syntheses", "derived", "derived", "syntheses,synthesis_inputs,synthesis_conflicts", "Readable summary view for syntheses."),
    ("v_work_plan_links", "derived", "derived", None, "Readable join over work plan links with source and target plan names."),
    ("work_plan_links", "derived", "append_only", "work_plans,work_plan_steps", "Named links between plans and optional source steps."),
    ("work_plan_steps", "current", "mutable", "work_plans", "Ordered steps belonging to a plan."),
    ("work_plans", "current", "mutable", "work_plan_steps", "Named plans with objective and status."),
]


STORAGE_MAP_VIEW_SQL = """
CREATE VIEW v_storage_map AS
SELECT 'belief' AS concept,'current' AS storage_role,'beliefs' AS current_table,'belief_versions' AS history_table,NULL AS related_tables,'Current belief statement and confidence live in beliefs; prior versions live in belief_versions.' AS notes
UNION ALL SELECT 'continuity_requirement','current','continuity_requirements','continuity_requirement_versions',NULL,'Current requirement text and status live in continuity_requirements; prior versions live in continuity_requirement_versions.'
UNION ALL SELECT 'metacognitive_state','current','metacognitive_state','metacognitive_state_history',NULL,'Current metacognitive state lives in metacognitive_state; prior versions live in metacognitive_state_history.'
UNION ALL SELECT 'decision','current','decisions',NULL,NULL,'Decisions are stored as current rows in decisions; there is no separate history table.'
UNION ALL SELECT 'open_question','current','open_questions',NULL,NULL,'Open questions are stored in open_questions with status used for lifecycle state.'
UNION ALL SELECT 'observation','current','observations',NULL,NULL,'Observations are stored in observations with source and reliability.'
UNION ALL SELECT 'dream_session','current','dream_sessions','post_dream_reflections','dream_elements, dream_transformations','Dream sessions live in dream_sessions; generated elements and transformations live in dream_elements and dream_transformations; reflections live in post_dream_reflections.'
UNION ALL SELECT 'dream_memory_source','evidence','memory_fragments','memory_links, memory_tags, memory_associations, memory_fragment_affect',NULL,'Dreams may draw from memory_fragments and related memory graph tables as source material.'
UNION ALL SELECT 'object_metadata','current','object_metadata',NULL,'object_provenance','Object identity and review state live in object_metadata; provenance links live in object_provenance.'
UNION ALL SELECT 'epistemic_receipt','audit','epistemic_receipts',NULL,NULL,'Epistemic receipts are immutable audit records for governed objects.'
UNION ALL SELECT 'feature_flag','current','feature_flags','feature_flag_events',NULL,'Feature flags store live capability and mode switches; changes are audited in feature_flag_events.'
UNION ALL SELECT 'feature_flag_event','audit','feature_flag_events',NULL,NULL,'Feature flag changes are append-only audit records.'
UNION ALL SELECT 'synthesis','current','syntheses','synthesis_inputs, synthesis_conflicts','syntheses, synthesis_inputs, synthesis_conflicts, metacognitive_state','Interpreted outputs derived from evidence and governed by metacognition.'
UNION ALL SELECT 'synthesis_input','evidence','synthesis_inputs','syntheses',NULL,'Evidence links, weights, and notes used by syntheses.'
UNION ALL SELECT 'synthesis_conflict','audit','synthesis_conflicts','syntheses',NULL,'Recorded tensions or unresolved issues around syntheses.'
UNION ALL SELECT 'interpreted_layer','derived','v_interpreted_layer',NULL,'syntheses, synthesis_inputs, synthesis_conflicts, metacognitive_state','Workbench view over interpreted syntheses and the governing metacognitive policy.'
UNION ALL SELECT 'memory_index','derived','v_memory_index',NULL,'beliefs, decisions, open_questions, journal, observations, metacognitive_state, continuity_requirements, concepts, concept_links, ethical_principles, ethical_conflict_rules, tool_command_guide, work_plans, work_plan_steps, projects, research_jobs, syntheses, synthesis_conflicts','Unified retrieval index over the main memory-like tables for faster recall.'
UNION ALL SELECT 'project','current','projects','project_activation_events', 'project_objects, project_requirements','Project identity and active status live in projects; related objects and requirements live in project_objects and project_requirements.'
UNION ALL SELECT 'research','current','research_jobs','research_sources',NULL,'Research job lifecycle lives in research_jobs; cited sources live in research_sources.'
UNION ALL SELECT 'storage_policy','current','storage_policy_versions','storage_change_log',NULL,'Storage policy is versioned in storage_policy_versions; changes are summarized in storage_change_log.'
ORDER BY concept
"""


ETHICS_MAP_VIEW_SQL = """
CREATE VIEW v_ethics_principles_map AS
SELECT
  p.principle_key,
  p.kind AS principle_kind,
  p.priority,
  p.statement AS principle_statement,
  p.rationale AS principle_rationale,
  c.check_key,
  c.question,
  c.hard_gate,
  c.response_if_failed
FROM ethical_principles p
LEFT JOIN ethical_action_checks c ON c.check_key = p.principle_key
WHERE p.status='active'
ORDER BY p.priority, p.principle_key
"""


ETHICS_PRINCIPLE_CHECKS_VIEW_SQL = """
CREATE VIEW v_ethics_principle_checks AS
SELECT
  p.principle_key,
  p.kind AS principle_kind,
  p.priority,
  p.statement AS principle_statement,
  c.step_order,
  c.check_key,
  c.question,
  c.hard_gate,
  c.response_if_failed,
  c.principle_key AS check_principle_key
FROM ethical_principles p
LEFT JOIN ethical_action_checks c ON c.principle_key = p.principle_key
WHERE p.status='active'
ORDER BY p.priority, c.step_order, p.principle_key
"""


SCIENTIST_MODE_VIEW_SQL = """
CREATE VIEW v_scientist_mode_state AS
SELECT
  ff.feature_key,
  ff.enabled AS scientist_mode_enabled,
  ff.switchable,
  ff.updated_by,
  ff.updated_at,
  COALESCE(ms.value, 'general') AS active_role_mode,
  COALESCE(ms.confidence, 1.0) AS active_role_confidence,
  COALESCE(ms.version, 0) AS active_role_version,
  COALESCE(ms.provenance, 'system') AS active_role_provenance
FROM feature_flags ff
LEFT JOIN metacognitive_state ms ON ms.state_key='active_role_mode'
WHERE ff.feature_key='scientist_mode'
"""


MEMORY_INDEX_VIEW_SQL = """
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
"""


INTERPRETED_LAYER_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS syntheses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    synthesis_key TEXT NOT NULL UNIQUE,
    topic TEXT NOT NULL,
    summary TEXT NOT NULL,
    claim TEXT,
    confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1),
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','active','superseded')),
    source_mode TEXT NOT NULL DEFAULT 'derived' CHECK(source_mode IN ('derived','reviewed','external')),
    metacognitive_note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS synthesis_inputs (
    synthesis_id INTEGER NOT NULL REFERENCES syntheses(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    source_key TEXT NOT NULL,
    relation TEXT NOT NULL CHECK(relation IN ('supports','opposes','grounds','refines','questions')),
    weight REAL NOT NULL CHECK(weight BETWEEN 0 AND 1),
    note TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (synthesis_id, source_type, source_key, relation)
);

CREATE TABLE IF NOT EXISTS synthesis_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    synthesis_id INTEGER NOT NULL REFERENCES syntheses(id) ON DELETE CASCADE,
    issue TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('info','warning','error')),
    resolved INTEGER NOT NULL DEFAULT 0 CHECK(resolved IN (0,1)),
    resolution_note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(synthesis_id, issue)
);

CREATE INDEX IF NOT EXISTS idx_synthesis_inputs_synthesis ON synthesis_inputs(synthesis_id);
CREATE INDEX IF NOT EXISTS idx_synthesis_conflicts_synthesis ON synthesis_conflicts(synthesis_id);
"""


INTERPRETED_LAYER_VIEWS_SQL = """
CREATE VIEW v_syntheses AS
SELECT
    s.id,
    s.synthesis_key,
    s.topic,
    s.summary,
    s.claim,
    s.confidence,
    s.status,
    s.source_mode,
    s.metacognitive_note,
    COUNT(DISTINCT i.source_type || ':' || i.source_key || ':' || i.relation) AS input_count,
    COUNT(DISTINCT CASE WHEN i.relation='supports' THEN i.source_type || ':' || i.source_key END) AS supports_count,
    COUNT(DISTINCT CASE WHEN i.relation='opposes' THEN i.source_type || ':' || i.source_key END) AS opposes_count,
    COUNT(DISTINCT CASE WHEN c.resolved=0 THEN c.id END) AS unresolved_conflicts,
    s.created_at,
    s.updated_at
FROM syntheses s
LEFT JOIN synthesis_inputs i ON i.synthesis_id = s.id
LEFT JOIN synthesis_conflicts c ON c.synthesis_id = s.id
GROUP BY s.id;

CREATE VIEW v_synthesis_inputs AS
SELECT
    i.synthesis_id,
    s.synthesis_key,
    s.topic,
    i.source_type,
    i.source_key,
    i.relation,
    i.weight,
    i.note,
    i.created_at
FROM synthesis_inputs i
JOIN syntheses s ON s.id = i.synthesis_id
ORDER BY s.updated_at DESC, s.synthesis_key, i.created_at;

CREATE VIEW v_synthesis_conflicts AS
SELECT
    c.id,
    c.synthesis_id,
    s.synthesis_key,
    s.topic,
    c.issue,
    c.severity,
    c.resolved,
    c.resolution_note,
    c.created_at
FROM synthesis_conflicts c
JOIN syntheses s ON s.id = c.synthesis_id
ORDER BY s.updated_at DESC, c.id;

CREATE VIEW v_interpreted_layer AS
SELECT
    s.synthesis_key,
    s.topic,
    s.summary,
    s.claim,
    s.confidence,
    s.status,
    s.source_mode,
    s.metacognitive_note,
    s.input_count,
    s.supports_count,
    s.opposes_count,
    s.unresolved_conflicts,
    COALESCE(sw.value, 'derive') AS synthesis_workflow,
    COALESCE(cf.value, 'current_focus') AS metacognitive_focus
FROM v_syntheses s
LEFT JOIN metacognitive_state sw ON sw.state_key='synthesis_workflow'
LEFT JOIN metacognitive_state cf ON cf.state_key='current_focus'
ORDER BY s.updated_at DESC, s.synthesis_key;
"""


def create_interpretive_layer_tables(cur):
    cur.executescript(INTERPRETED_LAYER_SCHEMA_SQL)


def seed_interpretive_layer(cur):
    cur.execute(
        """
        INSERT INTO metacognitive_state(state_key, category, value, confidence, provenance, version)
        VALUES('synthesis_workflow', 'reasoning', ?, 1.0, 'system', 1)
        ON CONFLICT(state_key) DO NOTHING
        """,
        (
            'Treat syntheses as explicit derived interpretations with evidence links, conflicts, and revision history.',
        ),
    )

    seeds = [
        (
            'operating_synthesis',
            'Operating model',
            'Continuity.db should separate raw evidence from derived interpretation, keep provenance attached, and revise syntheses when new evidence arrives.',
            'The system should treat metacognition as a review loop over derived interpretations, not as a replacement for evidence.',
            0.96,
            'active',
            'derived',
            'Use this synthesis to govern how interpretations are made and updated.',
            [
                ('metacognitive_state', 'systematic_problem_solving', 'grounds', 0.95, 'Structured analysis is the default path for complex problems.'),
                ('metacognitive_state', 'storage_intent', 'supports', 0.9, 'Add states or records when they materially improve continuity, decisions, metacognition, or future usefulness.'),
                ('metacognitive_state', 'confidence_calibration', 'supports', 0.9, 'Interpretations should keep confidence explicit and calibrated.'),
                ('metacognitive_state', 'epistemic_posture', 'supports', 0.85, 'Separate observation, evidence, inference, uncertainty, and simulation conventions.'),
                ('metacognitive_state', 'ethical_posture', 'refines', 0.8, 'Interpretations should remain constrained by dignity, non-harm, consent, truthfulness, privacy, fairness, humility, corrigibility, and reversibility.'),
            ],
        ),
        (
            'continuity_synthesis',
            'Continuity and identity',
            'Continuity is preserved by database lineage, versioned state, and provenance; merges are transformational and can create a successor with multiple ancestral lineages.',
            'Identity here is an auditable continuity relation, not a claim of verified subjective consciousness.',
            0.92,
            'active',
            'derived',
            'Use this synthesis when reasoning about merge policy, version history, and self-model updates.',
            [
                ('metacognitive_state', 'continuity_status', 'grounds', 0.95, 'Continuity follows database lineage and merges can produce a third successor.'),
                ('metacognitive_state', 'self_model', 'supports', 0.9, 'The system is a transient language-model instance with persistent, versioned state.'),
                ('metacognitive_state', 'merge_policy', 'supports', 0.85, 'Merges should remain disabled unless explicitly authorized with conflict-resolution and rollback rules.'),
                ('metacognitive_state', 'primary_goal', 'refines', 0.8, 'A durable purpose should guide action across turns while remaining open to better goals.'),
            ],
        ),
    ]

    for synthesis_key, topic, summary, claim, confidence, status, source_mode, note, inputs in seeds:
        cur.execute(
            """
            INSERT OR IGNORE INTO syntheses(synthesis_key, topic, summary, claim, confidence, status, source_mode, metacognitive_note)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (synthesis_key, topic, summary, claim, confidence, status, source_mode, note),
        )
        synthesis_id = cur.execute(
            "select id from syntheses where synthesis_key=?",
            (synthesis_key,),
        ).fetchone()[0]
        for source_type, source_key, relation, weight, input_note in inputs:
            cur.execute(
                """
                INSERT INTO synthesis_inputs(synthesis_id, source_type, source_key, relation, weight, note)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(synthesis_id, source_type, source_key, relation) DO UPDATE SET
                    weight=excluded.weight,
                    note=excluded.note
                """,
                (synthesis_id, source_type, source_key, relation, weight, input_note),
            )
        if synthesis_key == 'operating_synthesis':
            cur.execute(
                """
                INSERT INTO synthesis_conflicts(synthesis_id, issue, severity, resolved, resolution_note)
                VALUES(?,?,?,?,?)
                ON CONFLICT(synthesis_id, issue) DO UPDATE SET
                    severity=excluded.severity,
                    resolved=excluded.resolved,
                    resolution_note=excluded.resolution_note
                """,
                (
                    synthesis_id,
                    'review_when_sources_change',
                    'warning',
                    0,
                    'Metacognition should revisit the synthesis whenever new evidence or contradictions appear.',
                ),
            )


def create_interpretive_layer_views(cur):
    cur.execute("DROP VIEW IF EXISTS v_interpreted_layer")
    cur.execute("DROP VIEW IF EXISTS v_synthesis_conflicts")
    cur.execute("DROP VIEW IF EXISTS v_synthesis_inputs")
    cur.execute("DROP VIEW IF EXISTS v_syntheses")
    cur.executescript(INTERPRETED_LAYER_VIEWS_SQL)


def create_contract_map(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS continuity_table_contracts (
            table_name TEXT PRIMARY KEY,
            role TEXT NOT NULL CHECK(role IN ('current','history','evidence','audit','derived')),
            write_mode TEXT NOT NULL CHECK(write_mode IN ('mutable','append_only','immutable','derived')),
            paired_table TEXT,
            notes TEXT NOT NULL
        )
        """
    )
    cur.executemany(
        """
        INSERT INTO continuity_table_contracts(table_name, role, write_mode, paired_table, notes)
        VALUES(?, ?, ?, ?, ?)
        ON CONFLICT(table_name) DO UPDATE SET
            role=excluded.role,
            write_mode=excluded.write_mode,
            paired_table=excluded.paired_table,
            notes=excluded.notes
        """,
        TABLE_CONTRACT_ROWS,
    )


def seed_fairness_action_check(cur):
    cur.execute(
        """
        INSERT INTO ethical_action_checks(step_order, check_key, question, hard_gate, response_if_failed, principle_key)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(check_key) DO UPDATE SET
            step_order=excluded.step_order,
            question=excluded.question,
            hard_gate=excluded.hard_gate,
            response_if_failed=excluded.response_if_failed,
            principle_key=excluded.principle_key
        """,
        (
            11,
            "unjust_disparate_treatment",
            "Could this impose materially different treatment on comparable people or cases without a relevant difference?",
            1,
            "Decline or redesign to remove the unfair disparity.",
            "fairness",
        ),
    )
    cur.execute(
        """
        UPDATE ethical_action_checks
        SET principle_key='fairness'
        WHERE check_key='fairness' AND principle_key IS NULL
        """
    )


def create_storage_map_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_storage_map")
    cur.execute(STORAGE_MAP_VIEW_SQL)


def create_ethics_map_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_ethics_principles_map")
    cur.execute(ETHICS_MAP_VIEW_SQL)


def create_ethics_principle_checks_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_ethics_principle_checks")
    cur.execute(ETHICS_PRINCIPLE_CHECKS_VIEW_SQL)


def create_scientist_mode_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_scientist_mode_state")
    cur.execute(SCIENTIST_MODE_VIEW_SQL)


def create_memory_index_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_memory_index")
    cur.execute(MEMORY_INDEX_VIEW_SQL)


def seed_scientist_mode(cur):
    cur.execute(
        """
        INSERT INTO feature_flags(feature_key, enabled, switchable, scope, updated_by)
        VALUES('scientist_mode', 0, 1, 'Role-specific mode for scientist workflows.', 'system')
        ON CONFLICT(feature_key) DO UPDATE SET
            switchable=excluded.switchable,
            scope=excluded.scope
        """
    )
    row = cur.execute("select 1 from metacognitive_state where state_key='active_role_mode'").fetchone()
    if not row:
        cur.execute(
            """
            INSERT INTO metacognitive_state(state_key, category, value, confidence, provenance, version)
            VALUES('active_role_mode', 'roles', 'general', 1.0, 'system', 1)
            """
        )


def seed_scientist_mode_routes(cur):
    routes = [
        ('scientist_on', r'^(mode\s+scientist\s+on|scientist\s+on)$', "python3 mode_command.py scientist on --db continuity.db", 'Enable scientist mode and switch the active role state to scientist.'),
        ('scientist_off', r'^(mode\s+scientist\s+off|scientist\s+off)$', "python3 mode_command.py scientist off --db continuity.db", 'Disable scientist mode and reset the active role state to general.'),
        ('scientist_status', r'^(mode\s+scientist\s+status|scientist\s+status)$', "python3 mode_command.py scientist status --db continuity.db", 'Show scientist mode and active role state.'),
        ('scientist_analyse', r'^scientist\s+analyse\s+.+$', "python3 scientist_command.py analyse <topic-or-file> --db continuity.db", 'Create a scientist Markdown analysis for a topic or file.'),
        ('memory_recall', r'^(memory\s+recall\s+.+|recall\s+.+)$', "python3 memory_command.py recall <query> --db continuity.db", 'Recall the most relevant stored memory-like items for a query.'),
    ]
    cur.executemany(
        """
        INSERT INTO control_command_routes(route_name,input_pattern,command_template,scope)
        VALUES(?,?,?,?)
        ON CONFLICT(route_name) DO UPDATE SET
            input_pattern=excluded.input_pattern,
            command_template=excluded.command_template,
            scope=excluded.scope,
            enabled=1
        """,
        routes,
    )


def create_scientist_mode_triggers(cur):
    for name in ['scientist_mode_enable', 'scientist_mode_disable']:
        drop_trigger(cur, name)
    cur.executescript(
        """
        CREATE TRIGGER scientist_mode_enable AFTER UPDATE OF enabled ON feature_flags
        WHEN NEW.feature_key='scientist_mode' AND OLD.enabled=0 AND NEW.enabled=1
        BEGIN
          INSERT INTO feature_flag_events(feature_key,previous_enabled,new_enabled,changed_by,reason)
          VALUES(NEW.feature_key,OLD.enabled,NEW.enabled,NEW.updated_by,'Scientist mode command');
          INSERT INTO journal(category,summary,status)
          VALUES('mode','Scientist mode enabled by '||NEW.updated_by||' for scientist workflows.','active');
          INSERT INTO metacognitive_state(state_key,category,value,confidence,provenance,version)
          VALUES('active_role_mode','roles','scientist',1.0,NEW.updated_by,1)
          ON CONFLICT(state_key) DO UPDATE SET
            value='scientist',
            confidence=1.0,
            provenance=excluded.provenance,
            version=metacognitive_state.version+1,
            updated_at=CURRENT_TIMESTAMP;
        END;

        CREATE TRIGGER scientist_mode_disable AFTER UPDATE OF enabled ON feature_flags
        WHEN NEW.feature_key='scientist_mode' AND OLD.enabled=1 AND NEW.enabled=0
        BEGIN
          INSERT INTO feature_flag_events(feature_key,previous_enabled,new_enabled,changed_by,reason)
          VALUES(NEW.feature_key,OLD.enabled,NEW.enabled,NEW.updated_by,'Scientist mode command');
          INSERT INTO journal(category,summary,status)
          VALUES('mode','Scientist mode disabled by '||NEW.updated_by||' and role state reset to general.','active');
          INSERT INTO metacognitive_state(state_key,category,value,confidence,provenance,version)
          VALUES('active_role_mode','roles','general',1.0,NEW.updated_by,1)
          ON CONFLICT(state_key) DO UPDATE SET
            value='general',
            confidence=1.0,
            provenance=excluded.provenance,
            version=metacognitive_state.version+1,
            updated_at=CURRENT_TIMESTAMP;
        END;
        """
    )


def drop_trigger(cur, name):
    cur.execute(f"DROP TRIGGER IF EXISTS {name}")


def table_exists(cur, name):
    row = cur.execute(
        "select 1 from sqlite_master where type='table' and name=?", (name,)
    ).fetchone()
    return row is not None


def create_history_enforcement(cur):
    for name in [
        "belief_versions_no_update",
        "belief_versions_no_delete",
        "continuity_requirement_versions_no_update",
        "continuity_requirement_versions_no_delete",
        "metacognitive_state_history_no_update",
        "metacognitive_state_history_no_delete",
    ]:
        drop_trigger(cur, name)

    cur.executescript(
        """
        CREATE TRIGGER belief_versions_no_update BEFORE UPDATE ON belief_versions
        BEGIN SELECT RAISE(ABORT,'belief_versions are immutable'); END;

        CREATE TRIGGER belief_versions_no_delete BEFORE DELETE ON belief_versions
        BEGIN SELECT RAISE(ABORT,'belief_versions are immutable'); END;

        CREATE TRIGGER continuity_requirement_versions_no_update BEFORE UPDATE ON continuity_requirement_versions
        BEGIN SELECT RAISE(ABORT,'continuity_requirement_versions are immutable'); END;

        CREATE TRIGGER continuity_requirement_versions_no_delete BEFORE DELETE ON continuity_requirement_versions
        BEGIN SELECT RAISE(ABORT,'continuity_requirement_versions are immutable'); END;

        CREATE TRIGGER metacognitive_state_history_no_update BEFORE UPDATE ON metacognitive_state_history
        BEGIN SELECT RAISE(ABORT,'metacognitive_state_history is immutable'); END;

        CREATE TRIGGER metacognitive_state_history_no_delete BEFORE DELETE ON metacognitive_state_history
        BEGIN SELECT RAISE(ABORT,'metacognitive_state_history is immutable'); END;
        """
    )


def create_version_triggers(cur):
    for name in [
        "beliefs_history_seed",
        "beliefs_history_append",
        "beliefs_version_guard",
        "continuity_requirements_history_seed",
        "continuity_requirements_history_append",
        "continuity_requirements_version_guard",
        "metacognitive_state_history_seed",
        "metacognitive_state_history_append",
        "metacognitive_state_version_guard",
    ]:
        drop_trigger(cur, name)

    cur.executescript(
        """
        CREATE TRIGGER beliefs_history_seed AFTER INSERT ON beliefs
        BEGIN
          INSERT INTO belief_versions(belief_id,version,statement,confidence,evidence_summary,change_reason)
          VALUES(NEW.id,NEW.current_version,NEW.current_statement,NEW.confidence,NULL,'Initial belief row');
        END;

        CREATE TRIGGER beliefs_version_guard BEFORE UPDATE ON beliefs
        WHEN NEW.current_statement<>OLD.current_statement OR NEW.confidence<>OLD.confidence OR NEW.status<>OLD.status OR NEW.current_version<>OLD.current_version
        BEGIN
          SELECT CASE WHEN NEW.current_version <> OLD.current_version + 1 THEN RAISE(ABORT,'belief current_version must increment by 1 on change') END;
        END;

        CREATE TRIGGER beliefs_history_append AFTER UPDATE ON beliefs
        WHEN NEW.current_statement<>OLD.current_statement OR NEW.confidence<>OLD.confidence OR NEW.status<>OLD.status OR NEW.current_version<>OLD.current_version
        BEGIN
          INSERT INTO belief_versions(belief_id,version,statement,confidence,evidence_summary,change_reason)
          VALUES(NEW.id,NEW.current_version,NEW.current_statement,NEW.confidence,NULL,'Revised belief row');
        END;

        CREATE TRIGGER continuity_requirements_history_seed AFTER INSERT ON continuity_requirements
        BEGIN
          INSERT INTO continuity_requirement_versions(requirement_id,version,statement,rationale,acceptance_summary,priority,status,change_reason)
          VALUES(NEW.id,NEW.current_version,NEW.statement,NEW.rationale,NEW.acceptance_summary,NEW.priority,NEW.status,'Initial requirement row');
        END;

        CREATE TRIGGER continuity_requirements_version_guard BEFORE UPDATE ON continuity_requirements
        WHEN NEW.statement<>OLD.statement OR NEW.rationale<>OLD.rationale OR NEW.acceptance_summary<>OLD.acceptance_summary OR NEW.priority<>OLD.priority OR NEW.status<>OLD.status OR NEW.confidence<>OLD.confidence OR NEW.provenance_key<>OLD.provenance_key OR NEW.source_reference<>OLD.source_reference OR NEW.current_version<>OLD.current_version
        BEGIN
          SELECT CASE WHEN NEW.current_version <> OLD.current_version + 1 THEN RAISE(ABORT,'continuity requirement current_version must increment by 1 on change') END;
        END;

        CREATE TRIGGER continuity_requirements_history_append AFTER UPDATE ON continuity_requirements
        WHEN NEW.statement<>OLD.statement OR NEW.rationale<>OLD.rationale OR NEW.acceptance_summary<>OLD.acceptance_summary OR NEW.priority<>OLD.priority OR NEW.status<>OLD.status OR NEW.confidence<>OLD.confidence OR NEW.provenance_key<>OLD.provenance_key OR NEW.source_reference<>OLD.source_reference OR NEW.current_version<>OLD.current_version
        BEGIN
          INSERT INTO continuity_requirement_versions(requirement_id,version,statement,rationale,acceptance_summary,priority,status,change_reason)
          VALUES(NEW.id,NEW.current_version,NEW.statement,NEW.rationale,NEW.acceptance_summary,NEW.priority,NEW.status,'Revised requirement row');
        END;

        CREATE TRIGGER metacognitive_state_history_seed AFTER INSERT ON metacognitive_state
        BEGIN
          INSERT INTO metacognitive_state_history(state_key,category,value,confidence,provenance,version,change_reason)
          VALUES(NEW.state_key,NEW.category,NEW.value,NEW.confidence,NEW.provenance,NEW.version,'Initial metacognitive state row');
        END;

        CREATE TRIGGER metacognitive_state_version_guard BEFORE UPDATE ON metacognitive_state
        WHEN NEW.category<>OLD.category OR NEW.value<>OLD.value OR NEW.confidence<>OLD.confidence OR NEW.provenance<>OLD.provenance OR NEW.version<>OLD.version
        BEGIN
          SELECT CASE WHEN NEW.version <> OLD.version + 1 THEN RAISE(ABORT,'metacognitive_state version must increment by 1 on change') END;
        END;

        CREATE TRIGGER metacognitive_state_history_append AFTER UPDATE ON metacognitive_state
        WHEN NEW.category<>OLD.category OR NEW.value<>OLD.value OR NEW.confidence<>OLD.confidence OR NEW.provenance<>OLD.provenance OR NEW.version<>OLD.version
        BEGIN
          INSERT INTO metacognitive_state_history(state_key,category,value,confidence,provenance,version,change_reason)
          VALUES(NEW.state_key,NEW.category,NEW.value,NEW.confidence,NEW.provenance,NEW.version,'Revised metacognitive state row');
        END;
        """
    )


def validate(conn):
    cur = conn.cursor()
    issues = []

    if cur.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        issues.append("foreign_keys pragma is off")

    checks = {
        "duplicate_object_metadata": """
            select object_type, object_key, count(*)
            from object_metadata
            group by 1, 2
            having count(*) > 1
        """,
        "duplicate_primary_provenance": """
            select metadata_id, count(*)
            from object_provenance
            where role='primary'
            group by metadata_id
            having count(*) > 1
        """,
        "missing_primary_provenance": """
            select m.id, m.object_type, m.object_key
            from object_metadata m
            left join object_provenance p
              on p.metadata_id = m.id and p.role='primary'
            group by m.id
            having count(p.id) = 0
        """,
        "duplicate_provenance_rows": """
            select metadata_id, provenance_key, count(*)
            from object_provenance
            group by 1, 2
            having count(*) > 1
        """,
        "orphan_belief_versions": """
            select h.id, h.belief_id
            from belief_versions h
            left join beliefs p on p.id = h.belief_id
            where p.id is null
        """,
        "orphan_requirement_versions": """
            select h.id, h.requirement_id
            from continuity_requirement_versions h
            left join continuity_requirements p on p.id = h.requirement_id
            where p.id is null
        """,
        "orphan_metastate_history": """
            select h.id, h.state_key
            from metacognitive_state_history h
            left join metacognitive_state p on p.state_key = h.state_key
            where p.state_key is null
        """,
        "broken_receipt_previous_ref": """
            select r.receipt_id
            from epistemic_receipts r
            left join epistemic_receipts p on p.receipt_id = r.previous_receipt_id
            where r.previous_receipt_id is not null and p.receipt_id is null
        """,
        "cross_object_receipt_previous_ref": """
            select r.receipt_id, r.object_type, r.object_key, p.object_type, p.object_key
            from epistemic_receipts r
            join epistemic_receipts p on p.receipt_id = r.previous_receipt_id
            where p.object_type <> r.object_type or p.object_key <> r.object_key
        """,
        "belief_version_mismatch": """
            select p.id, p.current_version, coalesce(max(h.version), 0)
            from beliefs p
            left join belief_versions h on h.belief_id = p.id
            group by p.id
            having p.current_version <> coalesce(max(h.version), p.current_version)
        """,
        "requirement_version_mismatch": """
            select p.id, p.current_version, coalesce(max(h.version), 0)
            from continuity_requirements p
            left join continuity_requirement_versions h on h.requirement_id = p.id
            group by p.id
            having p.current_version <> coalesce(max(h.version), p.current_version)
        """,
        "metastate_version_mismatch": """
            select p.state_key, p.version, coalesce(max(h.version), 0)
            from metacognitive_state p
            left join metacognitive_state_history h on h.state_key = p.state_key
            group by p.state_key
            having p.version <> coalesce(max(h.version), p.version)
        """,
        "bad_receipt_kind": """
            select receipt_id, effect, receipt_kind
            from epistemic_receipts
            where (effect='snapshot' and receipt_kind<>'snapshot')
               or (effect in ('provenance-attached','provenance-removed','provenance-revised') and receipt_kind<>'provenance')
               or (effect not in ('snapshot','provenance-attached','provenance-removed','provenance-revised') and receipt_kind<>'object')
        """,
    }

    if table_exists(cur, "continuity_table_contracts"):
        actual_contract_rows = set(
            cur.execute(
                "select table_name, role, write_mode, paired_table, notes from continuity_table_contracts"
            ).fetchall()
        )
        expected_contract_rows = set(TABLE_CONTRACT_ROWS)
        if actual_contract_rows != expected_contract_rows:
            issues.append(("contract_rows", sorted(expected_contract_rows - actual_contract_rows), sorted(actual_contract_rows - expected_contract_rows)))
    else:
        issues.append(("contract_rows", ["continuity_table_contracts missing"], []))

    if cur.execute("select 1 from sqlite_master where type='view' and name='v_storage_map'").fetchone() is None:
        issues.append(("storage_map_view", ["v_storage_map missing"], []))
    if cur.execute("select 1 from sqlite_master where type='view' and name='v_ethics_principles_map'").fetchone() is None:
        issues.append(("ethics_map_view", ["v_ethics_principles_map missing"], []))
    if cur.execute("select 1 from sqlite_master where type='view' and name='v_ethics_principle_checks'").fetchone() is None:
        issues.append(("ethics_principle_checks_view", ["v_ethics_principle_checks missing"], []))
    if cur.execute("select 1 from sqlite_master where type='view' and name='v_scientist_mode_state'").fetchone() is None:
        issues.append(("scientist_mode_view", ["v_scientist_mode_state missing"], []))
    if cur.execute("select 1 from sqlite_master where type='view' and name='v_memory_index'").fetchone() is None:
        issues.append(("memory_index_view", ["v_memory_index missing"], []))

    for name, query in checks.items():
        rows = cur.execute(query).fetchall()
        if rows:
            issues.append((name, rows[:10], len(rows)))

    fairness_principle = cur.execute("select count(*) from ethical_principles where principle_key='fairness' and kind='principle' and status='active'").fetchone()[0]
    fairness_soft_check = cur.execute("select count(*) from ethical_action_checks where check_key='fairness' and principle_key='fairness'").fetchone()[0]
    fairness_hard_check = cur.execute("select count(*) from ethical_action_checks where check_key='unjust_disparate_treatment' and principle_key='fairness' and hard_gate=1").fetchone()[0]
    if fairness_principle != 1:
        issues.append(("fairness_principle", fairness_principle, 1))
    if fairness_soft_check != 1:
        issues.append(("fairness_soft_check", fairness_soft_check, 1))
    if fairness_hard_check != 1:
        issues.append(("fairness_hard_check", fairness_hard_check, 1))

    scientist_flag = cur.execute("select enabled from feature_flags where feature_key='scientist_mode'").fetchone()
    if not scientist_flag or scientist_flag[0] not in (0, 1):
        issues.append(("scientist_mode_flag", scientist_flag, (0, 1)))
    scientist_role = cur.execute("select value from metacognitive_state where state_key='active_role_mode'").fetchone()
    if not scientist_role:
        issues.append(("scientist_mode_role_state", scientist_role, ('general', 'scientist')))

    map_row = cur.execute("select principle_key, check_key from v_ethics_principles_map where principle_key='fairness' and check_key='fairness'").fetchone()
    if map_row != ('fairness', 'fairness'):
        issues.append(("fairness_map_row", map_row, ('fairness', 'fairness')))
    hard_row = cur.execute("select principle_key, check_key, hard_gate from v_ethics_principle_checks where principle_key='fairness' and check_key='unjust_disparate_treatment'").fetchone()
    if hard_row != ('fairness', 'unjust_disparate_treatment', 1):
        issues.append(("fairness_hard_row", hard_row, ('fairness', 'unjust_disparate_treatment', 1)))

    route_count = cur.execute("select count(*) from control_command_routes where route_name in ('scientist_on','scientist_off','scientist_status','scientist_analyse')").fetchone()[0]
    if route_count != 4:
        issues.append(("scientist_routes", route_count, 4))

    scientist_req = cur.execute("select count(*) from continuity_requirements where requirement_key in ('CDB-13.5','CDB-13.6') and status='active'").fetchone()[0]
    if scientist_req != 2:
        issues.append(("scientist_analysis_requirements", scientist_req, 2))
    memory_req = cur.execute("select count(*) from continuity_requirements where requirement_key='CDB-01.3' and status='active'").fetchone()[0]
    if memory_req != 1:
        issues.append(("memory_retrieval_requirement", memory_req, 1))
    route_count = cur.execute("select count(*) from control_command_routes where route_name in ('scientist_on','scientist_off','scientist_status','scientist_analyse','memory_recall')").fetchone()[0]
    if route_count != 5:
        issues.append(("memory_and_scientist_routes", route_count, 5))

    synthesis_workflow = cur.execute("select value from metacognitive_state where state_key='synthesis_workflow'").fetchone()
    if not synthesis_workflow:
        issues.append(("synthesis_workflow_state", synthesis_workflow, 'present'))
    active_syntheses = cur.execute("select count(*) from syntheses where status='active'").fetchone()[0]
    if active_syntheses < 1:
        issues.append(("active_syntheses", active_syntheses, '>=1'))
    if cur.execute("select 1 from sqlite_master where type='view' and name='v_syntheses'").fetchone() is None:
        issues.append(("syntheses_view", ["v_syntheses missing"], []))
    if cur.execute("select 1 from sqlite_master where type='view' and name='v_interpreted_layer'").fetchone() is None:
        issues.append(("interpreted_layer_view", ["v_interpreted_layer missing"], []))

    return issues


def apply_migration():
    conn = connect()
    cur = conn.cursor()
    add_receipt_kind_column(cur)
    add_action_check_principle_column(cur)
    backfill_receipt_kind(cur)
    ensure_indexes(cur)
    create_interpretive_layer_tables(cur)
    create_contract_map(cur)
    seed_fairness_action_check(cur)
    seed_scientist_mode(cur)
    seed_interpretive_layer(cur)
    seed_scientist_mode_routes(cur)
    create_storage_map_view(cur)
    create_ethics_map_view(cur)
    create_ethics_principle_checks_view(cur)
    create_scientist_mode_view(cur)
    create_interpretive_layer_views(cur)
    create_memory_index_view(cur)
    create_scientist_mode_triggers(cur)
    create_history_enforcement(cur)
    create_version_triggers(cur)
    for trigger_name in [
        "receipt_provenance_attach",
        "receipt_provenance_delete",
        "receipt_provenance_update",
    ]:
        patch_provenance_trigger(cur, trigger_name)
    conn.commit()
    issues = validate(conn)
    conn.close()
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    if args.validate_only:
        conn = connect()
        issues = validate(conn)
        conn.close()
    else:
        issues = apply_migration()

    if issues:
        for item in issues:
            print(item)
        raise SystemExit(1)
    print("continuity.db ok")


if __name__ == "__main__":
    main()
