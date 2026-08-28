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
    ("beliefs", "current", "mutable", "belief_versions", "Canonical current belief row"),
    ("belief_versions", "history", "append_only", "beliefs", "Immutable belief history"),
    ("continuity_requirements", "current", "mutable", "continuity_requirement_versions", "Canonical current requirement row"),
    ("continuity_requirement_versions", "history", "append_only", "continuity_requirements", "Immutable requirement history"),
    ("ethical_principles", "current", "mutable", "ethical_action_checks", "Active ethical principles and priorities"),
    ("ethical_action_checks", "evidence", "append_only", "ethical_principles", "Action checks that operationalize ethical principles"),
    ("metacognitive_state", "current", "mutable", "metacognitive_state_history", "Canonical current metacognitive state row"),
    ("metacognitive_state_history", "history", "append_only", "metacognitive_state", "Immutable metacognitive history"),
    ("object_metadata", "current", "mutable", "object_provenance", "Canonical object metadata row"),
    ("object_provenance", "evidence", "mutable", "object_metadata", "Supporting provenance for objects"),
    ("epistemic_receipts", "audit", "immutable", None, "Immutable audit log"),
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

    map_row = cur.execute("select principle_key, check_key from v_ethics_principles_map where principle_key='fairness' and check_key='fairness'").fetchone()
    if map_row != ('fairness', 'fairness'):
        issues.append(("fairness_map_row", map_row, ('fairness', 'fairness')))
    hard_row = cur.execute("select principle_key, check_key, hard_gate from v_ethics_principle_checks where principle_key='fairness' and check_key='unjust_disparate_treatment'").fetchone()
    if hard_row != ('fairness', 'unjust_disparate_treatment', 1):
        issues.append(("fairness_hard_row", hard_row, ('fairness', 'unjust_disparate_treatment', 1)))

    return issues


def apply_migration():
    conn = connect()
    cur = conn.cursor()
    add_receipt_kind_column(cur)
    add_action_check_principle_column(cur)
    backfill_receipt_kind(cur)
    ensure_indexes(cur)
    create_contract_map(cur)
    seed_fairness_action_check(cur)
    create_storage_map_view(cur)
    create_ethics_map_view(cur)
    create_ethics_principle_checks_view(cur)
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
