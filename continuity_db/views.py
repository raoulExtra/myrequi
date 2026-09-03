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

TAG_SEARCH_VIEW_SQL = """
CREATE VIEW v_tag_search AS
SELECT
    t.tag_key,
    t.label AS tag_label,
    t.description AS tag_description,
    o.object_type,
    o.object_key,
    CASE
        WHEN o.object_type='metacognitive_state' THEN m.state_key
        WHEN o.object_type='concept' THEN c.name
        ELSE o.object_key
    END AS object_title,
    CASE
        WHEN o.object_type='metacognitive_state' THEN m.value
        WHEN o.object_type='concept' THEN c.description
        ELSE o.note
    END AS object_body,
    o.note,
    COALESCE(m.category, '') AS object_category,
    COALESCE(m.provenance, '') AS object_provenance,
    COALESCE(m.updated_at, c.updated_at, o.created_at) AS recorded_at,
    lower(
        COALESCE(t.tag_key, '') || ' ' ||
        COALESCE(t.label, '') || ' ' ||
        COALESCE(t.description, '') || ' ' ||
        COALESCE(o.object_type, '') || ' ' ||
        COALESCE(o.object_key, '') || ' ' ||
        COALESCE(o.note, '') || ' ' ||
        COALESCE(m.state_key, '') || ' ' ||
        COALESCE(m.category, '') || ' ' ||
        COALESCE(m.value, '') || ' ' ||
        COALESCE(c.concept_key, '') || ' ' ||
        COALESCE(c.name, '') || ' ' ||
        COALESCE(c.description, '')
    ) AS searchable_text
FROM object_epistemic_tags o
JOIN epistemic_tags t ON t.tag_key = o.tag_key
LEFT JOIN metacognitive_state m ON o.object_type='metacognitive_state' AND m.state_key = o.object_key
LEFT JOIN concepts c ON o.object_type='concept' AND c.concept_key = o.object_key
ORDER BY recorded_at DESC, t.tag_key, o.object_type, o.object_key
"""

COMPONENT_INFLUENCE_VIEWS_SQL = """
CREATE VIEW v_component_influence_modes AS
SELECT mode_key, label, description, created_at
FROM component_influence_modes
ORDER BY mode_key;

CREATE VIEW v_component_influence AS
SELECT
    ci.component_type,
    ci.component_key,
    ci.mode_key,
    m.label AS mode_label,
    m.description AS mode_description,
    ci.default_score,
    ci.current_score,
    ci.override_reason,
    ci.updated_at,
    CASE
        WHEN ci.current_score > ci.default_score THEN 'raised'
        WHEN ci.current_score < ci.default_score THEN 'lowered'
        ELSE 'baseline'
    END AS influence_state
FROM component_influence ci
JOIN component_influence_modes m ON m.mode_key = ci.mode_key
ORDER BY ci.component_type, ci.component_key;

CREATE VIEW v_component_influence_presets AS
SELECT
    p.mode_key,
    m.label AS mode_label,
    m.description AS mode_description,
    p.component_type,
    p.component_key,
    p.preset_score,
    p.reason,
    p.created_at
FROM component_influence_presets p
JOIN component_influence_modes m ON m.mode_key = p.mode_key
ORDER BY p.mode_key, p.component_type, p.component_key;

CREATE VIEW v_component_influence_history AS
SELECT
    h.id,
    h.component_type,
    h.component_key,
    h.mode_key,
    m.label AS mode_label,
    h.default_score,
    h.previous_score,
    h.current_score,
    h.delta,
    h.reason,
    h.changed_at
FROM component_influence_history h
JOIN component_influence_modes m ON m.mode_key = h.mode_key
ORDER BY h.changed_at DESC, h.id DESC;
"""

SCHEMA_CATALOG_VIEW_SQL = """
CREATE VIEW v_schema_catalog AS
SELECT
    name AS object_name,
    type AS object_type,
    tbl_name AS table_name,
    COALESCE(sql, '') AS definition,
    lower(name || ' ' || type || ' ' || tbl_name || ' ' || COALESCE(sql, '')) AS searchable_text
FROM sqlite_master
WHERE type IN ('table', 'view')
  AND name NOT LIKE 'sqlite_%'
ORDER BY type, name
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

CORE_MODEL_VIEW_SQL = """
CREATE VIEW v_core_model AS
SELECT 1 AS sort_order, 'state' AS layer_key, 'What is true, uncertain, or decided.' AS purpose, 'observations, beliefs, convictions, open_questions, decisions' AS current_tables, 'beliefs, convictions' AS collapsed_concepts, 'Keep the smallest useful semantic state surface.' AS notes
UNION ALL SELECT 2, 'action', 'What should happen next.', 'continuity_requirements, work_plans, work_plan_steps, projects', 'missions, strategies, plans, commitments', 'Treat plans as execution scaffolding, not a separate universe.'
UNION ALL SELECT 3, 'audit', 'How we know, what changed, and why.', 'epistemic_receipts, reasoning_episodes, reasoning_episode_inputs, decision_versions, belief_versions, conviction_versions, continuity_requirement_versions, object_provenance, journal, synthesis_conflicts, feature_flag_events, component_influence_history', 'episodes, receipts, provenance, history', 'Preserve traceability, but keep it out of the core reasoning vocabulary.'
UNION ALL SELECT 4, 'policy', 'How the engine should behave.', 'metacognitive_state, component_influence, component_influence_modes, component_influence_presets, feature_flags, epistemic_tags', 'personas, trust, quality, modes', 'Treat tuning and persona-like state as policy metadata, not core facts.'
ORDER BY sort_order
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
