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
)
from .views import FRAME_VIEWS_SQL, GLOSSARY_TERMS_VIEW_SQL, LEAN_THINKING_PATTERNS_VIEW_SQL, DECISION_PATTERNS_VIEW_SQL, PROBLEM_SOLVING_PATTERNS_VIEW_SQL, PROBLEM_UNDERSTANDING_PATTERNS_VIEW_SQL, PROVENANCE_SUMMARY_VIEW_SQL

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


def create_reasoning_v2_views(cur):
    for name in ['v_item_links', 'v_meta', 'v_explain', 'v_recall', 'v_items', 'v_memory_index', 'v_decision_versions', 'v_decision_options', 'v_open_question_flow', 'v_reasoning_episode_inputs', 'v_reasoning_flow']:
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
        "v_ethics_principles_map",
        "v_ethics_principle_checks",
        "v_scientist_mode_state",
        "v_glossary_terms",
        "v_provenance_summary",
        "v_visions",
        "v_missions",
        "v_strategies",
        "v_plans",
        "v_items",
        "v_item_links",
        "v_argument_claims",
        "v_recall",
        "v_explain",
        "v_meta",
        "v_memory_index",
        "v_decision_versions",
        "v_decision_options",
        "v_open_question_flow",
        "v_reasoning_episode_inputs",
        "v_reasoning_flow",
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
    create_argument_claims_table(cur)
    create_contract_map(cur)
    seed_fairness_action_check(cur)
    seed_scientist_mode(cur)
    seed_memory_mvp_requirements(cur)
    seed_reasoning_episodes(cur)
    backfill_reasoning_episode_inputs(cur)
    backfill_reasoning_decision_links(cur)
    backfill_open_question_flow(cur)
    backfill_open_question_resolutions(cur)
    backfill_decision_history(cur)
    seed_interpretive_layer(cur)
    seed_scientist_mode_routes(cur)
    create_storage_map_view(cur)
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
    create_interpretive_layer_views(cur)
    create_argument_claims_view(cur)
    create_decision_options_view(cur)
    create_reasoning_v2_views(cur)
    create_open_question_flow_view(cur)
    create_reasoning_flow_views(cur)
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
