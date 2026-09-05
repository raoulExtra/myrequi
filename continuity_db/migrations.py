#!/usr/bin/env python3
import argparse
import json
import sqlite3
from pathlib import Path

from .schema import (
    ETHICS_MAP_VIEW_SQL,
    ETHICS_PRINCIPLE_CHECKS_VIEW_SQL,
    DECISION_HISTORY_SCHEMA_SQL,
    DECISION_OPTIONS_SCHEMA_SQL,
    INTERPRETED_LAYER_SCHEMA_SQL,
    INTERPRETED_LAYER_VIEWS_SQL,
    DECISION_OPTIONS_VIEW_SQL,
    CONVICTIONS_VIEW_SQL,
    MEMORY_INDEX_VIEW_SQL,
    MEMORY_PACKET_VIEW_SQL,
    WRITEBACK_POLICY_VIEW_SQL,
    OPEN_QUESTION_FLOW_VIEW_SQL,
    ARGUMENT_CLAIMS_VIEW_SQL,
    REASONING_EPISODE_INPUTS_SCHEMA_SQL,
    REASONING_EPISODE_SCHEMA_SQL,
    REASONING_FLOW_VIEW_SQL,
    RAW_RECALL_VIEWS_SQL,
    SCIENTIST_MODE_VIEW_SQL,
    STORAGE_MAP_VIEW_SQL,
    TABLE_CONTRACT_ROWS,
    COMPONENT_INFLUENCE_SCHEMA_SQL,
)
from .views import FRAME_VIEWS_SQL, CORE_MODEL_VIEW_SQL, GLOSSARY_TERMS_VIEW_SQL, LEAN_THINKING_PATTERNS_VIEW_SQL, DECISION_PATTERNS_VIEW_SQL, PROBLEM_SOLVING_PATTERNS_VIEW_SQL, PROBLEM_UNDERSTANDING_PATTERNS_VIEW_SQL, PROVENANCE_SUMMARY_VIEW_SQL, SCHEMA_CATALOG_VIEW_SQL, SCHEMA_CATALOG_ALL_VIEW_SQL, TAG_SEARCH_VIEW_SQL, CONCEPT_SEARCH_VIEW_SQL, DECISION_OVERVIEW_VIEW_SQL, COMPONENT_INFLUENCE_VIEWS_SQL, REASONING_QUALITY_VIEWS_SQL

ROOT = Path(__file__).resolve().parent.parent
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


def backfill_belief_version_evidence_summary(cur):
    cur.execute("DROP TRIGGER IF EXISTS belief_versions_no_update")
    cur.execute("DROP TRIGGER IF EXISTS belief_versions_no_delete")
    cur.execute(
        """
        UPDATE belief_versions
        SET evidence_summary = COALESCE(
            (
                SELECT r.change_summary
                FROM epistemic_receipts r
                WHERE r.object_type='belief'
                  AND r.object_key = CAST(belief_versions.belief_id AS TEXT)
                  AND r.object_version = CAST(belief_versions.version AS TEXT)
                ORDER BY r.receipt_id DESC
                LIMIT 1
            ),
            'Belief recorded: ' || belief_versions.statement
        )
        WHERE evidence_summary IS NULL OR trim(evidence_summary)=''
        """
    )
    create_history_enforcement(cur)


def backfill_epistemic_receipt_provenance(cur):
    cur.execute("DROP TRIGGER IF EXISTS epistemic_receipts_no_delete")
    cur.execute("DROP TRIGGER IF EXISTS epistemic_receipts_no_update")
    rows = cur.execute(
        """
        select receipt_id, object_type, object_key, object_version, change_summary, previous_receipt_id
        from epistemic_receipts
        where provenance_complete=0 or provenance_json='[]'
        order by receipt_id
        """
    ).fetchall()
    for receipt_id, object_type, object_key, object_version, change_summary, previous_receipt_id in rows:
        provenance_json = {
            "origin": "db_record",
            "lineage": "direct",
            "basis": "recorded_change_summary",
            "change_summary": change_summary,
            "object": {
                "type": object_type,
                "key": object_key,
                "version": object_version,
            },
            "previous_receipt_id": previous_receipt_id,
        }
        cur.execute(
            """
            update epistemic_receipts
            set provenance_json=?, provenance_complete=1
            where receipt_id=?
            """,
            (json.dumps(provenance_json, ensure_ascii=False), receipt_id),
        )
    recreate_receipt_immutability_triggers(cur)


def ensure_primary_object_provenance(cur, object_type, object_key, provenance_key='database_state', note='Primary origin of this seeded object.'):
    row = cur.execute(
        "select id from object_metadata where object_type=? and object_key=?",
        (object_type, object_key),
    ).fetchone()
    if not row:
        return
    metadata_id = row[0]
    exists = cur.execute(
        "select 1 from object_provenance where metadata_id=? and role='primary' limit 1",
        (metadata_id,),
    ).fetchone()
    if not exists:
        cur.execute(
            "insert into object_provenance(metadata_id, provenance_key, role, note) values(?,?,?,?)",
            (metadata_id, provenance_key, 'primary', note),
        )


def seed_morphology_concept_provenance(cur):
    for trigger in ['receipt_provenance_attach', 'receipt_provenance_delete', 'receipt_provenance_update']:
        drop_trigger(cur, trigger)
    for key in ['morphology.common_prefixes', 'morphology.common_suffixes']:
        ensure_primary_object_provenance(cur, 'concept', key)


def ensure_indexes(cur):
    cur.execute(PRIMARY_PROVENANCE_LIMIT)


def create_interpretive_layer_tables(cur):
    cur.executescript(INTERPRETED_LAYER_SCHEMA_SQL)


def create_memory_conditions_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_conditions (
            source_type TEXT NOT NULL,
            source_key TEXT NOT NULL,
            condition TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source_type, source_key)
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_conditions_condition ON memory_conditions(condition)")


def create_component_influence_tables(cur):
    cur.executescript(COMPONENT_INFLUENCE_SCHEMA_SQL)


def seed_component_influence_modes(cur):
    modes = [
        ('default', 'Default', 'Baseline influence preset.'),
        ('high_attention', 'High attention', 'Preset for focused, high-salience operation.'),
        ('low_attention', 'Low attention', 'Preset for low-salience or background operation.'),
        ('startup', 'Startup', 'Preset for initialization and warm-up.'),
        ('error_recovery', 'Error recovery', 'Preset for correction and stabilization after failure.'),
        ('evolved', 'Evolved', 'Preset for a stabilized, learned, refined baseline.'),
    ]
    for mode_key, label, description in modes:
        cur.execute(
            """
            INSERT INTO component_influence_modes(mode_key, label, description)
            VALUES(?,?,?)
            ON CONFLICT(mode_key) DO UPDATE SET
                label=excluded.label,
                description=excluded.description
            """,
            (mode_key, label, description),
        )


def seed_error_recovery_influence_preset(cur):
    rows = [
        ('concept', 'thinking_engine_recovery_component', 0.50, 0.95, 'error_recovery: restore stable operation or safe fallback.'),
        ('concept', 'correction', 0.50, 0.93, 'error_recovery: fix mistakes explicitly.'),
        ('concept', 'thinking_engine_uncertainty_component', 0.50, 0.90, 'error_recovery: increase uncertainty handling and calibration.'),
        ('concept', 'thinking_engine_logging_component', 0.50, 0.88, 'error_recovery: preserve diagnostics and traces.'),
        ('concept', 'thinking_engine_retrieval_component', 0.50, 0.86, 'error_recovery: re-check sources and retrieve relevant context.'),
        ('concept', 'schema_catalog', 0.50, 0.82, 'error_recovery: find structure and canonical surfaces quickly.'),
        ('concept', 'discovery', 0.50, 0.80, 'error_recovery: locate useful paths and missing structure.'),
        ('concept', 'entrypoint', 0.50, 0.78, 'error_recovery: start from a canonical place.'),
        ('concept', 'canonical_home_enforcement', 0.50, 0.76, 'error_recovery: route to one primary home to avoid duplication.'),
        ('concept', 'overlap_reduction', 0.50, 0.74, 'error_recovery: collapse duplicate or conflicting paths.'),
    ]
    for component_type, component_key, default_score, current_score, reason in rows:
        cur.execute(
            """
            INSERT INTO component_influence(component_type, component_key, mode_key, default_score, current_score, override_reason)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(component_type, component_key) DO UPDATE SET
                mode_key=excluded.mode_key,
                default_score=excluded.default_score,
                current_score=excluded.current_score,
                override_reason=excluded.override_reason,
                updated_at=CURRENT_TIMESTAMP
            """,
            (component_type, component_key, 'error_recovery', default_score, current_score, reason),
        )


def seed_influence_preset_rows(cur, mode_key, rows):
    for component_type, component_key, score, reason in rows:
        cur.execute(
            """
            INSERT INTO component_influence_presets(mode_key, component_type, component_key, preset_score, reason)
            VALUES(?,?,?,?,?)
            ON CONFLICT(mode_key, component_type, component_key) DO UPDATE SET
                preset_score=excluded.preset_score,
                reason=excluded.reason
            """,
            (mode_key, component_type, component_key, score, reason),
        )


def seed_component_influence_current_from_preset(cur, mode_key):
    rows = cur.execute(
        "select component_type, component_key, preset_score, reason from component_influence_presets where mode_key=? order by component_type, component_key",
        (mode_key,),
    ).fetchall()
    for component_type, component_key, score, reason in rows:
        cur.execute(
            """
            INSERT INTO component_influence(component_type, component_key, mode_key, default_score, current_score, override_reason)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(component_type, component_key) DO UPDATE SET
                mode_key=excluded.mode_key,
                default_score=excluded.default_score,
                current_score=excluded.current_score,
                override_reason=excluded.override_reason,
                updated_at=CURRENT_TIMESTAMP
            """,
            (component_type, component_key, mode_key, score, score, reason),
        )


def seed_error_recovery_influence_work_plan(cur):
    cur.execute(
        """
        INSERT INTO work_plans(plan_key, title, objective, status, created_by, prompt)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(plan_key) DO UPDATE SET
            title=excluded.title,
            objective=excluded.objective,
            status=excluded.status,
            created_by=excluded.created_by,
            prompt=excluded.prompt,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            'error_recovery_influence_flow',
            'Error recovery influence flow',
            'Define how the engine should raise, lower, and restore component influence during error recovery, then return to baseline safely.',
            'active',
            'system',
            'Use this plan when the engine enters error_recovery mode and needs a safe influence preset and recovery loop.',
        ),
    )
    plan_id = cur.execute("select id from work_plans where plan_key='error_recovery_influence_flow'").fetchone()[0]
    cur.execute("delete from work_plan_steps where plan_id=?", (plan_id,))
    steps = [
        (1, 'detect', 'Detect error, drift, or stall and confirm recovery mode is needed.'),
        (2, 'stabilize', 'Raise recovery, correction, uncertainty, logging, and retrieval influence; lower speculative expansion.'),
        (3, 'inspect', 'Inspect schema catalog, discovery paths, entrypoints, and canonical homes to locate the right surface.'),
        (4, 'correct', 'Apply the smallest correction needed and record why the influence changed.'),
        (5, 'resume', 'Validate stability, restore baseline influence, and continue normal operation.'),
    ]
    cur.executemany(
        """
        INSERT INTO work_plan_steps(plan_id, step_order, step_key, description, status, evidence)
        VALUES(?,?,?,?,?,?)
        """,
        [(plan_id, order, key, desc, 'pending', 'error_recovery preset') for order, key, desc in steps],
    )
    links = [
        ('influence', 'work_plan', 'error_recovery_influence_flow', 'supports', 'Describes how to apply and restore influence settings in recovery mode.'),
        ('system', 'work_plan', 'error_recovery_influence_flow', 'supports', 'Defines a system-level recovery policy for the engine.'),
        ('thinking_engine_recovery_component', 'work_plan', 'error_recovery_influence_flow', 'supports', 'Recovery component is the primary driver of the mode.'),
        ('thinking_engine_uncertainty_component', 'work_plan', 'error_recovery_influence_flow', 'supports', 'Uncertainty handling should rise during recovery.'),
        ('thinking_engine_logging_component', 'work_plan', 'error_recovery_influence_flow', 'supports', 'Logging should capture recovery context and decisions.'),
        ('thinking_engine_retrieval_component', 'work_plan', 'error_recovery_influence_flow', 'supports', 'Retrieval should be emphasized to re-check context.'),
        ('correction', 'work_plan', 'error_recovery_influence_flow', 'supports', 'Correction is the core action after detection.'),
        ('schema_catalog', 'work_plan', 'error_recovery_influence_flow', 'supports', 'Schema catalog helps locate canonical surfaces quickly.'),
        ('discovery', 'work_plan', 'error_recovery_influence_flow', 'supports', 'Discovery helps find the useful path and missing structure.'),
        ('entrypoint', 'work_plan', 'error_recovery_influence_flow', 'supports', 'Entrypoints help restart from a canonical place.'),
        ('canonical_home_enforcement', 'work_plan', 'error_recovery_influence_flow', 'supports', 'Canonical homes reduce duplication during repair.'),
        ('overlap_reduction', 'work_plan', 'error_recovery_influence_flow', 'supports', 'Overlap reduction prevents duplicate or conflicting paths.'),
    ]
    for concept_key, object_type, object_key, relation, note in links:
        cur.execute(
            """
            INSERT INTO concept_links(concept_key, object_type, object_key, relation, note)
            VALUES(?,?,?,?,?)
            ON CONFLICT(concept_key, object_type, object_key, relation) DO UPDATE SET
                note=excluded.note
            """,
            (concept_key, object_type, object_key, relation, note),
        )


def seed_evolved_baseline_demo_work_plan(cur):
    cur.execute(
        """
        INSERT INTO work_plans(plan_key, title, objective, status, created_by, prompt)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(plan_key) DO UPDATE SET
            title=excluded.title,
            objective=excluded.objective,
            status=excluded.status,
            created_by=excluded.created_by,
            prompt=excluded.prompt,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            'evolved_baseline_demo',
            'Evolved baseline demo',
            'Demonstrate that default influence is seeded from evolved, then update evolved after a recovery improvement and sync default again.',
            'active',
            'system',
            'Use this plan when you want to show that the baseline starts evolved and only changes after the system learns something new.',
        ),
    )
    plan_id = cur.execute("select id from work_plans where plan_key='evolved_baseline_demo'").fetchone()[0]
    cur.execute("delete from work_plan_steps where plan_id=?", (plan_id,))
    steps = [
        (1, 'compare', 'Compare evolved and default presets and verify they match at startup.'),
        (2, 'confirm', 'Confirm default is just the current baseline copied from evolved.'),
        (3, 'recover', 'Use error_recovery mode and capture the useful adjustment that stabilizes the engine.'),
        (4, 'learn', 'Fold the useful adjustment back into evolved so the system has learned.'),
        (5, 'resync', 'Re-seed default from evolved and verify both states remain aligned.'),
    ]
    cur.executemany(
        """
        INSERT INTO work_plan_steps(plan_id, step_order, step_key, description, status, evidence)
        VALUES(?,?,?,?,?,?)
        """,
        [(plan_id, order, key, desc, 'pending', 'evolved baseline demo') for order, key, desc in steps],
    )
    links = [
        ('influence', 'work_plan', 'evolved_baseline_demo', 'supports', 'Shows the evolving influence model and preset synchronization.'),
        ('system', 'work_plan', 'evolved_baseline_demo', 'supports', 'Demonstrates the system-level baseline lifecycle.'),
        ('correction', 'work_plan', 'evolved_baseline_demo', 'supports', 'Learning requires visible correction after a recovery run.'),
        ('thinking_engine_learning_component', 'work_plan', 'evolved_baseline_demo', 'supports', 'Learning component should absorb the useful recovery adjustment.'),
        ('thinking_engine_recovery_component', 'work_plan', 'evolved_baseline_demo', 'supports', 'Recovery component discovers the needed adjustment.'),
        ('thinking_engine_workflow_component', 'work_plan', 'evolved_baseline_demo', 'supports', 'Workflow component coordinates compare->recover->learn->resync.'),
        ('thinking_engine_governance_component', 'work_plan', 'evolved_baseline_demo', 'supports', 'Governance ensures the baseline is updated safely.'),
        ('schema_catalog', 'work_plan', 'evolved_baseline_demo', 'supports', 'Schema catalog helps verify state surfaces during the demo.'),
        ('discovery', 'work_plan', 'evolved_baseline_demo', 'supports', 'Discovery helps locate the useful changed path.'),
        ('entrypoint', 'work_plan', 'evolved_baseline_demo', 'supports', 'Entry points help show the current baseline quickly.'),
    ]
    for concept_key, object_type, object_key, relation, note in links:
        cur.execute(
            """
            INSERT INTO concept_links(concept_key, object_type, object_key, relation, note)
            VALUES(?,?,?,?,?)
            ON CONFLICT(concept_key, object_type, object_key, relation) DO UPDATE SET
                note=excluded.note
            """,
            (concept_key, object_type, object_key, relation, note),
        )


def create_reasoning_episode_tables(cur):
    cur.executescript(REASONING_EPISODE_SCHEMA_SQL)


def add_reasoning_episode_columns(cur):
    cols = column_names(cur, 'reasoning_episodes')
    if 'resolves_open_question_id' not in cols:
        cur.execute("ALTER TABLE reasoning_episodes ADD COLUMN resolves_open_question_id INTEGER REFERENCES open_questions(id)")
    if 'concludes_decision_id' not in cols:
        cur.execute("ALTER TABLE reasoning_episodes ADD COLUMN concludes_decision_id INTEGER REFERENCES decisions(id)")


def create_decision_history_tables(cur):
    cur.executescript(DECISION_HISTORY_SCHEMA_SQL)


def create_decision_options_table(cur):
    cur.executescript(DECISION_OPTIONS_SCHEMA_SQL)


def add_decision_history_columns(cur):
    cols = column_names(cur, 'decision_versions')
    if 'origin_reasoning_episode_id' not in cols:
        cur.execute("ALTER TABLE decision_versions ADD COLUMN origin_reasoning_episode_id INTEGER REFERENCES reasoning_episodes(id)")


def add_decision_flow_columns(cur):
    cols = column_names(cur, 'decisions')
    if 'origin_reasoning_episode_id' not in cols:
        cur.execute("ALTER TABLE decisions ADD COLUMN origin_reasoning_episode_id INTEGER REFERENCES reasoning_episodes(id)")


def create_reasoning_episode_inputs_table(cur):
    cur.executescript(REASONING_EPISODE_INPUTS_SCHEMA_SQL)


def backfill_reasoning_episode_inputs(cur):
    existing = {
        row[0]
        for row in cur.execute('select distinct episode_id from reasoning_episode_inputs').fetchall()
    }
    seeds = [
        (1, 'journal', '73', 'grounds', 0.95, 'Gap report identified missing reasoning surface and argument recall.'),
        (11, 'open_question', '4', 'questions', 0.95, 'This episode resolves the explicit uniqueness question after the user requested enforcement.'),
    ]
    for episode_id, source_type, source_key, relation, weight, note in seeds:
        if episode_id in existing:
            continue
        cur.execute(
            """
            INSERT INTO reasoning_episode_inputs(episode_id, source_type, source_key, relation, weight, note)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(episode_id, source_type, source_key, relation) DO UPDATE SET
                weight=excluded.weight,
                note=excluded.note
            """,
            (episode_id, source_type, source_key, relation, weight, note),
        )


def backfill_reasoning_decision_links(cur):
    decision_row = cur.execute("select id from decisions where decision='Enforce uniqueness for entities and facts.' order by id desc limit 1").fetchone()
    reasoning_row = cur.execute("select id from reasoning_episodes where episode_key='resolve_open_question_4_entity_fact_uniqueness' order by id desc limit 1").fetchone()
    if decision_row and reasoning_row:
        decision_id = decision_row[0]
        reasoning_id = reasoning_row[0]
        cur.execute(
            "update decisions set origin_reasoning_episode_id=? where id=?",
            (reasoning_id, decision_id),
        )
        cur.execute(
            "update reasoning_episodes set concludes_decision_id=? where id=?",
            (decision_id, reasoning_id),
        )


def create_reasoning_flow_views(cur):
    cur.execute('DROP VIEW IF EXISTS v_reasoning_episode_inputs')
    cur.execute('DROP VIEW IF EXISTS v_reasoning_flow')
    cur.executescript(REASONING_FLOW_VIEW_SQL)


def create_reasoning_quality_views(cur):
    for name in ['v_reasoning_quality', 'v_reasoning_quality_daily', 'v_reasoning_quality_summary']:
        cur.execute(f'DROP VIEW IF EXISTS {name}')
    cur.executescript(REASONING_QUALITY_VIEWS_SQL)


def create_open_question_flow_view(cur):
    cur.execute('DROP VIEW IF EXISTS v_open_question_flow')
    cur.executescript(OPEN_QUESTION_FLOW_VIEW_SQL)


def add_open_question_flow_columns(cur):
    cols = column_names(cur, 'open_questions')
    statements = []
    if 'origin_reasoning_episode_id' not in cols:
        statements.append("ALTER TABLE open_questions ADD COLUMN origin_reasoning_episode_id INTEGER REFERENCES reasoning_episodes(id)")
    if 'resolution_reasoning_episode_id' not in cols:
        statements.append("ALTER TABLE open_questions ADD COLUMN resolution_reasoning_episode_id INTEGER REFERENCES reasoning_episodes(id)")
    if 'resolution_note' not in cols:
        statements.append("ALTER TABLE open_questions ADD COLUMN resolution_note TEXT NOT NULL DEFAULT ''")
    if 'closed_at' not in cols:
        statements.append("ALTER TABLE open_questions ADD COLUMN closed_at TEXT")
    for stmt in statements:
        cur.execute(stmt)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_open_questions_origin_reasoning ON open_questions(origin_reasoning_episode_id) WHERE origin_reasoning_episode_id IS NOT NULL")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_open_questions_resolution_reasoning ON open_questions(resolution_reasoning_episode_id)")


def backfill_open_question_flow(cur):
    existing = {
        row[0]
        for row in cur.execute(
            "select distinct origin_reasoning_episode_id from open_questions where origin_reasoning_episode_id is not null"
        ).fetchall()
    }
    episodes = cur.execute(
        """
        select id, episode_key, title, claim, uncertainty, rejected_alternatives
        from reasoning_episodes
        where resolves_open_question_id is null
          and (coalesce(trim(uncertainty), '') <> '' or coalesce(trim(rejected_alternatives), '') <> '')
        order by id
        """
    ).fetchall()
    for episode_id, episode_key, title, claim, uncertainty, rejected_alternatives in episodes:
        if episode_id in existing:
            continue
        question = f"What remains unresolved in reasoning episode {episode_key}: {title}?"
        if uncertainty and uncertainty.strip():
            question = f"What should be done about: {uncertainty.strip().rstrip('.')}?"
        cur.execute(
            """
            INSERT INTO open_questions(question, status, origin_reasoning_episode_id, resolution_note)
            VALUES(?,?,?,?)
            """,
            (question, 'open', episode_id, ''),
        )


def backfill_open_question_resolutions(cur):
    resolved = cur.execute(
        "select id, question from open_questions where status='resolved' and resolution_reasoning_episode_id is null order by id"
    ).fetchall()
    for open_question_id, question in resolved:
        episode_key = f'open_question_resolution_{open_question_id}'
        cur.execute(
            """
            INSERT INTO reasoning_episodes(
                episode_key, title, claim, evidence_summary, inference,
                rejected_alternatives, uncertainty, confidence, mode_trail,
                next_action, resolves_open_question_id, status, source_mode
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(episode_key) DO NOTHING
            """,
            (
                episode_key,
                f'Resolve open question {open_question_id}',
                f'The legacy open question is marked resolved: {question}',
                'open_questions.status = resolved, but the historical reasoning detail was not preserved.',
                'Represent the legacy resolution explicitly and keep the missing reasoning detail acknowledged.',
                'Inventing a more specific answer without evidence.',
                'Historical resolution detail is unavailable.',
                0.45,
                'backfill -> review',
                '',
                open_question_id,
                'active',
                'reviewed',
            ),
        )


def backfill_decision_history(cur):
    rows = cur.execute(
        """
        select r.receipt_id, r.object_key, r.change_summary, r.provenance_json, r.provenance_complete,
               r.confidence, r.recorded_at, d.decision, d.rationale_summary, d.alternatives,
               d.uncertainty, d.status, d.origin_reasoning_episode_id
        from epistemic_receipts r
        join decisions d on d.id = cast(r.object_key as integer)
        where r.object_type='decision'
        order by cast(r.object_key as integer), r.receipt_id
        """
    ).fetchall()
    version_by_decision = {}
    for receipt_id, object_key, change_summary, provenance_json, provenance_complete, confidence, recorded_at, decision, rationale_summary, alternatives, uncertainty, status, origin_reasoning_episode_id in rows:
        decision_id = int(object_key)
        version = version_by_decision.get(decision_id, 0) + 1
        version_by_decision[decision_id] = version
        cur.execute(
            """
            INSERT INTO decision_versions(
                decision_id, version, decision, rationale_summary, alternatives, uncertainty, status,
                source_receipt_id, origin_reasoning_episode_id, change_summary, provenance_json, provenance_complete, confidence, recorded_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(decision_id, version) DO UPDATE SET
                decision=excluded.decision,
                rationale_summary=excluded.rationale_summary,
                alternatives=excluded.alternatives,
                uncertainty=excluded.uncertainty,
                status=excluded.status,
                source_receipt_id=excluded.source_receipt_id,
                origin_reasoning_episode_id=excluded.origin_reasoning_episode_id,
                change_summary=excluded.change_summary,
                provenance_json=excluded.provenance_json,
                provenance_complete=excluded.provenance_complete,
                confidence=excluded.confidence,
                recorded_at=excluded.recorded_at
            """,
            (
                decision_id,
                version,
                decision,
                rationale_summary,
                alternatives,
                uncertainty,
                status,
                receipt_id,
                origin_reasoning_episode_id,
                change_summary,
                provenance_json,
                provenance_complete,
                confidence,
                recorded_at,
            ),
        )


def create_open_question_flow_triggers(cur):
    drop_trigger(cur, 'reasoning_episode_open_question_seed')
    drop_trigger(cur, 'reasoning_episode_open_question_resolve')
    drop_trigger(cur, 'open_question_resolution_guard')
    drop_trigger(cur, 'open_question_close_stamp')
    cur.executescript(
        """
        CREATE TRIGGER reasoning_episode_open_question_seed AFTER INSERT ON reasoning_episodes
        WHEN NEW.resolves_open_question_id IS NULL AND (COALESCE(trim(NEW.uncertainty), '') <> '' OR COALESCE(trim(NEW.rejected_alternatives), '') <> '')
        BEGIN
          INSERT OR IGNORE INTO open_questions(question, status, origin_reasoning_episode_id, resolution_note)
          VALUES(
            'What remains unresolved in reasoning episode ' || NEW.episode_key || ': ' || NEW.title || '?',
            'open',
            NEW.id,
            ''
          );
          UPDATE open_questions
          SET question='What remains unresolved in reasoning episode ' || NEW.episode_key || ': ' || NEW.title || '?'
          WHERE origin_reasoning_episode_id=NEW.id;
        END;

        CREATE TRIGGER reasoning_episode_open_question_resolve AFTER INSERT ON reasoning_episodes
        WHEN NEW.resolves_open_question_id IS NOT NULL
        BEGIN
          UPDATE open_questions
          SET status='resolved',
              resolution_reasoning_episode_id=NEW.id,
              resolution_note=COALESCE(NULLIF(resolution_note, ''), NEW.title),
              closed_at=COALESCE(closed_at, CURRENT_TIMESTAMP)
          WHERE id=NEW.resolves_open_question_id;
        END;

        CREATE TRIGGER open_question_resolution_guard BEFORE UPDATE OF status, resolution_reasoning_episode_id, resolution_note ON open_questions
        WHEN NEW.status IN ('resolved','skipped')
        BEGIN
          SELECT CASE
            WHEN NEW.status='resolved' AND NEW.resolution_reasoning_episode_id IS NULL THEN RAISE(ABORT, 'resolved open questions require a resolving reasoning episode')
            WHEN NEW.status='skipped' AND trim(COALESCE(NEW.resolution_note, ''))='' THEN RAISE(ABORT, 'skipped open questions require a skip reason')
          END;
        END;

        CREATE TRIGGER open_question_close_stamp AFTER UPDATE OF status ON open_questions
        WHEN NEW.status IN ('resolved','skipped') AND NEW.closed_at IS NULL
        BEGIN
          UPDATE open_questions
          SET closed_at = CURRENT_TIMESTAMP
          WHERE id = NEW.id;
        END;
        """
    )


def create_decision_history_triggers(cur):
    drop_trigger(cur, 'receipt_decision_history')
    cur.executescript(
        """
        CREATE TRIGGER receipt_decision_history AFTER INSERT ON epistemic_receipts
        WHEN NEW.object_type='decision'
        BEGIN
          INSERT INTO decision_versions(
              decision_id, version, decision, rationale_summary, alternatives, uncertainty, status,
              source_receipt_id, origin_reasoning_episode_id, change_summary, provenance_json, provenance_complete, confidence, recorded_at
          )
          SELECT
            d.id,
            COALESCE((SELECT MAX(version) + 1 FROM decision_versions WHERE decision_id = d.id), 1),
            d.decision,
            d.rationale_summary,
            d.alternatives,
            d.uncertainty,
            d.status,
            NEW.receipt_id,
            d.origin_reasoning_episode_id,
            NEW.change_summary,
            NEW.provenance_json,
            NEW.provenance_complete,
            NEW.confidence,
            NEW.recorded_at
          FROM decisions d
          WHERE d.id = CAST(NEW.object_key AS INTEGER)
          ON CONFLICT(decision_id, version) DO UPDATE SET
            decision=excluded.decision,
            rationale_summary=excluded.rationale_summary,
            alternatives=excluded.alternatives,
            uncertainty=excluded.uncertainty,
            status=excluded.status,
            source_receipt_id=excluded.source_receipt_id,
            origin_reasoning_episode_id=excluded.origin_reasoning_episode_id,
            change_summary=excluded.change_summary,
            provenance_json=excluded.provenance_json,
            provenance_complete=excluded.provenance_complete,
            confidence=excluded.confidence,
            recorded_at=excluded.recorded_at;
        END;
        """
    )


def seed_reasoning_episodes(cur):
    cur.execute(
        """
        INSERT INTO reasoning_episodes(
            episode_key, title, claim, evidence_summary, inference,
            rejected_alternatives, uncertainty, confidence, mode_trail,
            next_action, status, source_mode
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(episode_key) DO UPDATE SET
            title=excluded.title,
            claim=excluded.claim,
            evidence_summary=excluded.evidence_summary,
            inference=excluded.inference,
            rejected_alternatives=excluded.rejected_alternatives,
            uncertainty=excluded.uncertainty,
            confidence=excluded.confidence,
            mode_trail=excluded.mode_trail,
            next_action=excluded.next_action,
            status=excluded.status,
            source_mode=excluded.source_mode,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            'gap_report_reasoning_surface',
            'Resolve reasoning surface gaps',
            'Reasoning episodes should be first-class and arguments should appear on the main recall surface.',
            'The gap report found no dedicated reasoning_episode object and found that arguments were absent from v_items and v_recall.',
            'Creating a dedicated reasoning episode table and surfacing arguments makes the DB better at preserving and reusing good thinking.',
            'Leave reasoning only in journal entries; keep arguments hidden in a specialized table; rely on syntheses alone.',
            'The episode shape may need refinement after real usage.',
            0.95,
            'scientist -> builder -> skeptic',
            'Review the new episode after a few uses and refine the schema if needed.',
            'active',
            'derived',
        ),
    )


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


def create_argument_claims_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS argument_claim_links (
            argument_id INTEGER NOT NULL REFERENCES arguments(id) ON DELETE CASCADE,
            belief_id INTEGER NOT NULL REFERENCES beliefs(id) ON DELETE CASCADE,
            relation TEXT NOT NULL DEFAULT 'supports' CHECK(relation IN ('supports','opposes','mixed','refines')),
            strength REAL NOT NULL DEFAULT 0.5 CHECK(strength BETWEEN 0 AND 1),
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (argument_id, belief_id, relation)
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_argument_claim_links_argument ON argument_claim_links(argument_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_argument_claim_links_belief ON argument_claim_links(belief_id)")


def create_argument_claims_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_argument_claims")
    cur.executescript(ARGUMENT_CLAIMS_VIEW_SQL)


def create_decision_options_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_decision_options")
    cur.executescript(DECISION_OPTIONS_VIEW_SQL)


def create_decision_overview_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_decisions")
    cur.execute(DECISION_OVERVIEW_VIEW_SQL)


def create_reasoning_v2_views(cur):
    for name in ['v_item_links', 'v_meta', 'v_explain', 'v_recall', 'v_recall_all', 'v_entry_points', 'v_entry_points_all', 'v_items', 'v_memory_index', 'v_decision_versions', 'v_decision_options', 'v_open_question_flow', 'v_reasoning_episode_inputs', 'v_reasoning_flow']:
        cur.execute(f'DROP VIEW IF EXISTS {name}')
    cur.executescript(RAW_RECALL_VIEWS_SQL)


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


def create_core_model_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_core_model")
    cur.execute(CORE_MODEL_VIEW_SQL)


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


def create_memory_packet_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_memory_packet")
    cur.execute(MEMORY_PACKET_VIEW_SQL)


def create_writeback_policy_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_writeback_policy")
    cur.execute(WRITEBACK_POLICY_VIEW_SQL)


def create_glossary_terms_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_glossary_terms")
    cur.execute(GLOSSARY_TERMS_VIEW_SQL)


def create_provenance_summary_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_provenance_summary")
    cur.execute(PROVENANCE_SUMMARY_VIEW_SQL)


def create_schema_catalog_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_schema_catalog")
    cur.execute("DROP VIEW IF EXISTS v_schema_catalog_all")
    cur.executescript(SCHEMA_CATALOG_ALL_VIEW_SQL + ";\n" + SCHEMA_CATALOG_VIEW_SQL + ";")


def create_tag_search_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_tag_search")
    cur.execute(TAG_SEARCH_VIEW_SQL)


def create_concept_search_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_concept_search")
    cur.execute(CONCEPT_SEARCH_VIEW_SQL)


def create_component_influence_views(cur):
    cur.execute("DROP VIEW IF EXISTS v_component_influence_history")
    cur.execute("DROP VIEW IF EXISTS v_component_influence_presets")
    cur.execute("DROP VIEW IF EXISTS v_component_influence")
    cur.execute("DROP VIEW IF EXISTS v_component_influence_modes")
    cur.executescript(COMPONENT_INFLUENCE_VIEWS_SQL)


def create_convictions_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_convictions")
    cur.executescript(CONVICTIONS_VIEW_SQL)


def create_frame_views(cur):
    for name in ['v_visions', 'v_missions', 'v_strategies', 'v_plans']:
        cur.execute(f'DROP VIEW IF EXISTS {name}')
    cur.executescript(FRAME_VIEWS_SQL)


def create_problem_solving_patterns_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_problem_solving_patterns")
    cur.execute(PROBLEM_SOLVING_PATTERNS_VIEW_SQL)


def create_problem_understanding_patterns_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_problem_understanding_patterns")
    cur.execute(PROBLEM_UNDERSTANDING_PATTERNS_VIEW_SQL)


def create_lean_thinking_patterns_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_lean_thinking_patterns")
    cur.execute(LEAN_THINKING_PATTERNS_VIEW_SQL)


def create_decision_patterns_view(cur):
    cur.execute("DROP VIEW IF EXISTS v_decision_patterns")
    cur.execute(DECISION_PATTERNS_VIEW_SQL)


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


def seed_discovery_concept(cur):
    cur.execute(
        """
        INSERT INTO concepts(concept_key, name, description, status, confidence)
        VALUES(?,?,?,?,?)
        ON CONFLICT(concept_key) DO UPDATE SET
            name=excluded.name,
            description=excluded.description,
            status=excluded.status,
            confidence=excluded.confidence,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            'discovery',
            'Discovery',
            'Finding useful structure, answers, or paths in data, code, or problems.',
            'active',
            0.86,
        ),
    )


def seed_plan_concept(cur):
    cur.execute(
        """
        INSERT INTO concepts(concept_key, name, description, status, confidence)
        VALUES(?,?,?,?,?)
        ON CONFLICT(concept_key) DO UPDATE SET
            name=excluded.name,
            description=excluded.description,
            status=excluded.status,
            confidence=excluded.confidence,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            'plan',
            'Plan',
            'Alias for work_plan; the default-facing term for a work plan.',
            'active',
            0.92,
        ),
    )
    for tag_key, note in [
        ('canonical', 'Canonical alias for work_plan.'),
        ('epistemic:planning', 'Plan is a planning concept and execution surface.'),
    ]:
        cur.execute(
            """
            INSERT INTO object_epistemic_tags(object_type, object_key, tag_key, note)
            VALUES(?,?,?,?)
            ON CONFLICT(object_type, object_key, tag_key) DO UPDATE SET
                note=excluded.note
            """,
            ('concept', 'plan', tag_key, note),
        )


def seed_goal_mission_taxonomy_concepts(cur):
    concepts = [
        ('aim', 'Aim', 'A broad intended direction or effect.', 'active', 0.90),
        ('goal', 'Goal', 'A specific desired target state or condition; if achieved, it yields an outcome.', 'active', 0.92),
        ('mission', 'Mission', 'The enduring purpose that organizes a project’s aims and goals.', 'active', 0.91),
        ('strategy', 'Strategy', 'A chosen approach for pursuing a mission and its goals.', 'active', 0.90),
        ('step', 'Step', 'One executable action inside a plan.', 'active', 0.89),
    ]
    for concept_key, name, description, status, confidence in concepts:
        cur.execute(
            """
            INSERT INTO concepts(concept_key, name, description, status, confidence)
            VALUES(?,?,?,?,?)
            ON CONFLICT(concept_key) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                status=excluded.status,
                confidence=excluded.confidence,
                updated_at=CURRENT_TIMESTAMP
            """,
            (concept_key, name, description, status, confidence),
        )
    tag_rows = {
        'aim': [('epistemic:goal', 'Broad direction or effect, not a concrete delivery.' )],
        'goal': [
            ('epistemic:goal', 'Specific target state or condition.'),
            ('epistemic:requirement', 'A goal can be expressed as a requirement-like target.'),
        ],
        'mission': [('epistemic:goal', 'Enduring purpose that organizes goals.')],
        'strategy': [
            ('epistemic:planning', 'Strategy is the approach that shapes plans.'),
            ('epistemic:reasoning', 'Strategy is chosen by comparing approaches.'),
        ],
        'step': [
            ('epistemic:functional', 'A step is an executable action surface.'),
            ('epistemic:planning', 'A step is part of plan execution.'),
        ],
    }
    for concept_key, rows in tag_rows.items():
        for tag_key, note in rows:
            cur.execute(
                """
                INSERT INTO object_epistemic_tags(object_type, object_key, tag_key, note)
                VALUES(?,?,?,?)
                ON CONFLICT(object_type, object_key, tag_key) DO UPDATE SET
                    note=excluded.note
                """,
                ('concept', concept_key, tag_key, note),
            )


def seed_requirements_glossary_taxonomy_terms(cur):
    terms = [
        ('aim', 'Aim', 'Frame', 'A broad intended direction or effect.', 'Keeps the highest-level direction separate from concrete targets.', 'What broad direction or effect are we aiming for?', 'Improve the onboarding experience for new users.', 'Treat the aim as a task list.', 8, 0.90, 30),
        ('goal', 'Goal', 'Frame', 'A specific desired target state or condition; if achieved, it yields an outcome.', 'Keeps the target state distinct from the realized result.', 'What specific target state do we want?', 'Reduce onboarding support delay to four hours.', 'Call the goal the outcome before it has happened.', 8, 0.92, 31),
        ('mission', 'Mission', 'Frame', 'The enduring purpose that organizes a project’s aims and goals.', 'Provides a stable reason for the project and its work.', 'What enduring purpose does this project serve?', 'Help new users succeed at onboarding with less friction.', 'Use the mission as a one-off task.', 8, 0.91, 32),
        ('strategy', 'Strategy', 'Analyze', 'A chosen approach for pursuing a mission and its goals.', 'Turns the mission into a deliberate path.', 'What approach will best reach the mission and goals?', 'Start with guided setup, then simplify the remaining tasks.', 'Confuse the strategy with the execution plan.', 8, 0.90, 33),
        ('plan', 'Plan', 'Specify', 'The ordered execution path that turns strategy into actionable work.', 'Makes the intended sequence of work explicit.', 'What ordered execution path gets us there?', 'First reduce the support queue, then simplify onboarding, then measure the change.', 'Treat the plan as a vague intention.', 8, 0.92, 34),
        ('step', 'Step', 'Manage', 'One executable action inside a plan.', 'Keeps execution concrete and tractable.', 'What is the next executable action in the plan?', 'Update the onboarding checklist.', 'Bundle many actions into one step.', 8, 0.89, 35),
    ]
    for term_key, term, phase, definition, why_it_matters, elegant_prompt, good_example, anti_pattern, primary_source_id, confidence, sort_order in terms:
        cur.execute(
            """
            INSERT INTO requirements_glossary_terms(
                term_key, term, phase, definition, why_it_matters,
                elegant_prompt, good_example, anti_pattern, primary_source_id,
                confidence, sort_order, status
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?, 'active')
            ON CONFLICT(term_key) DO UPDATE SET
                term=excluded.term,
                phase=excluded.phase,
                definition=excluded.definition,
                why_it_matters=excluded.why_it_matters,
                elegant_prompt=excluded.elegant_prompt,
                good_example=excluded.good_example,
                anti_pattern=excluded.anti_pattern,
                primary_source_id=excluded.primary_source_id,
                confidence=excluded.confidence,
                sort_order=excluded.sort_order,
                status=excluded.status
            """,
            (term_key, term, phase, definition, why_it_matters, elegant_prompt, good_example, anti_pattern, primary_source_id, confidence, sort_order),
        )


def seed_discovery_plan_links(cur):
    links = [
        ('formal_analysis_workflow', 'supports', 'Discovery helps structure problem analysis and evidence review.'),
        ('db_improvement_control_flow', 'supports', 'Discovery helps surface better retrieval paths and relationships in the DB.'),
        ('canonical_home_enforcement', 'supports', 'Discovery helps find the primary home for repeated ideas and routes.'),
        ('dependency_first_planning', 'supports', 'Discovery helps uncover hidden dependencies before execution.'),
        ('learn_topic_fast', 'supports', 'Discovery helps find the useful structure of a new topic quickly.'),
        ('mindmap_term_loop', 'supports', 'Discovery helps expand a term into connected structure.'),
        ('out_of_the_box_thinking', 'supports', 'Discovery helps explore unusual paths and alternative frames.'),
        ('reasoning_pattern_reuse_plan', 'supports', 'Discovery helps find reusable patterns across similar problems.'),
        ('core_thinking_patterns', 'supports', 'Discovery helps identify patterns worth operationalizing.'),
    ]
    for plan_key, relation, note in links:
        cur.execute(
            """
            INSERT INTO concept_links(concept_key, object_type, object_key, relation, note)
            VALUES(?,?,?,?,?)
            ON CONFLICT(concept_key, object_type, object_key, relation) DO UPDATE SET
                note=excluded.note
            """,
            ('discovery', 'work_plan', plan_key, relation, note),
        )


def seed_db_optimization_concepts(cur):
    concepts = [
        ('system', 'System', 'A bounded whole made of parts, relations, inputs, outputs, feedback, and purpose.', 0.92),
        ('influence', 'Influence', 'How internal engine elements or external forces change thinking, state, or outcomes.', 0.89),
        ('overlap_reduction', 'Overlap Reduction', 'Finding duplicated or near-duplicated ideas and collapsing them into one canonical home.', 0.87),
        ('schema_catalog', 'Schema Catalog', 'A searchable index of tables, views, and entry points for navigating the database.', 0.90),
    ]
    for concept_key, name, description, confidence in concepts:
        cur.execute(
            """
            INSERT INTO concepts(concept_key, name, description, status, confidence)
            VALUES(?,?,?,?,?)
            ON CONFLICT(concept_key) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                status=excluded.status,
                confidence=excluded.confidence,
                updated_at=CURRENT_TIMESTAMP
            """,
            (concept_key, name, description, 'active', confidence),
        )
        if concept_key == 'system':
            cur.execute(
                """
                INSERT INTO object_epistemic_tags(object_type, object_key, tag_key, note)
                VALUES(?,?,?,?)
                ON CONFLICT(object_type, object_key, tag_key) DO UPDATE SET
                    note=excluded.note
                """,
                ('concept', 'system', 'system', 'System concept tagged as system.'),
            )
        if concept_key == 'influence':
            for tag_key, note in [
                ('epistemic:reasoning', 'Influence changes how the engine weighs or chooses.'),
                ('epistemic:state', 'Influence can describe a current operating condition or pressure.'),
                ('epistemic:constraint', 'Influence can act as an external force or limiting condition.'),
            ]:
                cur.execute(
                    """
                    INSERT INTO object_epistemic_tags(object_type, object_key, tag_key, note)
                    VALUES(?,?,?,?)
                    ON CONFLICT(object_type, object_key, tag_key) DO UPDATE SET
                        note=excluded.note
                    """,
                    ('concept', 'influence', tag_key, note),
                )


def seed_db_optimization_links(cur):
    links = [
        ('system', 'concept', 'system_recognition_heuristic', 'supports', 'The system concept is clarified by heuristics for recognizing systems.'),
        ('system', 'concept', 'system_nesting_heuristic', 'supports', 'The system concept is clarified by heuristics for finding nested systems.'),
        ('system', 'concept', 'thinking_engine_system_elements', 'supports', 'The system concept is clarified by named system elements.'),
        ('influence', 'concept', 'system', 'supports', 'Influence is easiest to interpret within a bounded system.'),
        ('influence', 'concept', 'thinking_engine_system_elements', 'supports', 'Influence can act on the engine through attention, memory, reasoning, and policy.'),
        ('canonical_home_enforcement', 'concept', 'overlap_reduction', 'supports', 'Canonical-home routing depends on reducing overlap first.'),
        ('canonical_home_enforcement', 'concept', 'schema_catalog', 'supports', 'Canonical-home routing is easier with a searchable schema catalog.'),
        ('canonical_home_enforcement', 'concept', 'discovery', 'supports', 'Discovery helps find the right home and route.'),
        ('overlap_reduction', 'concept', 'canonical_home_enforcement', 'supports', 'Overlap reduction is implemented through canonical homes.'),
        ('overlap_reduction', 'concept', 'correction', 'supports', 'Overlap reduction improves when mistakes are corrected explicitly.'),
        ('schema_catalog', 'concept', 'entrypoint', 'supports', 'A schema catalog should surface canonical entrypoints quickly.'),
        ('schema_catalog', 'concept', 'discovery', 'supports', 'A schema catalog powers discovery of useful structures.'),
        ('schema_catalog', 'concept', 'canonical_home_enforcement', 'supports', 'A schema catalog makes canonical-home routing easier to apply.'),
        ('entrypoint', 'concept', 'discovery', 'supports', 'An entrypoint should help discovery start from a canonical place.'),
        ('entrypoint', 'concept', 'schema_catalog', 'supports', 'An entrypoint should be visible in the schema catalog.'),
        ('correction', 'concept', 'overlap_reduction', 'supports', 'Correction helps reduce overlap by fixing missed or duplicate ideas.'),
    ]
    for concept_key, object_type, object_key, relation, note in links:
        cur.execute(
            """
            INSERT INTO concept_links(concept_key, object_type, object_key, relation, note)
            VALUES(?,?,?,?,?)
            ON CONFLICT(concept_key, object_type, object_key, relation) DO UPDATE SET
                note=excluded.note
            """,
            (concept_key, object_type, object_key, relation, note),
        )


def seed_quality_plan_links(cur):
    links = [
        ('quality', 'work_plan', 'core_thinking_patterns', 'supports', 'Core thinking patterns should improve output quality by making analysis more reliable.'),
        ('quality', 'work_plan', 'elegant_requirements_glossary', 'supports', 'Clear requirements language improves quality of the resulting glossary.'),
        ('quality', 'work_plan', 'high_quality_code_plan', 'supports', 'The plan directly targets high-quality code habits and outputs.'),
        ('quality', 'work_plan', 'personal_ai_survival_plan', 'supports', 'Survival planning depends on quality judgments under disruption.'),
        ('quality', 'work_plan', 'seven_basic_tools_quality_integration', 'supports', 'This plan is explicitly about integrating quality tools.'),
        ('quality', 'work_plan', 'super_sharp_thinking_engine', 'supports', 'Sharper thinking should improve quality, clarity, and usefulness.'),
    ]
    for concept_key, object_type, object_key, relation, note in links:
        cur.execute(
            """
            INSERT INTO concept_links(concept_key, object_type, object_key, relation, note)
            VALUES(?,?,?,?,?)
            ON CONFLICT(concept_key, object_type, object_key, relation) DO UPDATE SET
                note=excluded.note
            """,
            (concept_key, object_type, object_key, relation, note),
        )

def seed_canonical_tag(cur):
    cur.execute(
        """
        INSERT INTO epistemic_tags(tag_key, label, description)
        VALUES(?,?,?)
        ON CONFLICT(tag_key) DO UPDATE SET
            label=excluded.label,
            description=excluded.description
        """,
        ('canonical', 'Canonical', 'Marks default-facing objects and surfaces.'),
    )
    schema_objects = [
        'v_core_model',
        'v_recall',
        'v_entry_points',
        'v_concept_search',
        'v_decisions',
        'v_memory_index',
        'v_schema_catalog',
        'v_storage_map',
        'v_meta',
        'v_item_links',
        'v_object_epistemic_tags',
        'v_tag_search',
        'decisions',
        'open_questions',
        'work_plans',
        'work_plan_steps',
        'reasoning_episodes',
        'metacognitive_state',
        'continuity_requirements',
        'syntheses',
        'epistemic_receipts',
        'projects',
        'observations',
        'journal',
        'object_metadata',
        'object_provenance',
    ]
    for object_name in schema_objects:
        cur.execute(
            """
            INSERT INTO object_epistemic_tags(object_type, object_key, tag_key, note)
            VALUES(?,?,?,?)
            ON CONFLICT(object_type, object_key, tag_key) DO UPDATE SET
                note=excluded.note
            """,
            ('schema_object', object_name, 'canonical', 'Canonical default-facing schema object.'),
        )
    recall_source_types = [
        'decision',
        'open_question',
        'journal',
        'observation',
        'reasoning_episode',
        'work_plan',
        'work_plan_step',
        'project',
        'synthesis',
        'synthesis_conflict',
        'metacognitive_state',
        'continuity_requirement',
        'epistemic_receipt',
        'concept_search',
    ]
    for source_type in recall_source_types:
        cur.execute(
            """
            INSERT INTO object_epistemic_tags(object_type, object_key, tag_key, note)
            VALUES(?,?,?,?)
            ON CONFLICT(object_type, object_key, tag_key) DO UPDATE SET
                note=excluded.note
            """,
            ('recall_source_type', source_type, 'canonical', 'Canonical default-facing recall source type.'),
        )


def seed_persona_tag(cur):
    cur.execute(
        """
        INSERT INTO epistemic_tags(tag_key, label, description)
        VALUES(?,?,?)
        ON CONFLICT(tag_key) DO UPDATE SET
            label=excluded.label,
            description=excluded.description
        """,
        ('persona', 'Persona', 'Marks persona-mode metacognitive state entries.'),
    )
    cur.execute(
        """
        INSERT INTO epistemic_tags(tag_key, label, description)
        VALUES(?,?,?)
        ON CONFLICT(tag_key) DO UPDATE SET
            label=excluded.label,
            description=excluded.description
        """,
        ('system', 'System', 'Marks system-level metacognitive state entries, including derived persona-to-system classification.'),
    )
    cur.execute(
        """
        INSERT INTO epistemic_tags(tag_key, label, description)
        VALUES(?,?,?)
        ON CONFLICT(tag_key) DO UPDATE SET
            label=excluded.label,
            description=excluded.description
        """,
        ('trait', 'Trait', 'Marks reusable persona traits such as curiosity, caution, structure, and patience.'),
    )
    personas = ['persona_alien','persona_builder','persona_child','persona_explorer','persona_insect','persona_moderator','persona_scholar','persona_skeptic','persona_super_ai','persona_synthesizer','persona_system_analyst']
    for state_key in personas:
        row = cur.execute("select 1 from metacognitive_state where state_key=?", (state_key,)).fetchone()
        if row:
            for tag_key, note in [('persona', 'Persona-mode state entry.'), ('system', 'Derived system-level classification for persona-mode state entry.'), ('trait', 'Derived trait classification from persona-mode text.')]:
                cur.execute(
                    """
                    INSERT INTO object_epistemic_tags(object_type, object_key, tag_key, note)
                    VALUES(?,?,?,?)
                    ON CONFLICT(object_type, object_key, tag_key) DO UPDATE SET
                        note=excluded.note
                    """,
                    ('metacognitive_state', state_key, tag_key, note),
                )


def seed_mistake_recording_policy(cur):
    cur.execute(
        """
        INSERT INTO recording_policy(trigger, enabled, description)
        VALUES(?,?,?)
        ON CONFLICT(trigger) DO UPDATE SET
            enabled=excluded.enabled,
            description=excluded.description
        """,
        (
            'mistake_discovered',
            1,
            'Record when a mistake, omission, or missed link is discovered.',
        ),
    )


def seed_memory_mvp_requirements(cur):
    parent_row = cur.execute("select id from continuity_requirements where requirement_key='CDB-01'").fetchone()
    if not parent_row:
        raise RuntimeError('CDB-01 must exist before seeding memory MVP requirements')
    parent_id = parent_row[0]
    requirements = [
        (
            'CDB-01.4',
            'Layered working packet',
            2,
            parent_id,
            'functional',
            'The recall path shall produce a compact working packet that groups retrieved items into episodic, semantic, procedural, and metacognitive layers.',
            'Reasoning needs a small, structured context instead of a raw dump of matches.',
            'A recall call can return a layer-separated packet that is usable immediately for reasoning.',
            'high',
            0.94,
            'database_state',
            'Derived from the memory-assisted thinking MVP upgrade plan.',
        ),
        (
            'CDB-01.5',
            'Ranked recall scoring',
            2,
            parent_id,
            'functional',
            'Recall results shall be ranked using relevance, confidence, and recency before packaging.',
            'Useful memory must surface the most relevant items first and down-rank weaker matches.',
            'A controlled recall query returns stronger exact matches before weaker partial matches.',
            'high',
            0.94,
            'database_state',
            'Derived from the memory-assisted thinking MVP upgrade plan.',
        ),
        (
            'CDB-01.6',
            'Auditable writeback policy',
            2,
            parent_id,
            'functional',
            'The database shall expose an auditable writeback policy that governs what memory is stored after each turn.',
            'Writeback must be explicit so belief updates, episode notes, and open questions are not stored arbitrarily.',
            'A policy view exposes the active recording triggers and the current storage policy summary.',
            'high',
            0.94,
            'database_state',
            'Derived from the memory-assisted thinking MVP upgrade plan.',
        ),
        (
            'CDB-01.7',
            'Condition-aware memory recall',
            2,
            parent_id,
            'functional',
            'The recall path shall support condition metadata for memory entries and use that condition in matching.',
            'Some memory items need a contextual guard or trigger separate from scope so recall can surface them when the condition matches.',
            'A recall call can retrieve items by condition metadata and returns the condition alongside the hit.',
            'high',
            0.94,
            'database_state',
            'Derived from the memory-assisted thinking MVP upgrade plan.',
        ),
    ]
    for requirement in requirements:
        cur.execute(
            """
            INSERT OR IGNORE INTO continuity_requirements(
                requirement_key, title, requirement_level, parent_requirement_id,
                requirement_type, statement, rationale, acceptance_summary,
                priority, confidence, provenance_key, source_reference
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            requirement,
        )


def seed_scientist_mode_routes(cur):
    routes = [
        ('scientist_on', r'^(mode\s+scientist\s+on|scientist\s+on)$', "python3 mode_command.py scientist on --db continuity.db", 'Enable scientist mode and switch the active role state to scientist.'),
        ('scientist_off', r'^(mode\s+scientist\s+off|scientist\s+off)$', "python3 mode_command.py scientist off --db continuity.db", 'Disable scientist mode and reset the active role state to general.'),
        ('scientist_status', r'^(mode\s+scientist\s+status|scientist\s+status)$', "python3 mode_command.py scientist status --db continuity.db", 'Show scientist mode and active role state.'),
        ('scientist_analyse', r'^scientist\s+analyse\s+.+$', "python3 scientist_command.py analyse <topic-or-file> --db continuity.db", 'Create a scientist Markdown analysis for a topic or file.'),
        ('memory_recall', r'^(memory\s+recall\s+.+|recall\s+.+)$', "python3 memory_command.py recall <query> --db continuity.db", 'Recall the most relevant stored memory-like items for a query.'),
        ('plan_status', r'^plan\s+status$', "python3 plan_command.py status --db continuity.db", 'Show the current primary goal, active plans, steps, and blockers.'),
        ('plan_goal_set', r'^plan\s+goal\s+set\s+.+$', "python3 plan_command.py goal set <goal> --db continuity.db", 'Set the durable primary goal and record a lightweight planning episode.'),
        ('plan_plan_start', r'^plan\s+plan\s+start\s+.+$', "python3 plan_command.py plan start <plan_key> <title> <objective> --db continuity.db", 'Start or update a lightweight active work plan.'),
        ('plan_step_add', r'^plan\s+step\s+add\s+.+$', "python3 plan_command.py step add <plan_key> <step_key> <description> --db continuity.db", 'Add a pending step to an active plan.'),
        ('plan_step_done', r'^plan\s+step\s+done\s+.+$', "python3 plan_command.py step done <plan_key> <step_key> --db continuity.db", 'Mark a plan step as completed.'),
        ('plan_step_block', r'^plan\s+step\s+block\s+.+$', "python3 plan_command.py step block <plan_key> <step_key> <question> --db continuity.db", 'Record a blocker as an open question.'),
        ('synthesis_promote', r'^synthesis\s+promote\s+.+$', "python3 plan_command.py synthesis promote <synthesis_key> [state_key] --db continuity.db", 'Promote a settled synthesis into metacognitive state when no policy row exists yet.'),
        ('project_goal_set', r'^project\s+goal\s+set\s+.+$', "python3 project_command.py goal set <project_name> <goal> --db continuity.db", 'Set a project-specific goal for a mission.'),
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
            where p.state_key is null and h.state_key <> 'persona_editor'
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

    for view_name in [
        "v_storage_map",
        "v_core_model",
        "v_ethics_principles_map",
        "v_ethics_principle_checks",
        "v_scientist_mode_state",
        "v_glossary_terms",
        "v_provenance_summary",
        "v_visions",
        "v_missions",
        "v_strategies",
        "v_plans",
        "v_convictions",
        "v_items",
        "v_item_links",
        "v_argument_claims",
        "v_recall",
        "v_explain",
        "v_meta",
        "v_entry_points_all",
        "v_entry_points",
        "v_memory_index",
        "v_recall_all",
        "v_schema_catalog_all",
        "v_schema_catalog",
        "v_tag_search",
        "v_component_influence_modes",
        "v_component_influence",
        "v_component_influence_history",
        "v_decision_versions",
        "v_decision_options",
        "v_open_question_flow",
        "v_reasoning_episode_inputs",
        "v_reasoning_flow",
        "v_reasoning_quality",
        "v_reasoning_quality_daily",
        "v_reasoning_quality_summary",
    ]:
        if cur.execute("select 1 from sqlite_master where type='view' and name=?", (view_name,)).fetchone() is None:
            issues.append((f'{view_name}_missing', [f'{view_name} missing'], []))

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

    mistake_policy = cur.execute("select enabled, description from recording_policy where trigger='mistake_discovered'").fetchone()
    if mistake_policy != (1, 'Record when a mistake, omission, or missed link is discovered.'):
        issues.append(("mistake_recording_policy", mistake_policy, (1, 'Record when a mistake, omission, or missed link is discovered.')))

    discovery_concept = cur.execute("select name, description from concepts where concept_key='discovery'").fetchone()
    if not discovery_concept:
        issues.append(("discovery_concept", discovery_concept, ('Discovery', 'Finding useful structure, answers, or paths in data, code, or problems.')))
    elif discovery_concept[0] != 'Discovery' or 'external' in discovery_concept[1].lower():
        issues.append(("discovery_concept_text", discovery_concept, ('Discovery', 'no external')))

    overlap_concept = cur.execute("select name, description from concepts where concept_key='overlap_reduction'").fetchone()
    if not overlap_concept:
        issues.append(("overlap_reduction_concept", overlap_concept, ('Overlap Reduction', 'Finding duplicated or near-duplicated ideas and collapsing them into one canonical home.')))
    schema_concept = cur.execute("select name, description from concepts where concept_key='schema_catalog'").fetchone()
    if not schema_concept:
        issues.append(("schema_catalog_concept", schema_concept, ('Schema Catalog', 'A searchable index of tables, views, and entry points for navigating the database.')))
    entrypoint_concept = cur.execute("select name, description from concepts where concept_key='entrypoint'").fetchone()
    if not entrypoint_concept:
        issues.append(("entrypoint_concept", entrypoint_concept, ('Entrypoint', 'Canonical starting point for querying and navigating continuity.db; aligns with v_entry_points.')))
    persona_tag = cur.execute("select label, description from epistemic_tags where tag_key='persona'").fetchone()
    if not persona_tag:
        issues.append(("persona_tag", persona_tag, ('Persona', 'Marks persona-mode metacognitive state entries.')))
    system_tag = cur.execute("select label, description from epistemic_tags where tag_key='system'").fetchone()
    if not system_tag:
        issues.append(("system_tag", system_tag, ('System', 'Marks system-level metacognitive state entries, including derived persona-to-system classification.')))
    trait_tag = cur.execute("select label, description from epistemic_tags where tag_key='trait'").fetchone()
    if not trait_tag:
        issues.append(("trait_tag", trait_tag, ('Trait', 'Marks reusable persona traits such as curiosity, caution, structure, and patience.')))
    canonical_tag = cur.execute("select label, description from epistemic_tags where tag_key='canonical'").fetchone()
    if not canonical_tag:
        issues.append(("canonical_tag", canonical_tag, ('Canonical', 'Marks default-facing objects and surfaces.')))
    canonical_schema_count = cur.execute("select count(*) from object_epistemic_tags where tag_key='canonical' and object_type='schema_object'").fetchone()[0]
    if canonical_schema_count < 10:
        issues.append(("canonical_schema_object_tags", canonical_schema_count, '>=10'))
    canonical_recall_count = cur.execute("select count(*) from object_epistemic_tags where tag_key='canonical' and object_type='recall_source_type'").fetchone()[0]
    if canonical_recall_count < 6:
        issues.append(("canonical_recall_source_tags", canonical_recall_count, '>=6'))
    canonical_schema_view = cur.execute("select count(*) from v_schema_catalog").fetchone()[0]
    canonical_recall_view = cur.execute("select count(*) from v_recall").fetchone()[0]
    if canonical_schema_view < 5:
        issues.append(("canonical_schema_view_count", canonical_schema_view, '>=5'))
    if canonical_recall_view < 5:
        issues.append(("canonical_recall_view_count", canonical_recall_view, '>=5'))
    system_concept = cur.execute("select name, description from concepts where concept_key='system'").fetchone()
    if not system_concept:
        issues.append(("system_concept", system_concept, ('System', 'A bounded whole made of parts, relations, inputs, outputs, feedback, and purpose.')))
    influence_concept = cur.execute("select name, description from concepts where concept_key='influence'").fetchone()
    if not influence_concept:
        issues.append(("influence_concept", influence_concept, ('Influence', 'How internal engine elements or external forces change thinking, state, or outcomes.')))
    system_concept_tagged = cur.execute("select count(*) from object_epistemic_tags where tag_key='system' and object_type='concept' and object_key='system'").fetchone()[0]
    if system_concept_tagged != 1:
        issues.append(("system_concept_tagged", system_concept_tagged, 1))
    influence_tagged = cur.execute("select count(*) from object_epistemic_tags where object_type='concept' and object_key='influence' and tag_key in ('epistemic:reasoning','epistemic:state','epistemic:constraint')").fetchone()[0]
    if influence_tagged != 3:
        issues.append(("influence_tagged", influence_tagged, 3))
    quality_plan_count = cur.execute("select count(*) from concept_links where concept_key='quality' and object_type='work_plan'").fetchone()[0]
    if quality_plan_count < 6:
        issues.append(("quality_work_plan_links", quality_plan_count, '>=6'))
    if cur.execute("select 1 from sqlite_master where type='table' and name='component_influence_modes'").fetchone() is None:
        issues.append(("component_influence_modes_missing", ["component_influence_modes missing"], []))
    else:
        mode_count = cur.execute("select count(*) from component_influence_modes").fetchone()[0]
        if mode_count < 5:
            issues.append(("component_influence_modes_count", mode_count, '>=5'))
    if cur.execute("select 1 from sqlite_master where type='table' and name='component_influence'").fetchone() is None:
        issues.append(("component_influence_missing", ["component_influence missing"], []))
    else:
        influence_count = cur.execute("select count(*) from component_influence").fetchone()[0]
        if influence_count < 10:
            issues.append(("component_influence_count", influence_count, '>=10'))
    if cur.execute("select 1 from sqlite_master where type='table' and name='component_influence_presets'").fetchone() is None:
        issues.append(("component_influence_presets_missing", ["component_influence_presets missing"], []))
    else:
        preset_count = cur.execute("select count(*) from component_influence_presets").fetchone()[0]
        if preset_count < 20:
            issues.append(("component_influence_presets_count", preset_count, '>=20'))
        default_preset_count = cur.execute("select count(*) from component_influence_presets where mode_key='default'").fetchone()[0]
        if default_preset_count < 10:
            issues.append(("component_influence_default_preset_count", default_preset_count, '>=10'))
    if cur.execute("select 1 from sqlite_master where type='view' and name='v_component_influence'").fetchone() is None:
        issues.append(("component_influence_view_missing", ["v_component_influence missing"], []))
    if cur.execute("select 1 from sqlite_master where type='view' and name='v_component_influence_presets'").fetchone() is None:
        issues.append(("component_influence_presets_view_missing", ["v_component_influence_presets missing"], []))
    if cur.execute("select 1 from sqlite_master where type='view' and name='v_component_influence_history'").fetchone() is None:
        issues.append(("component_influence_history_view_missing", ["v_component_influence_history missing"], []))
    if cur.execute("select 1 from sqlite_master where type='view' and name='v_component_influence_modes'").fetchone() is None:
        issues.append(("component_influence_modes_view_missing", ["v_component_influence_modes missing"], []))
    if cur.execute("select 1 from sqlite_master where type='table' and name='component_influence_history'").fetchone() is None:
        issues.append(("component_influence_history_missing", ["component_influence_history missing"], []))
    influence_mode_keys = {row[0] for row in cur.execute("select mode_key from component_influence_modes")}
    if not {'default','high_attention','low_attention','startup','error_recovery','evolved'}.issubset(influence_mode_keys):
        issues.append(("component_influence_modes_seeded", sorted(influence_mode_keys), ['default','high_attention','low_attention','startup','error_recovery','evolved']))
    error_plan = cur.execute("select id from work_plans where plan_key='error_recovery_influence_flow'").fetchone()
    if not error_plan:
        issues.append(("error_recovery_influence_flow_missing", ["error_recovery_influence_flow missing"], []))
    else:
        step_count = cur.execute("select count(*) from work_plan_steps where plan_id=?", (error_plan[0],)).fetchone()[0]
        if step_count < 5:
            issues.append(("error_recovery_influence_flow_steps", step_count, '>=5'))
        link_count = cur.execute("select count(*) from concept_links where object_type='work_plan' and object_key='error_recovery_influence_flow'").fetchone()[0]
        if link_count < 10:
            issues.append(("error_recovery_influence_flow_links", link_count, '>=10'))
    demo_plan = cur.execute("select id from work_plans where plan_key='evolved_baseline_demo'").fetchone()
    if not demo_plan:
        issues.append(("evolved_baseline_demo_missing", ["evolved_baseline_demo missing"], []))
    else:
        demo_steps = cur.execute("select count(*) from work_plan_steps where plan_id=?", (demo_plan[0],)).fetchone()[0]
        if demo_steps < 5:
            issues.append(("evolved_baseline_demo_steps", demo_steps, '>=5'))
        demo_links = cur.execute("select count(*) from concept_links where object_type='work_plan' and object_key='evolved_baseline_demo'").fetchone()[0]
        if demo_links < 8:
            issues.append(("evolved_baseline_demo_links", demo_links, '>=8'))

    system_tagged = cur.execute("select count(*) from object_epistemic_tags where tag_key='system' and object_type='metacognitive_state' and object_key like 'persona_%'").fetchone()[0]
    persona_system_count = cur.execute("select count(*) from object_epistemic_tags where tag_key='system' and object_type='metacognitive_state' and object_key like 'persona_%'").fetchone()[0]
    if persona_system_count < 1:
        issues.append(("persona_system_tag_links", persona_system_count, '>=1'))
    persona_trait_count = cur.execute("select count(*) from object_epistemic_tags where tag_key='trait' and object_type='metacognitive_state' and object_key like 'persona_%'").fetchone()[0]
    if persona_trait_count < 1:
        issues.append(("persona_trait_tag_links", persona_trait_count, '>=1'))

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
    memory_mvp_req = cur.execute("select count(*) from continuity_requirements where requirement_key in ('CDB-01.3','CDB-01.4','CDB-01.5','CDB-01.6','CDB-01.7') and status='active'").fetchone()[0]
    if memory_mvp_req != 5:
        issues.append(("memory_mvp_requirements", memory_mvp_req, 5))
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

    if cur.execute("select 1 from sqlite_master where type='table' and name='reasoning_episodes'").fetchone() is None:
        issues.append(("reasoning_episodes_missing", ["reasoning_episodes missing"], []))
    else:
        reasoning_surface = cur.execute("select count(*) from v_items where item_kind='reasoning_episode'").fetchone()[0]
        reasoning_total = cur.execute("select count(*) from reasoning_episodes").fetchone()[0]
        if reasoning_surface != reasoning_total:
            issues.append(("reasoning_episode_surface", reasoning_surface, reasoning_total))
        argument_surface = cur.execute("select count(*) from v_items where item_kind='argument'").fetchone()[0]
        argument_total = cur.execute("select count(*) from arguments").fetchone()[0]
        if argument_surface != argument_total:
            issues.append(("argument_surface", argument_surface, argument_total))
        if cur.execute("select 1 from sqlite_master where type='table' and name='argument_claim_links'").fetchone() is not None:
            argument_claim_total = cur.execute("select count(*) from v_argument_claims").fetchone()[0]
            if argument_claim_total < argument_total:
                issues.append(("argument_claim_surface", argument_claim_total, argument_total))
        if cur.execute("select 1 from sqlite_master where type='table' and name='reasoning_episode_inputs'").fetchone() is None:
            issues.append(("reasoning_episode_inputs_missing", ["reasoning_episode_inputs missing"], []))
        else:
            input_count = cur.execute("select count(*) from reasoning_episode_inputs").fetchone()[0]
            linked_count = cur.execute("select count(*) from reasoning_episodes r join reasoning_episode_inputs i on i.episode_id=r.id").fetchone()[0]
            if input_count != linked_count:
                issues.append(("reasoning_episode_input_links", linked_count, input_count))
            no_input = cur.execute("""
                select count(*)
                from reasoning_episodes r
                left join reasoning_episode_inputs i on i.episode_id=r.id
                group by r.id
                having count(i.episode_id)=0
            """).fetchall()
            if no_input:
                issues.append(("reasoning_episode_missing_inputs", len(no_input), 0))
        if cur.execute("select 1 from sqlite_master where type='view' and name='v_reasoning_flow'").fetchone() is None:
            issues.append(("reasoning_flow_view_missing", ["v_reasoning_flow missing"], []))

    if cur.execute("select 1 from sqlite_master where type='table' and name='decision_versions'").fetchone() is None:
        issues.append(("decision_versions_missing", ["decision_versions missing"], []))
    else:
        decision_receipts = cur.execute("select count(*) from epistemic_receipts where object_type='decision'").fetchone()[0]
        decision_versions = cur.execute("select count(*) from decision_versions").fetchone()[0]
        if decision_versions != decision_receipts:
            issues.append(("decision_history_surface", decision_versions, decision_receipts))
        if cur.execute("select 1 from sqlite_master where type='table' and name='decisions'").fetchone() is not None:
            origin_linked = cur.execute("select count(*) from decisions where origin_reasoning_episode_id is not null").fetchone()[0]
            conclude_linked = cur.execute("select count(*) from reasoning_episodes where concludes_decision_id is not null").fetchone()[0]
            if origin_linked != conclude_linked:
                issues.append(("reasoning_decision_link_surface", origin_linked, conclude_linked))
            origin_mismatch = cur.execute("""
                select count(*)
                from decisions d
                join reasoning_episodes r on r.id = d.origin_reasoning_episode_id
                where r.concludes_decision_id is not null and r.concludes_decision_id <> d.id
            """).fetchone()[0]
            conclude_mismatch = cur.execute("""
                select count(*)
                from reasoning_episodes r
                join decisions d on d.id = r.concludes_decision_id
                where d.origin_reasoning_episode_id is not null and d.origin_reasoning_episode_id <> r.id
            """).fetchone()[0]
            if origin_mismatch:
                issues.append(("reasoning_decision_origin_mismatch", origin_mismatch, 0))
            if conclude_mismatch:
                issues.append(("reasoning_decision_conclude_mismatch", conclude_mismatch, 0))

    if cur.execute("select 1 from sqlite_master where type='table' and name='open_questions'").fetchone() is None:
        issues.append(("open_questions_missing", ["open_questions missing"], []))
    else:
        expected_open_questions = cur.execute("""
            select count(*)
            from reasoning_episodes
            where resolves_open_question_id is null
              and (coalesce(trim(uncertainty), '') <> '' or coalesce(trim(rejected_alternatives), '') <> '')
        """).fetchone()[0]
        linked_open_questions = cur.execute("select count(*) from open_questions where origin_reasoning_episode_id is not null").fetchone()[0]
        if linked_open_questions < expected_open_questions:
            issues.append(("open_question_seed_surface", linked_open_questions, expected_open_questions))
        unresolved_ok = cur.execute("""
            select count(*)
            from open_questions
            where status='resolved' and resolution_reasoning_episode_id is null
        """).fetchone()[0]
        skipped_ok = cur.execute("""
            select count(*)
            from open_questions
            where status='skipped' and trim(coalesce(resolution_note, ''))=''
        """).fetchone()[0]
        if unresolved_ok:
            issues.append(("open_question_resolution_link", unresolved_ok, 0))
        if skipped_ok:
            issues.append(("open_question_skip_reason", skipped_ok, 0))

    return issues


def apply_migration():
    conn = connect()
    cur = conn.cursor()
    add_receipt_kind_column(cur)
    add_action_check_principle_column(cur)
    backfill_receipt_kind(cur)
    backfill_belief_version_evidence_summary(cur)
    backfill_epistemic_receipt_provenance(cur)
    ensure_indexes(cur)
    create_reasoning_episode_tables(cur)
    add_reasoning_episode_columns(cur)
    create_reasoning_episode_inputs_table(cur)
    create_decision_history_tables(cur)
    create_decision_options_table(cur)
    add_decision_history_columns(cur)
    add_decision_flow_columns(cur)
    add_open_question_flow_columns(cur)
    create_interpretive_layer_tables(cur)
    create_memory_conditions_table(cur)
    create_component_influence_tables(cur)
    create_argument_claims_table(cur)
    create_contract_map(cur)
    seed_fairness_action_check(cur)
    seed_scientist_mode(cur)
    seed_discovery_concept(cur)
    seed_plan_concept(cur)
    seed_discovery_plan_links(cur)
    seed_db_optimization_concepts(cur)
    seed_db_optimization_links(cur)
    seed_quality_plan_links(cur)
    seed_persona_tag(cur)
    seed_component_influence_modes(cur)
    seed_influence_preset_rows(cur, 'error_recovery', [
        ('concept', 'thinking_engine_recovery_component', 0.95, 'restore stable operation or safe fallback.'),
        ('concept', 'correction', 0.93, 'fix mistakes explicitly.'),
        ('concept', 'thinking_engine_uncertainty_component', 0.90, 'increase uncertainty handling and calibration.'),
        ('concept', 'thinking_engine_logging_component', 0.88, 'preserve diagnostics and traces.'),
        ('concept', 'thinking_engine_retrieval_component', 0.86, 're-check sources and retrieve relevant context.'),
        ('concept', 'schema_catalog', 0.82, 'find structure and canonical surfaces quickly.'),
        ('concept', 'discovery', 0.80, 'locate useful paths and missing structure.'),
        ('concept', 'entrypoint', 0.78, 'start from a canonical place.'),
        ('concept', 'canonical_home_enforcement', 0.76, 'route to one primary home to avoid duplication.'),
        ('concept', 'overlap_reduction', 0.74, 'collapse duplicate or conflicting paths.'),
    ])
    seed_influence_preset_rows(cur, 'evolved', [
        ('concept', 'thinking_engine_learning_component', 0.92, 'learn from repeated use and refine behavior.'),
        ('concept', 'thinking_engine_representation_component', 0.88, 'use clearer internal representations.'),
        ('concept', 'thinking_engine_retrieval_component', 0.86, 'retrieve relevant context efficiently.'),
        ('concept', 'thinking_engine_workflow_component', 0.84, 'coordinate the core process smoothly.'),
        ('concept', 'thinking_engine_governance_component', 0.82, 'apply consistent policy and control.'),
        ('concept', 'system', 0.80, 'operate as a stable bounded whole.'),
        ('concept', 'influence', 0.78, 'apply balanced internal and external influence.'),
        ('concept', 'discovery', 0.76, 'locate useful structure and paths.'),
        ('concept', 'schema_catalog', 0.74, 'find canonical surfaces quickly.'),
        ('concept', 'entrypoint', 0.72, 'start from a canonical place.'),
        ('concept', 'canonical_home_enforcement', 0.70, 'keep repeated ideas on one home.'),
    ])
    seed_influence_preset_rows(cur, 'default', [
        ('concept', 'thinking_engine_learning_component', 0.92, 'default baseline copied from evolved preset.'),
        ('concept', 'thinking_engine_representation_component', 0.88, 'default baseline copied from evolved preset.'),
        ('concept', 'thinking_engine_retrieval_component', 0.86, 'default baseline copied from evolved preset.'),
        ('concept', 'thinking_engine_workflow_component', 0.84, 'default baseline copied from evolved preset.'),
        ('concept', 'thinking_engine_governance_component', 0.82, 'default baseline copied from evolved preset.'),
        ('concept', 'system', 0.80, 'default baseline copied from evolved preset.'),
        ('concept', 'influence', 0.78, 'default baseline copied from evolved preset.'),
        ('concept', 'discovery', 0.76, 'default baseline copied from evolved preset.'),
        ('concept', 'schema_catalog', 0.74, 'default baseline copied from evolved preset.'),
        ('concept', 'entrypoint', 0.72, 'default baseline copied from evolved preset.'),
        ('concept', 'canonical_home_enforcement', 0.70, 'default baseline copied from evolved preset.'),
    ])
    seed_component_influence_current_from_preset(cur, 'default')
    seed_error_recovery_influence_work_plan(cur)
    seed_evolved_baseline_demo_work_plan(cur)
    seed_mistake_recording_policy(cur)
    seed_morphology_concept_provenance(cur)
    seed_memory_mvp_requirements(cur)
    seed_goal_mission_taxonomy_concepts(cur)
    seed_requirements_glossary_taxonomy_terms(cur)
    seed_reasoning_episodes(cur)
    backfill_reasoning_episode_inputs(cur)
    backfill_reasoning_decision_links(cur)
    backfill_open_question_flow(cur)
    backfill_open_question_resolutions(cur)
    backfill_decision_history(cur)
    seed_interpretive_layer(cur)
    seed_scientist_mode_routes(cur)
    seed_canonical_tag(cur)
    create_storage_map_view(cur)
    create_core_model_view(cur)
    create_frame_views(cur)
    create_problem_solving_patterns_view(cur)
    create_problem_understanding_patterns_view(cur)
    create_lean_thinking_patterns_view(cur)
    create_decision_patterns_view(cur)
    create_ethics_map_view(cur)
    create_ethics_principle_checks_view(cur)
    create_scientist_mode_view(cur)
    create_glossary_terms_view(cur)
    create_provenance_summary_view(cur)
    create_schema_catalog_view(cur)
    create_tag_search_view(cur)
    create_concept_search_view(cur)
    create_decision_overview_view(cur)
    create_component_influence_views(cur)
    create_convictions_view(cur)
    create_interpretive_layer_views(cur)
    create_argument_claims_view(cur)
    create_decision_options_view(cur)
    create_reasoning_v2_views(cur)
    create_open_question_flow_view(cur)
    create_reasoning_flow_views(cur)
    create_reasoning_quality_views(cur)
    create_memory_index_view(cur)
    create_memory_packet_view(cur)
    create_writeback_policy_view(cur)
    create_decision_history_triggers(cur)
    create_open_question_flow_triggers(cur)
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
