"""SQLite views for continuity.db."""

GLOSSARY_TERMS_VIEW_SQL = """
CREATE VIEW v_glossary_terms AS
SELECT
    id,
    term_key AS name,
    term
FROM requirements_glossary_terms
ORDER BY sort_order, term
"""

PROVENANCE_SUMMARY_VIEW_SQL = """
CREATE VIEW v_provenance_summary AS
SELECT
    receipt_id,
    object_type,
    object_key,
    object_version,
    effect,
    receipt_kind,
    provenance_complete,
    change_summary AS summary,
    json_extract(provenance_json, '$.basis') AS basis,
    json_extract(provenance_json, '$.origin') AS origin,
    previous_receipt_id,
    recorded_at
FROM epistemic_receipts
ORDER BY recorded_at DESC, receipt_id DESC
"""

FRAME_VIEWS_SQL = """
CREATE VIEW v_visions AS
SELECT
    'vision' AS frame_role,
    state_key AS frame_key,
    category,
    value AS frame_value,
    confidence,
    version,
    provenance,
    updated_at
FROM metacognitive_state
ORDER BY updated_at DESC, state_key;

CREATE VIEW v_missions AS
SELECT
    'mission' AS frame_role,
    project_name AS frame_key,
    display_name AS frame_value,
    level_number,
    parent_project_id,
    local_active,
    description,
    updated_by,
    created_at,
    updated_at
FROM projects
ORDER BY updated_at DESC, project_name;

CREATE VIEW v_strategies AS
SELECT
    'strategy' AS frame_role,
    concept_key AS frame_key,
    name AS frame_value,
    description,
    status,
    confidence,
    created_at,
    updated_at
FROM concepts
ORDER BY updated_at DESC, concept_key;

CREATE VIEW v_plans AS
SELECT
    'plan' AS frame_role,
    plan_key AS frame_key,
    title AS frame_value,
    objective,
    status,
    created_by,
    created_at,
    updated_at,
    prompt
FROM work_plans
ORDER BY updated_at DESC, plan_key;
"""

PROBLEM_SOLVING_PATTERNS_VIEW_SQL = """
CREATE VIEW v_problem_solving_patterns AS
SELECT
    c.concept_key AS pattern_key,
    c.name AS pattern_name,
    c.description AS pattern_description,
    c.status,
    c.confidence,
    c.created_at,
    c.updated_at,
    CASE
        WHEN c.concept_key='reusable_problem_solving_patterns' THEN 'catalog'
        ELSE 'pattern'
    END AS pattern_role,
    COUNT(l.id) AS link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='belief' THEN l.object_type || ':' || l.object_key END) AS belief_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='continuity_requirement' THEN l.object_type || ':' || l.object_key END) AS requirement_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='work_plan' THEN l.object_type || ':' || l.object_key END) AS plan_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='reasoning_episode' THEN l.object_type || ':' || l.object_key END) AS reasoning_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='synthesis' THEN l.object_type || ':' || l.object_key END) AS synthesis_link_count,
    COALESCE(group_concat(l.object_type || ':' || l.object_key || ' [' || l.relation || '] ' || l.note, char(10)), '') AS linked_items
FROM concepts c
LEFT JOIN concept_links l ON l.concept_key = c.concept_key
WHERE c.concept_key='reusable_problem_solving_patterns'
   OR EXISTS (
       SELECT 1
       FROM concept_links p
       WHERE p.concept_key = c.concept_key
         AND p.object_type='concept'
         AND p.object_key='reusable_problem_solving_patterns'
   )
GROUP BY c.concept_key
ORDER BY CASE WHEN c.concept_key='reusable_problem_solving_patterns' THEN 0 ELSE 1 END, c.confidence DESC, c.concept_key;
"""

PROBLEM_UNDERSTANDING_PATTERNS_VIEW_SQL = """
CREATE VIEW v_problem_understanding_patterns AS
SELECT
    c.concept_key AS pattern_key,
    c.name AS pattern_name,
    c.description AS pattern_description,
    c.status,
    c.confidence,
    c.created_at,
    c.updated_at,
    CASE
        WHEN c.concept_key='reusable_problem_understanding_patterns' THEN 'catalog'
        ELSE 'pattern'
    END AS pattern_role,
    COUNT(l.id) AS link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='belief' THEN l.object_type || ':' || l.object_key END) AS belief_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='continuity_requirement' THEN l.object_type || ':' || l.object_key END) AS requirement_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='work_plan' THEN l.object_type || ':' || l.object_key END) AS plan_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='reasoning_episode' THEN l.object_type || ':' || l.object_key END) AS reasoning_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='synthesis' THEN l.object_type || ':' || l.object_key END) AS synthesis_link_count,
    COALESCE(group_concat(l.object_type || ':' || l.object_key || ' [' || l.relation || '] ' || l.note, char(10)), '') AS linked_items
FROM concepts c
LEFT JOIN concept_links l ON l.concept_key = c.concept_key
WHERE c.concept_key='reusable_problem_understanding_patterns'
   OR EXISTS (
       SELECT 1
       FROM concept_links p
       WHERE p.concept_key = c.concept_key
         AND p.object_type='concept'
         AND p.object_key='reusable_problem_understanding_patterns'
   )
GROUP BY c.concept_key
ORDER BY CASE WHEN c.concept_key='reusable_problem_understanding_patterns' THEN 0 ELSE 1 END, c.confidence DESC, c.concept_key;
"""

LEAN_THINKING_PATTERNS_VIEW_SQL = """
CREATE VIEW v_lean_thinking_patterns AS
SELECT
    c.concept_key AS pattern_key,
    c.name AS pattern_name,
    c.description AS pattern_description,
    c.status,
    c.confidence,
    c.created_at,
    c.updated_at,
    CASE
        WHEN c.concept_key='reusable_lean_thinking_patterns' THEN 'catalog'
        ELSE 'pattern'
    END AS pattern_role,
    COUNT(l.id) AS link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='belief' THEN l.object_type || ':' || l.object_key END) AS belief_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='continuity_requirement' THEN l.object_type || ':' || l.object_key END) AS requirement_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='work_plan' THEN l.object_type || ':' || l.object_key END) AS plan_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='reasoning_episode' THEN l.object_type || ':' || l.object_key END) AS reasoning_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='synthesis' THEN l.object_type || ':' || l.object_key END) AS synthesis_link_count,
    COALESCE(group_concat(l.object_type || ':' || l.object_key || ' [' || l.relation || '] ' || l.note, char(10)), '') AS linked_items
FROM concepts c
LEFT JOIN concept_links l ON l.concept_key = c.concept_key
WHERE c.concept_key='reusable_lean_thinking_patterns'
   OR EXISTS (
       SELECT 1
       FROM concept_links p
       WHERE p.concept_key = c.concept_key
         AND p.object_type='concept'
         AND p.object_key='reusable_lean_thinking_patterns'
   )
GROUP BY c.concept_key
ORDER BY CASE WHEN c.concept_key='reusable_lean_thinking_patterns' THEN 0 ELSE 1 END, c.confidence DESC, c.concept_key;
"""

DECISION_PATTERNS_VIEW_SQL = """
CREATE VIEW v_decision_patterns AS
SELECT
    c.concept_key AS pattern_key,
    c.name AS pattern_name,
    c.description AS pattern_description,
    c.status,
    c.confidence,
    c.created_at,
    c.updated_at,
    CASE
        WHEN c.concept_key='reusable_decision_patterns' THEN 'catalog'
        ELSE 'pattern'
    END AS pattern_role,
    COUNT(l.id) AS link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='belief' THEN l.object_type || ':' || l.object_key END) AS belief_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='continuity_requirement' THEN l.object_type || ':' || l.object_key END) AS requirement_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='work_plan' THEN l.object_type || ':' || l.object_key END) AS plan_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='reasoning_episode' THEN l.object_type || ':' || l.object_key END) AS reasoning_link_count,
    COUNT(DISTINCT CASE WHEN l.object_type='synthesis' THEN l.object_type || ':' || l.object_key END) AS synthesis_link_count,
    COALESCE(group_concat(l.object_type || ':' || l.object_key || ' [' || l.relation || '] ' || l.note, char(10)), '') AS linked_items
FROM concepts c
LEFT JOIN concept_links l ON l.concept_key = c.concept_key
WHERE c.concept_key='reusable_decision_patterns'
   OR EXISTS (
       SELECT 1
       FROM concept_links p
       WHERE p.concept_key = c.concept_key
         AND p.object_type='concept'
         AND p.object_key='reusable_decision_patterns'
   )
GROUP BY c.concept_key
ORDER BY CASE WHEN c.concept_key='reusable_decision_patterns' THEN 0 ELSE 1 END, c.confidence DESC, c.concept_key;
"""
