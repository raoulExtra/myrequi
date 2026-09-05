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

CONCEPT_SEARCH_VIEW_SQL = """
CREATE VIEW v_concept_search AS
WITH link_summary AS (
    SELECT
        concept_key,
        COUNT(*) AS link_count,
        COALESCE(group_concat(object_type || ':' || object_key || ' [' || relation || '] ' || note, char(10)), '') AS linked_items
    FROM concept_links
    GROUP BY concept_key
), tag_summary AS (
    SELECT
        object_key AS concept_key,
        COALESCE(group_concat(tag_key || COALESCE(' [' || note || ']', ''), char(10)), '') AS tagged_terms
    FROM object_epistemic_tags
    WHERE object_type='concept'
    GROUP BY object_key
)
SELECT
    c.concept_key,
    c.name,
    c.description,
    c.status,
    c.confidence,
    c.created_at,
    c.updated_at,
    COALESCE(ls.link_count, 0) AS link_count,
    COALESCE(ls.linked_items, '') AS linked_items,
    COALESCE(ts.tagged_terms, '') AS tagged_terms,
    lower(
        COALESCE(c.concept_key, '') || ' ' ||
        COALESCE(c.name, '') || ' ' ||
        COALESCE(c.description, '') || ' ' ||
        COALESCE(c.status, '') || ' ' ||
        COALESCE(ls.linked_items, '') || ' ' ||
        COALESCE(ts.tagged_terms, '')
    ) AS searchable_text
FROM concepts c
LEFT JOIN link_summary ls ON ls.concept_key = c.concept_key
LEFT JOIN tag_summary ts ON ts.concept_key = c.concept_key
ORDER BY COALESCE(ls.link_count, 0) DESC, c.confidence DESC, c.updated_at DESC, c.concept_key
"""

DECISION_OVERVIEW_VIEW_SQL = """
CREATE VIEW v_decisions AS
WITH option_counts AS (
    SELECT
        decision_id,
        COUNT(*) AS option_count,
        SUM(CASE WHEN status='candidate' THEN 1 ELSE 0 END) AS candidate_option_count,
        SUM(CASE WHEN status='chosen' THEN 1 ELSE 0 END) AS chosen_option_count,
        SUM(CASE WHEN status='rejected' THEN 1 ELSE 0 END) AS rejected_option_count,
        SUM(CASE WHEN status='deferred' THEN 1 ELSE 0 END) AS deferred_option_count
    FROM decision_options
    GROUP BY decision_id
), history_counts AS (
    SELECT
        decision_id,
        COUNT(*) AS version_count,
        MAX(version) AS latest_version,
        MAX(recorded_at) AS latest_recorded_at
    FROM decision_versions
    GROUP BY decision_id
)
SELECT
    d.id AS decision_id,
    d.decision AS decision_text,
    d.rationale_summary,
    d.alternatives AS alternatives_summary,
    d.uncertainty,
    d.status,
    d.origin_reasoning_episode_id,
    COALESCE(oc.option_count, 0) AS option_count,
    COALESCE(oc.candidate_option_count, 0) AS candidate_option_count,
    COALESCE(oc.chosen_option_count, 0) AS chosen_option_count,
    COALESCE(oc.rejected_option_count, 0) AS rejected_option_count,
    COALESCE(oc.deferred_option_count, 0) AS deferred_option_count,
    COALESCE(hc.version_count, 0) AS version_count,
    hc.latest_version,
    hc.latest_recorded_at,
    d.created_at
FROM decisions d
LEFT JOIN option_counts oc ON oc.decision_id = d.id
LEFT JOIN history_counts hc ON hc.decision_id = d.id
ORDER BY d.created_at DESC, d.id DESC
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

SCHEMA_CATALOG_ALL_VIEW_SQL = """
CREATE VIEW v_schema_catalog_all AS
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

SCHEMA_CATALOG_VIEW_SQL = """
CREATE VIEW v_schema_catalog AS
SELECT
    sm.name AS object_name,
    sm.type AS object_type,
    sm.tbl_name AS table_name,
    COALESCE(sm.sql, '') AS definition,
    lower(sm.name || ' ' || sm.type || ' ' || sm.tbl_name || ' ' || COALESCE(sm.sql, '')) AS searchable_text
FROM sqlite_master sm
JOIN object_epistemic_tags oet
  ON oet.object_type='schema_object'
 AND oet.object_key=sm.name
 AND oet.tag_key='canonical'
WHERE sm.type IN ('table', 'view')
  AND sm.name NOT LIKE 'sqlite_%'
ORDER BY sm.type, sm.name
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

REASONING_QUALITY_VIEWS_SQL = """
CREATE VIEW v_reasoning_quality AS
WITH input_stats AS (
    SELECT
        r.id AS episode_id,
        COUNT(i.episode_id) AS input_count,
        COALESCE(SUM(i.weight), 0.0) AS input_weight,
        SUM(CASE WHEN i.relation IN ('supports', 'grounds', 'refines') THEN 1 ELSE 0 END) AS support_input_count,
        SUM(CASE WHEN i.relation IN ('questions', 'opposes') THEN 1 ELSE 0 END) AS challenge_input_count
    FROM reasoning_episodes r
    LEFT JOIN reasoning_episode_inputs i ON i.episode_id = r.id
    GROUP BY r.id
),
scored AS (
    SELECT
        r.id,
        r.episode_key,
        r.title,
        r.claim,
        r.evidence_summary,
        r.inference,
        r.rejected_alternatives,
        r.uncertainty,
        r.next_action,
        r.status,
        r.source_mode,
        r.created_at,
        r.updated_at,
        COALESCE(s.input_count, 0) AS input_count,
        COALESCE(s.input_weight, 0.0) AS input_weight,
        COALESCE(s.support_input_count, 0) AS support_input_count,
        COALESCE(s.challenge_input_count, 0) AS challenge_input_count,
        lower(r.title || ' ' || r.claim || ' ' || r.evidence_summary || ' ' || r.inference || ' ' || r.rejected_alternatives || ' ' || r.uncertainty || ' ' || r.next_action) AS context_text,
        CASE
            WHEN length(trim(r.claim)) BETWEEN 35 AND 180 THEN 5
            WHEN length(trim(r.claim)) BETWEEN 20 AND 240 THEN 4
            WHEN length(trim(r.claim)) BETWEEN 12 AND 300 THEN 3
            WHEN trim(r.claim) <> '' THEN 2
            ELSE 1
        END AS claim_clarity_score,
        CASE
            WHEN COALESCE(s.input_count, 0) >= 4 THEN 5
            WHEN COALESCE(s.input_count, 0) >= 2 THEN 4
            WHEN COALESCE(s.input_count, 0) >= 1 OR length(trim(r.evidence_summary)) >= 80 THEN 3
            WHEN trim(r.evidence_summary) <> '' THEN 2
            ELSE 1
        END AS evidence_score,
        CASE
            WHEN length(trim(r.inference)) BETWEEN 35 AND 220 THEN 5
            WHEN length(trim(r.inference)) BETWEEN 20 AND 280 THEN 4
            WHEN trim(r.inference) <> '' THEN 3
            ELSE 1
        END AS inference_score,
        CASE
            WHEN trim(r.uncertainty) = '' THEN 2
            WHEN lower(r.uncertainty) LIKE '%may%' OR lower(r.uncertainty) LIKE '%might%' OR lower(r.uncertainty) LIKE '%depend%' OR lower(r.uncertainty) LIKE '%uncertain%' OR lower(r.uncertainty) LIKE '%need%' OR lower(r.uncertainty) LIKE '%vary%' THEN 5
            ELSE 4
        END AS uncertainty_score,
        CASE
            WHEN lower(r.next_action) LIKE '%test%' OR lower(r.next_action) LIKE '%compare%' OR lower(r.next_action) LIKE '%review%' OR lower(r.next_action) LIKE '%measure%' OR lower(r.next_action) LIKE '%record%' OR lower(r.next_action) LIKE '%validate%' OR lower(r.next_action) LIKE '%revise%' THEN 5
            WHEN trim(r.next_action) <> '' THEN 3
            ELSE 1
        END AS actionability_score,
        CASE
            WHEN COALESCE(s.input_count, 0) >= 3 THEN 5
            WHEN COALESCE(s.input_count, 0) >= 1 THEN 4
            ELSE 2
        END AS traceability_score,
        CASE
            WHEN lower(r.title || ' ' || r.claim || ' ' || r.evidence_summary || ' ' || r.inference || ' ' || r.rejected_alternatives || ' ' || r.uncertainty || ' ' || r.next_action) LIKE '%before%'
              OR lower(r.title || ' ' || r.claim || ' ' || r.evidence_summary || ' ' || r.inference || ' ' || r.rejected_alternatives || ' ' || r.uncertainty || ' ' || r.next_action) LIKE '%after%'
              OR lower(r.title || ' ' || r.claim || ' ' || r.evidence_summary || ' ' || r.inference || ' ' || r.rejected_alternatives || ' ' || r.uncertainty || ' ' || r.next_action) LIKE '%compare%'
              OR lower(r.title || ' ' || r.claim || ' ' || r.evidence_summary || ' ' || r.inference || ' ' || r.rejected_alternatives || ' ' || r.uncertainty || ' ' || r.next_action) LIKE '%comparison%'
              OR lower(r.title || ' ' || r.claim || ' ' || r.evidence_summary || ' ' || r.inference || ' ' || r.rejected_alternatives || ' ' || r.uncertainty || ' ' || r.next_action) LIKE '%delta%'
              OR lower(r.title || ' ' || r.claim || ' ' || r.evidence_summary || ' ' || r.inference || ' ' || r.rejected_alternatives || ' ' || r.uncertainty || ' ' || r.next_action) LIKE '%improv%' THEN 5
            ELSE 2
        END AS improvement_signal_score
    FROM reasoning_episodes r
    LEFT JOIN input_stats s ON s.episode_id = r.id
),
ranked AS (
    SELECT
        scored.*,
        ROUND((
            claim_clarity_score +
            evidence_score +
            inference_score +
            uncertainty_score +
            actionability_score +
            traceability_score +
            improvement_signal_score
        ) / 7.0, 2) AS quality_score,
        LAG(ROUND((
            claim_clarity_score +
            evidence_score +
            inference_score +
            uncertainty_score +
            actionability_score +
            traceability_score +
            improvement_signal_score
        ) / 7.0, 2)) OVER (ORDER BY scored.created_at, scored.id) AS previous_quality_score
    FROM scored
)
SELECT
    ranked.id,
    ranked.episode_key,
    ranked.title,
    ranked.claim,
    ranked.evidence_summary,
    ranked.inference,
    ranked.uncertainty,
    ranked.next_action,
    ranked.status,
    ranked.source_mode,
    ranked.created_at,
    ranked.updated_at,
    ranked.input_count,
    ranked.input_weight,
    ranked.support_input_count,
    ranked.challenge_input_count,
    ranked.claim_clarity_score,
    ranked.evidence_score,
    ranked.inference_score,
    ranked.uncertainty_score,
    ranked.actionability_score,
    ranked.traceability_score,
    ranked.improvement_signal_score,
    ranked.quality_score,
    ranked.previous_quality_score,
    ROUND(ranked.quality_score - COALESCE(ranked.previous_quality_score, ranked.quality_score), 2) AS quality_delta,
    CASE
        WHEN ranked.quality_score >= 4.5 THEN 'excellent'
        WHEN ranked.quality_score >= 4.0 THEN 'strong'
        WHEN ranked.quality_score >= 3.0 THEN 'steady'
        WHEN ranked.quality_score >= 2.0 THEN 'mixed'
        ELSE 'weak'
    END AS quality_band,
    CASE
        WHEN ROUND(ranked.quality_score - COALESCE(ranked.previous_quality_score, ranked.quality_score), 2) > 0 THEN 'improved'
        WHEN ROUND(ranked.quality_score - COALESCE(ranked.previous_quality_score, ranked.quality_score), 2) < 0 THEN 'regressed'
        ELSE 'flat'
    END AS quality_trend
FROM ranked
ORDER BY ranked.created_at DESC, ranked.id DESC;

CREATE VIEW v_reasoning_quality_daily AS
SELECT
    date(created_at) AS day,
    COUNT(*) AS episode_count,
    ROUND(AVG(quality_score), 2) AS avg_quality_score,
    ROUND(AVG(quality_delta), 2) AS avg_quality_delta,
    SUM(CASE WHEN quality_trend = 'improved' THEN 1 ELSE 0 END) AS improved_count,
    SUM(CASE WHEN quality_trend = 'regressed' THEN 1 ELSE 0 END) AS regressed_count,
    ROUND(100.0 * SUM(CASE WHEN quality_trend = 'improved' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS improved_pct
FROM v_reasoning_quality
GROUP BY date(created_at)
ORDER BY day;

CREATE VIEW v_reasoning_quality_summary AS
SELECT
    COUNT(*) AS episode_count,
    ROUND(AVG(quality_score), 2) AS avg_quality_score,
    ROUND(AVG(quality_delta), 2) AS avg_quality_delta,
    SUM(CASE WHEN quality_trend = 'improved' THEN 1 ELSE 0 END) AS improved_count,
    SUM(CASE WHEN quality_trend = 'regressed' THEN 1 ELSE 0 END) AS regressed_count,
    ROUND(100.0 * SUM(CASE WHEN quality_trend = 'improved' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS improved_pct
FROM v_reasoning_quality;
"""
