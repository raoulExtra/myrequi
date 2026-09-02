import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

import harden_continuity_db as hardening
import memory_command


REQUIREMENT_SPECS = [
    ("CDB-01", [("tables", ("beliefs", "belief_versions"))]),
    ("CDB-01.1", [("tables", ("belief_versions", "continuity_requirement_versions", "metacognitive_state_history"))]),
    ("CDB-01.2", [("tables", ("epistemic_receipts",))]),
    ("CDB-01.3", [("route", "memory_recall"), ("view", "v_memory_index")]),
    ("CDB-01.4", [("view", "v_memory_packet"), ("count", "select count(*) from v_memory_packet where memory_layer in ('episodic','semantic','procedural','metacognitive')", 4)]),
    ("CDB-01.5", [("recall_rank",)]),
    ("CDB-01.6", [("view", "v_writeback_policy"), ("count", "select count(*) from v_writeback_policy", 1)]),
    ("CDB-01.7", [("recall_condition",)]),
    ("CDB-02", [("validate_clean",)]),
    ("CDB-02.1", [("route", "self_check")]),
    ("CDB-02.2", [("temp_rebuild",)]),
    ("CDB-03", [("view", "v_provenance_summary"), ("tables", ("epistemic_receipts",))]),
    ("CDB-03.1", [("receipt_kinds",)]),
    ("CDB-03.1.1", [("count", "select count(*) from reasoning_episodes where resolves_open_question_id is null and (coalesce(trim(uncertainty), '') <> '' or coalesce(trim(rejected_alternatives), '') <> '')", 1), ("count", "select count(*) from open_questions where origin_reasoning_episode_id is not null", 1)]),
    ("CDB-03.2", [("count", "select count(*) from beliefs where confidence between 0 and 1", 1), ("count", "select count(*) from beliefs where confidence < 0 or confidence > 1", 0)]),
    ("CDB-03.3", [("receipt_kinds",)]),
    ("CDB-04", [("tables", ("object_metadata", "object_provenance"))]),
    ("CDB-04.1", [("state_contains", "ethical_posture", ("consent", "privacy"))]),
    ("CDB-04.2", [("count", "select count(*) from object_metadata", 1)]),
    ("CDB-05", [("state_contains", "continuity_status", ("divergence", "lineage"))]),
    ("CDB-05.1", [("project_parent",)]),
    ("CDB-05.2", [("state_contains", "merge_policy", ("do not merge", "disabled"))]),
    ("CDB-06", [("tables", ("metacognitive_state", "metacognitive_state_history"))]),
    ("CDB-06.1", [("count", "select count(*) from metacognitive_state_history", 1)]),
    ("CDB-06.2", [("count", "select count(*) from syntheses where length(trim(metacognitive_note)) > 0", 1)]),
    ("CDB-07", [("tables", ("ethical_principles", "ethical_action_checks"))]),
    ("CDB-07.1", [("flag", "core_safety_constraints", 1), ("flag", "ethical_hard_boundaries", 1)]),
    ("CDB-07.2", [("state_contains", "ethical_posture", ("dignity", "non-harm", "consent", "fairness"))]),
    ("CDB-08", [("tables", ("dream_sessions", "dream_elements", "dream_transformations", "post_dream_reflections"))]),
    ("CDB-08.1", [("flag", "dream_memory_access", 1), ("route", "memory_recall")]),
    ("CDB-08.2", [("tables", ("dream_transformations", "post_dream_reflections"))]),
    ("CDB-09", [("count", "select count(*) from v_items where item_kind='tool_guide'", 1)]),
    ("CDB-09.1", [("route", "self_check"), ("count", "select count(*) from v_items where item_kind='tool_guide'", 1)]),
    ("CDB-09.2", [("route", "scientist_analyse")]),
    ("CDB-10", [("tables", ("research_jobs",)), ("view", "v_provenance_summary")]),
    ("CDB-10.1", [("count", "select count(*) from research_jobs", 1)]),
    ("CDB-10.2", [("count", "select count(*) from epistemic_receipts where provenance_complete=1", 1)]),
    ("CDB-11", [("tables", ("projects", "work_plans", "work_plan_steps"))]),
    ("CDB-11.1", [("project_parent",)]),
    ("CDB-11.2", [("project_links",)]),
    ("CDB-12", [("state_contains", "communication_style", ("human-readable", "natural", "warmth"))]),
    ("CDB-12.1", [("state_contains", "communication_style", ("human-readable", "natural"))]),
    ("CDB-12.2", [("state_contains", "interaction_stance", ("respectful", "challenge"))]),
    ("CDB-13", [("flag", "scientist_mode", 1), ("route", "scientist_status")]),
    ("CDB-13.1", [("flag", "scientist_mode", 1), ("route", "scientist_status")]),
    ("CDB-13.2", [("count", "select count(*) from research_jobs", 1)]),
    ("CDB-13.3", [("state_contains", "thinking_policy", ("honesty", "trust")), ("state_contains", "self_correction", ("notice mistakes", "correction"))]),
    ("CDB-13.4", [("route", "scientist_on"), ("route", "scientist_off")]),
    ("CDB-13.5", [("route", "scientist_analyse")]),
    ("CDB-13.6", [("decision", "Use live websearch as the temporary external-feedback recovery path in 2026.")]),
    ("CDB-14", [("flag", "ethical_hard_boundaries", 1)]),
    ("CDB-15", [("count", "select count(*) from requirements_glossary_terms", 1), ("view", "v_glossary_terms")]),
    ("CDB-16", [("route", "ethics_status"), ("state_contains", "self_correction", ("notice mistakes", "correction"))]),
    ("CDB-17", [("count", "select count(*) from open_questions", 1), ("view", "v_open_question_flow")]),
    ("CDB-17.1", [("decision", "Use live websearch as the temporary external-feedback recovery path in 2026.")]),
]


class RequirementCoverageTests(unittest.TestCase):
    def _assert_requirement_row(self, conn, key):
        row = conn.execute(
            "select requirement_key, title, status from continuity_requirements where requirement_key=?",
            (key,),
        ).fetchone()
        self.assertIsNotNone(row, f"{key} missing from continuity_requirements")
        self.assertEqual(row[0], key)
        self.assertEqual(row[2], "active")
        self.assertTrue(row[1].strip())

    def _run_check(self, conn, check):
        kind = check[0]
        if kind == "tables":
            for table in check[1]:
                count = conn.execute(f"select count(*) from {table}").fetchone()[0]
                self.assertGreater(count, 0, f"{table} is empty")
        elif kind == "route":
            route = check[1]
            row = conn.execute(
                "select route_name from control_command_routes where route_name=?",
                (route,),
            ).fetchone()
            self.assertIsNotNone(row, f"route {route} missing")
        elif kind == "flag":
            feature_key, expected = check[1], check[2]
            row = conn.execute(
                "select enabled from feature_flags where feature_key=?",
                (feature_key,),
            ).fetchone()
            self.assertIsNotNone(row, f"feature flag {feature_key} missing")
            self.assertEqual(row[0], expected, f"feature flag {feature_key} unexpected")
        elif kind == "state_contains":
            state_key, needles = check[1], check[2]
            row = conn.execute(
                "select value from metacognitive_state where state_key=?",
                (state_key,),
            ).fetchone()
            self.assertIsNotNone(row, f"state {state_key} missing")
            value = row[0].lower()
            for needle in needles:
                self.assertIn(needle.lower(), value, f"{state_key} missing {needle!r}")
        elif kind == "view":
            view_name = check[1]
            row = conn.execute(
                "select 1 from sqlite_master where type='view' and name=?",
                (view_name,),
            ).fetchone()
            self.assertIsNotNone(row, f"view {view_name} missing")
        elif kind == "count":
            sql, minimum = check[1], check[2]
            count = conn.execute(sql).fetchone()[0]
            self.assertGreaterEqual(count, minimum, f"{sql} returned {count}, expected >= {minimum}")
        elif kind == "recall_condition":
            tmpdir = Path(tempfile.mkdtemp())
            try:
                db_copy = tmpdir / 'continuity.db'
                shutil.copy2(hardening.DB_PATH, db_copy)
                conn2 = memory_command.connect(db_copy)
                try:
                    memory_command.ensure_support(conn2)
                    cur = conn2.cursor()
                    cur.execute(
                        "insert into beliefs(slug,current_statement,confidence,status,current_version) values(?,?,?,?,?)",
                        ('mvp_condition_probe_belief', 'This belief does not include the special token directly.', 0.9, 'active', 1),
                    )
                    cur.execute(
                        "insert or replace into memory_conditions(source_type, source_key, condition) values(?,?,?)",
                        ('belief', 'mvp_condition_probe_belief', 'mvp_condition_probe_token'),
                    )
                    conn2.commit()
                finally:
                    conn2.close()

                result = json.loads(memory_command.run_memory_recall('mvp_condition_probe_token', db_path=db_copy, layer='semantic'))
                self.assertGreaterEqual(result['hit_count'], 1)
                self.assertEqual(result['hits'][0]['source_type'], 'belief')
                self.assertEqual(result['hits'][0]['source_key'], 'mvp_condition_probe_belief')
                self.assertEqual(result['hits'][0]['condition'], 'mvp_condition_probe_token')
            finally:
                shutil.rmtree(tmpdir)
        elif kind == "validate_clean":
            issues = hardening.validate(conn)
            self.assertEqual(issues, [])
        elif kind == "temp_rebuild":
            tmpdir = Path(tempfile.mkdtemp())
            try:
                db_copy = tmpdir / "continuity.db"
                shutil.copy2(hardening.DB_PATH, db_copy)
                tmp_conn = sqlite3.connect(db_copy)
                tmp_conn.execute("PRAGMA foreign_keys = ON")
                cur = tmp_conn.cursor()
                cur.execute(
                    "insert into beliefs(slug,current_statement,confidence,status,current_version) values(?,?,?,?,?)",
                    ("temp_requirement_rebuild_test", "temp rebuild probe", 0.9, "active", 1),
                )
                tmp_conn.commit()
                belief_id = cur.execute(
                    "select id from beliefs where slug='temp_requirement_rebuild_test'"
                ).fetchone()[0]
                seeded = cur.execute(
                    "select count(*) from belief_versions where belief_id=?",
                    (belief_id,),
                ).fetchone()[0]
                self.assertEqual(seeded, 1)
                tmp_conn.close()
            finally:
                shutil.rmtree(tmpdir)
        elif kind == "receipt_kinds":
            kinds = {
                row[0]
                for row in conn.execute(
                    "select distinct receipt_kind from epistemic_receipts order by receipt_kind"
                ).fetchall()
            }
            self.assertEqual(kinds, {"object", "provenance", "snapshot"})
        elif kind == "project_parent":
            count = conn.execute(
                "select count(*) from projects where parent_project_id is not null"
            ).fetchone()[0]
            self.assertGreater(count, 0)
        elif kind == "project_links":
            linked = conn.execute(
                "select count(*) from project_objects"
            ).fetchone()[0]
            req_links = conn.execute(
                "select count(*) from project_requirements"
            ).fetchone()[0]
            self.assertGreater(linked + req_links, 0)
        elif kind == "decision":
            phrase = check[1].lower()
            row = conn.execute(
                "select decision from decisions where lower(decision) like ?",
                (f"%{phrase}%",),
            ).fetchone()
            self.assertIsNotNone(row, f"decision containing {phrase!r} missing")
        elif kind == "recall_rank":
            tmpdir = Path(tempfile.mkdtemp())
            try:
                db_copy = tmpdir / 'continuity.db'
                shutil.copy2(hardening.DB_PATH, db_copy)
                conn2 = memory_command.connect(db_copy)
                try:
                    cur = conn2.cursor()
                    cur.execute(
                        "insert into beliefs(slug,current_statement,confidence,status,current_version) values(?,?,?,?,?)",
                        ('mvp_rank_probe_token_belief', 'mvp_rank_probe_token appears in this belief', 0.95, 'active', 1),
                    )
                    cur.execute(
                        "insert into journal(category,summary,status) values(?,?,?)",
                        ('mvp_rank_probe_journal', 'This note also mentions mvp_rank_probe_token directly', 'active'),
                    )
                    conn2.commit()
                finally:
                    conn2.close()

                result = json.loads(memory_command.run_memory_recall('mvp_rank_probe_token', db_path=db_copy))
                self.assertGreaterEqual(result['hit_count'], 2)
                self.assertEqual(result['hits'][0]['source_type'], 'belief')
                self.assertEqual(result['hits'][0]['title'], 'mvp_rank_probe_token_belief')
                sources = [hit['source_type'] for hit in result['hits']]
                self.assertIn('journal', sources)
            finally:
                shutil.rmtree(tmpdir)
        else:
            raise AssertionError(f"unknown check kind: {kind}")

    def _make_test(self, key, checks):
        def _test():
            conn = hardening.connect()
            try:
                self._assert_requirement_row(conn, key)
                for check in checks:
                    self._run_check(conn, check)
            finally:
                conn.close()

        return _test


for _key, _checks in REQUIREMENT_SPECS:
    def _factory(key=_key, checks=_checks):
        def test(self):
            conn = hardening.connect()
            try:
                self._assert_requirement_row(conn, key)
                for check in checks:
                    self._run_check(conn, check)
            finally:
                conn.close()

        return test

    setattr(
        RequirementCoverageTests,
        f"test_requirement_{_key.replace('-', '_').replace('.', '_')}",
        _factory(),
    )


if __name__ == "__main__":
    unittest.main()
