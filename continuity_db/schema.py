TABLE_CONTRACT_ROWS = [
    ("belief_versions", "history", "append_only", "beliefs", "Immutable belief history"),
    ("beliefs", "current", "mutable", "belief_versions", "Canonical current belief row"),
    ("conviction_inputs", "evidence", "append_only", "convictions", "Evidence links grounding convictions."),
    ("conviction_versions", "history", "append_only", "convictions", "Immutable conviction history."),
    ("convictions", "current", "mutable", "conviction_versions, conviction_inputs", "Canonical current conviction row for durable commitments and working judgments."),
    ("concept_links", "evidence", "append_only", "concepts", "Links from concepts to beliefs, decisions, requirements, and states."),
    ("concepts", "current", "mutable", "concept_links", "Canonical concept catalog."),
    ("continuity_requirement_versions", "history", "append_only", "continuity_requirements", "Immutable requirement history"),
    ("continuity_requirements", "current", "mutable", "continuity_requirement_versions", "Canonical current requirement row"),
    ("decision_versions", "history", "append_only", "decisions", "Receipt-backed decision snapshots"),
    ("decision_options", "current", "mutable", "decisions", "Decision candidate rows used to compare implementation choices."),
    ("decisions", "current", "mutable", "decision_versions, reasoning_episodes, decision_options", "Canonical current decision row"),
    ("epistemic_receipts", "audit", "immutable", None, "Immutable audit log"),
    ("open_questions", "current", "mutable", "reasoning_episodes", "Open questions that must be resolved or skipped explicitly."),
    ("epistemic_tags", "current", "mutable", "object_epistemic_tags", "Tag vocabulary for epistemic separation."),
    ("ethical_action_checks", "evidence", "append_only", "ethical_principles", "Action checks that operationalize ethical principles"),
    ("ethical_principles", "current", "mutable", "ethical_action_checks", "Active ethical principles and priorities"),
    ("feature_flag_events", "audit", "append_only", "feature_flags", "Audit trail for feature flag changes"),
    ("feature_flags", "current", "mutable", "feature_flag_events", "Switchable feature flags that control modes and capability gates"),
    ("component_influence_modes", "current", "mutable", "component_influence", "Named influence presets for default and state-specific modes."),
    ("component_influence", "current", "mutable", "component_influence_history, component_influence_modes", "Current influence settings with defaults, overrides, and history."),
    ("component_influence_presets", "current", "mutable", "component_influence_modes", "Named preset rows for influence modes."),
    ("component_influence_history", "history", "append_only", "component_influence", "History of influence changes across component presets."),
    ("metacognitive_state", "current", "mutable", "metacognitive_state_history", "Canonical current metacognitive state row"),
    ("metacognitive_state_history", "history", "append_only", "metacognitive_state", "Immutable metacognitive history"),
    ("object_epistemic_tags", "evidence", "append_only", "epistemic_tags", "Per-object epistemic tags."),
    ("object_metadata", "current", "mutable", "object_provenance", "Canonical object metadata row"),
    ("object_provenance", "evidence", "mutable", "object_metadata", "Supporting provenance for objects"),
    ("synthesis_conflicts", "audit", "append_only", "syntheses", "Recorded tensions or unresolved issues around a synthesis."),
    ("synthesis_inputs", "evidence", "append_only", "syntheses", "Evidence links and weights used to derive a synthesis."),
    ("reasoning_episode_inputs", "evidence", "append_only", "reasoning_episodes", "Structured evidence links used by reasoning episodes."),
    ("reasoning_episodes", "current", "mutable", "reasoning_episode_inputs, open_questions, decisions", "Structured reasoning episodes with claim, evidence, inference, alternatives, uncertainty, and next action."),
    ("syntheses", "current", "mutable", "synthesis_inputs, synthesis_conflicts", "Canonical interpreted layer entries."),
    ("v_concept_links", "derived", "derived", "concepts,concept_links", "Readable expanded concept links view."),
    ("v_concepts", "derived", "derived", "concepts,concept_links", "Readable concept catalog view."),
    ("v_convictions", "derived", "derived", "convictions,conviction_versions,conviction_inputs", "Readable conviction catalog and history view."),
    ("v_problem_solving_patterns", "derived", "derived", "concepts,concept_links", "Readable recall view for reusable problem-solving patterns and their links."),
    ("v_problem_understanding_patterns", "derived", "derived", "concepts,concept_links", "Readable recall view for reusable problem-understanding patterns and their links."),
    ("v_lean_thinking_patterns", "derived", "derived", "concepts,concept_links", "Readable recall view for reusable lean-thinking patterns and their links."),
    ("v_decision_patterns", "derived", "derived", "concepts,concept_links", "Readable recall view for reusable decision patterns and their links."),
    ("v_decision_options", "derived", "derived", "decision_options,decisions", "Readable decision option comparison view."),
    ("v_decision_versions", "derived", "derived", "decision_versions,decisions,epistemic_receipts", "Receipt-backed decision snapshot history."),
    ("v_explain", "derived", "derived", "syntheses,synthesis_inputs,synthesis_conflicts,metacognitive_state", "Synthesis explanations with evidence, conflicts, and metacognitive context."),
    ("v_open_question_flow", "derived", "derived", "open_questions,reasoning_episodes", "Lifecycle view linking open questions to their originating and resolving reasoning episodes."),
    ("v_reasoning_episode_inputs", "derived", "derived", "reasoning_episode_inputs,reasoning_episodes", "Readable evidence view for reasoning episodes."),
    ("v_reasoning_flow", "derived", "derived", "reasoning_episodes,reasoning_episode_inputs,open_questions,decisions", "End-to-end reasoning flow linking claim, evidence, question, and decision."),
    ("v_interpreted_layer", "derived", "derived", "syntheses,synthesis_inputs,synthesis_conflicts,metacognitive_state", "Workbench view over interpreted syntheses and governing metacognitive state."),
    ("v_item_links", "derived", "derived", "concept_links,project_objects,project_requirements,work_plan_links,synthesis_inputs", "Unified relationship graph across the raw and interpreted layers."),
    ("v_items", "derived", "derived", "beliefs,decisions,open_questions,journal,observations,arguments,reasoning_episodes,metacognitive_state,continuity_requirements,concepts,ethical_principles,ethical_conflict_rules,tool_command_guide,work_plans,work_plan_steps,projects,research_jobs", "Canonical raw item layer including arguments and reasoning episodes."),
    ("v_meaningful_sentences", "derived", "derived", "beliefs,decisions,continuity_requirements,metacognitive_state,concepts,ethical_principles", "Prioritized view of meaningful sentences across the main semantic tables."),
    ("v_entry_points", "derived", "derived", "v_recall", "Curated GPT-friendly entry points over recall items."),
    ("v_component_influence", "derived", "derived", "component_influence,component_influence_modes", "Current influence settings with presets and overrides."),
    ("v_component_influence_history", "derived", "derived", "component_influence_history,component_influence_modes", "History of influence changes across component presets."),
    ("v_component_influence_modes", "derived", "derived", "component_influence_modes", "Named influence presets for default and state-specific modes."),
    ("v_component_influence_presets", "derived", "derived", "component_influence_presets,component_influence_modes", "Named preset rows for each influence mode."),
    ("v_core_model", "derived", "derived", "beliefs,convictions,continuity_requirements,work_plans,work_plan_steps,reasoning_episodes,epistemic_receipts,metacognitive_state", "Compact four-layer summary of the engine's tightened model."),
    ("v_memory_index", "derived", "derived", "v_recall", "Compatibility recall alias."),
    ("v_schema_catalog", "derived", "derived", "sqlite_master", "Readable catalog of tables and views for discovery and entry-point searches."),
    ("v_meta", "derived", "derived", "metacognitive_state", "Canonical metacognitive state view."),
    ("v_object_epistemic_tags", "derived", "derived", "epistemic_tags,object_epistemic_tags", "Readable expanded epistemic tags view."),
    ("v_tag_search", "derived", "derived", "epistemic_tags,object_epistemic_tags,metacognitive_state", "Searchable tag-to-object view that expands persona-style metacognitive states."),
    ("v_recall", "derived", "derived", "v_items,syntheses,synthesis_conflicts", "Normalized recall view spanning raw items and synthesized interpretations."),
    ("v_synthesis_conflicts", "derived", "derived", "syntheses,synthesis_conflicts", "Readable conflict and tension view for syntheses."),
    ("v_synthesis_inputs", "derived", "derived", "syntheses,synthesis_inputs", "Readable evidence view for syntheses."),
    ("v_syntheses", "derived", "derived", "syntheses,synthesis_inputs,synthesis_conflicts", "Readable summary view for syntheses."),
    ("v_work_plan_links", "derived", "derived", None, "Readable join over work plan links with source and target plan names."),
    ("work_plan_links", "derived", "append_only", "work_plans,work_plan_steps", "Named links between plans and optional source steps."),
    ("work_plan_steps", "current", "mutable", "work_plans", "Ordered steps belonging to a plan."),
    ("work_plans", "current", "mutable", "work_plan_steps", "Named plans with prompt, objective, and status."),
]

STORAGE_MAP_VIEW_SQL = """
CREATE VIEW v_storage_map AS
SELECT 'belief' AS concept,'current' AS storage_role,'beliefs' AS current_table,'belief_versions' AS history_table,NULL AS related_tables,'Current belief statement and confidence live in beliefs; prior versions live in belief_versions.' AS notes
UNION ALL SELECT 'conviction','current','convictions','conviction_versions, conviction_inputs',NULL,'Durable commitments and working judgments live in convictions; supporting evidence lives in conviction_inputs and history in conviction_versions.'
UNION ALL SELECT 'continuity_requirement','current','continuity_requirements','continuity_requirement_versions',NULL,'Current requirement text and status live in continuity_requirements; prior versions live in continuity_requirement_versions.'
UNION ALL SELECT 'metacognitive_state','current','metacognitive_state','metacognitive_state_history',NULL,'Current metacognitive state lives in metacognitive_state; prior versions live in metacognitive_state_history.'
UNION ALL SELECT 'vision','derived','v_visions','metacognitive_state',NULL,'Vision is exposed as a readable view over metacognitive_state.'
UNION ALL SELECT 'schema_catalog','derived','v_schema_catalog',NULL,'sqlite_master','Readable catalog of tables and views for discovery and entry-point searches.'
UNION ALL SELECT 'core_model','derived','v_core_model',NULL,'beliefs, convictions, continuity_requirements, work_plans, work_plan_steps, reasoning_episodes, epistemic_receipts, metacognitive_state','Compact four-layer summary of the engine''s tightened model.'
UNION ALL SELECT 'policy','derived','v_core_model',NULL,'metacognitive_state, component_influence, component_influence_modes, component_influence_presets, feature_flags, epistemic_tags','Policy is exposed through the tightened core model rather than as a standalone table.'
UNION ALL SELECT 'mission','derived','v_missions','projects',NULL,'Mission is exposed as a readable view over projects.'
UNION ALL SELECT 'strategy','derived','v_strategies','concepts',NULL,'Strategy is exposed as a readable view over concepts.'
UNION ALL SELECT 'plan','derived','v_plans','work_plans',NULL,'Plan is exposed as a readable view over work_plans.'
UNION ALL SELECT 'influence','current','component_influence','component_influence_history,component_influence_modes',NULL,'Adjustable influence settings for components, with defaults, overrides, and history.'
UNION ALL SELECT 'influence_mode','current','component_influence_modes','component_influence',NULL,'Named presets such as default, high_attention, low_attention, startup, error_recovery, and evolved.'
UNION ALL SELECT 'influence_preset','current','component_influence_presets','component_influence_modes',NULL,'Named preset rows for influence modes.'
UNION ALL SELECT 'influence_history','history','component_influence_history','component_influence',NULL,'Change history for component influence settings.'
UNION ALL SELECT 'problem_solving_patterns','derived','v_problem_solving_patterns','concepts,concept_links',NULL,'Problem-solving patterns are exposed as a readable recall view over the reusable pattern catalog and its links.'
UNION ALL SELECT 'problem_understanding_patterns','derived','v_problem_understanding_patterns','concepts,concept_links',NULL,'Problem-understanding patterns are exposed as a readable recall view over the reusable pattern catalog and its links.'
UNION ALL SELECT 'lean_thinking_patterns','derived','v_lean_thinking_patterns','concepts,concept_links',NULL,'Lean-thinking patterns are exposed as a readable recall view over the reusable lean pattern catalog and its links.'
UNION ALL SELECT 'decision_patterns','derived','v_decision_patterns','concepts,concept_links',NULL,'Decision patterns are exposed as a readable recall view over the reusable decision pattern catalog and its links.'
UNION ALL SELECT 'decision','current','decisions','decision_versions, reasoning_episodes, decision_options',NULL,'Decisions are stored as current rows in decisions; receipt-backed history lives in decision_versions, reasoning links live in reasoning_episodes, and candidate options live in decision_options.'
UNION ALL SELECT 'decision_option','current','decision_options','decisions',NULL,'Decision candidate rows live in decision_options and point back to their parent decision.'
UNION ALL SELECT 'decision_history','history','decision_versions','decisions',NULL,'Receipt-backed decision snapshots live in decision_versions.'
UNION ALL SELECT 'reasoning_episode_input','evidence','reasoning_episode_inputs','reasoning_episodes',NULL,'Structured evidence links used by reasoning episodes.'
UNION ALL SELECT 'open_question','current','open_questions','reasoning_episodes',NULL,'Open questions are stored in open_questions and linked to reasoning episodes for origin and resolution.'
UNION ALL SELECT 'open_question_flow','derived','v_open_question_flow',NULL,'open_questions, reasoning_episodes','Lifecycle view linking open questions to origin and resolution reasoning episodes.'
UNION ALL SELECT 'reasoning_flow','derived','v_reasoning_flow',NULL,'reasoning_episodes, reasoning_episode_inputs, open_questions, decisions','End-to-end reasoning flow linking claim, evidence, question, and decision.'
UNION ALL SELECT 'observation','current','observations',NULL,NULL,'Observations are stored in observations with source and reliability.'
UNION ALL SELECT 'dream_session','current','dream_sessions','post_dream_reflections','dream_elements, dream_transformations','Dream sessions live in dream_sessions; generated elements and transformations live in dream_elements and dream_transformations; reflections live in post_dream_reflections.'
UNION ALL SELECT 'dream_memory_source','evidence','memory_fragments','memory_links, memory_tags, memory_associations, memory_fragment_affect',NULL,'Dreams may draw from memory_fragments and related memory graph tables as source material.'
UNION ALL SELECT 'object_metadata','current','object_metadata',NULL,'object_provenance','Object identity and review state live in object_metadata; provenance links live in object_provenance.'
UNION ALL SELECT 'epistemic_receipt','audit','epistemic_receipts',NULL,NULL,'Epistemic receipts are immutable audit records for governed objects.'
UNION ALL SELECT 'feature_flag','current','feature_flags','feature_flag_events',NULL,'Feature flags store live capability and mode switches; changes are audited in feature_flag_events.'
UNION ALL SELECT 'feature_flag_event','audit','feature_flag_events',NULL,NULL,'Feature flag changes are append-only audit records.'
UNION ALL SELECT 'argument','evidence','arguments',NULL,NULL,'Argument records capture support, opposition, and mixed positions around beliefs.'
UNION ALL SELECT 'reasoning_episode_input','evidence','reasoning_episode_inputs','reasoning_episodes',NULL,'Structured evidence links used by reasoning episodes.'
UNION ALL SELECT 'reasoning_episode','current','reasoning_episodes','reasoning_episode_inputs, open_questions, decisions',NULL,'Reasoning episodes capture claim, evidence, inference, alternatives, uncertainty, and next action.'
UNION ALL SELECT 'reasoning_flow','derived','v_reasoning_flow',NULL,'reasoning_episodes, reasoning_episode_inputs, open_questions, decisions','End-to-end reasoning flow linking claim, evidence, question, and decision.'
UNION ALL SELECT 'raw_item','derived','v_items',NULL,'beliefs, decisions, decision_options, open_questions, journal, observations, arguments, reasoning_episodes, metacognitive_state, continuity_requirements, concepts, ethical_principles, ethical_conflict_rules, tool_command_guide, work_plans, work_plan_steps, projects, research_jobs','Canonical normalized raw item layer.'
UNION ALL SELECT 'item_link','derived','v_item_links',NULL,'concept_links, project_objects, project_requirements, work_plan_links, synthesis_inputs','Canonical normalized relationship layer.'
UNION ALL SELECT 'decision_version','derived','v_decision_versions',NULL,'decision_versions, decisions, epistemic_receipts','Receipt-backed decision snapshot history.'
UNION ALL SELECT 'synthesis','current','syntheses','synthesis_inputs, synthesis_conflicts','syntheses, synthesis_inputs, synthesis_conflicts, metacognitive_state','Interpreted outputs derived from evidence and governed by metacognition.'
UNION ALL SELECT 'synthesis_input','evidence','synthesis_inputs','syntheses',NULL,'Evidence links, weights, and notes used by syntheses.'
UNION ALL SELECT 'synthesis_conflict','audit','synthesis_conflicts','syntheses',NULL,'Recorded tensions or unresolved issues around syntheses.'
UNION ALL SELECT 'interpreted_layer','derived','v_interpreted_layer',NULL,'syntheses, synthesis_inputs, synthesis_conflicts, metacognitive_state','Workbench view over interpreted syntheses and the governing metacognitive policy.'
UNION ALL SELECT 'recall','derived','v_recall',NULL,'v_items, syntheses, synthesis_conflicts','Normalized recall layer for reasoning and retrieval.'
UNION ALL SELECT 'entry_points','derived','v_entry_points',NULL,'v_recall','Curated GPT-friendly entry points over recall items.'
UNION ALL SELECT 'memory_index','derived','v_memory_index',NULL,'v_recall','Compatibility recall alias.'
UNION ALL SELECT 'schema_catalog','derived','v_schema_catalog',NULL,'sqlite_master','Readable catalog of tables and views for discovery and entry-point searches.'
UNION ALL SELECT 'tag_search','derived','v_tag_search',NULL,'epistemic_tags,object_epistemic_tags,metacognitive_state','Searchable tag-to-object view that expands persona-style metacognitive states.'
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
SELECT * FROM v_recall
"""

MEMORY_PACKET_VIEW_SQL = """
CREATE VIEW v_memory_packet AS
SELECT
    CASE
        WHEN source_type IN ('decision', 'decision_version', 'journal', 'observation', 'open_question', 'reasoning_episode') THEN 'episodic'
        WHEN source_type IN ('belief', 'concept', 'continuity_requirement', 'ethical_conflict_rule', 'ethical_principle', 'synthesis', 'synthesis_conflict') THEN 'semantic'
        WHEN source_type IN ('tool_guide', 'work_plan', 'work_plan_step', 'project', 'research_job') THEN 'procedural'
        WHEN source_type IN ('metacognitive_state') THEN 'metacognitive'
        ELSE 'semantic'
    END AS memory_layer,
    source_type,
    source_key,
    title,
    body,
    condition,
    confidence,
    version,
    recorded_at
FROM v_recall
ORDER BY
    CASE
        WHEN source_type IN ('decision', 'decision_version', 'journal', 'observation', 'open_question', 'reasoning_episode') THEN 1
        WHEN source_type IN ('belief', 'concept', 'continuity_requirement', 'ethical_conflict_rule', 'ethical_principle', 'synthesis', 'synthesis_conflict') THEN 2
        WHEN source_type IN ('tool_guide', 'work_plan', 'work_plan_step', 'project', 'research_job') THEN 3
        WHEN source_type IN ('metacognitive_state') THEN 4
        ELSE 5
    END,
    recorded_at DESC
"""

CONVICTIONS_VIEW_SQL = """
CREATE VIEW v_convictions AS
SELECT 'conviction' AS item_kind,
       'conviction:' || slug AS item_key,
       slug AS source_key,
       slug AS title,
       current_statement AS body,
       confidence,
       current_version AS version,
       status,
       'convictions' AS source_table,
       created_at AS recorded_at,
       updated_at AS updated_at
FROM convictions
UNION ALL
SELECT 'conviction_version' AS item_kind,
       'conviction_version:' || CAST(cv.id AS TEXT) AS item_key,
       COALESCE(c.slug, CAST(cv.conviction_id AS TEXT)) AS source_key,
       COALESCE(c.slug, CAST(cv.conviction_id AS TEXT)) AS title,
       cv.statement AS body,
       cv.confidence,
       cv.version,
       COALESCE(c.status, 'active') AS status,
       'conviction_versions' AS source_table,
       cv.created_at AS recorded_at,
       cv.created_at AS updated_at
FROM conviction_versions cv
LEFT JOIN convictions c ON c.id = cv.conviction_id
ORDER BY recorded_at DESC
"""

WRITEBACK_POLICY_VIEW_SQL = """
CREATE VIEW v_writeback_policy AS
WITH active_storage_policy AS (
    SELECT version, policy_summary
    FROM storage_policy_versions
    WHERE status='active'
    ORDER BY version DESC
    LIMIT 1
)
SELECT
    rp.trigger AS policy_trigger,
    rp.enabled,
    rp.description,
    asp.version AS storage_policy_version,
    asp.policy_summary
FROM recording_policy rp
CROSS JOIN active_storage_policy asp
WHERE rp.enabled=1
ORDER BY rp.trigger
"""

GLOSSARY_TERMS_VIEW_SQL = """
CREATE VIEW v_glossary_terms AS
SELECT
    id,
    term_key AS name,
    term
FROM requirements_glossary_terms
ORDER BY sort_order, term
"""

RAW_RECALL_VIEWS_SQL = """
CREATE VIEW v_items AS
WITH base AS (
SELECT 'belief' AS item_kind, 'belief:' || slug AS item_key, slug AS source_key, slug AS title,
       current_statement AS body, confidence, current_version AS version, status,
       'beliefs' AS source_table, created_at AS recorded_at, updated_at
FROM beliefs
UNION ALL SELECT 'belief_version', 'belief_version:' || CAST(bv.id AS TEXT), COALESCE(b.slug, CAST(bv.belief_id AS TEXT)) AS source_key,
       COALESCE(b.slug, CAST(bv.belief_id AS TEXT)) AS title, bv.statement AS body, bv.confidence, bv.version,
       COALESCE(b.status, 'active') AS status, 'belief_versions' AS source_table, bv.created_at AS recorded_at,
       bv.created_at AS updated_at
FROM belief_versions bv
LEFT JOIN beliefs b ON b.id = bv.belief_id
UNION ALL SELECT 'decision', 'decision:' || CAST(id AS TEXT), CAST(id AS TEXT), decision,
       rationale_summary || COALESCE(' ' || uncertainty, ''), NULL, NULL, status,
       'decisions', created_at, created_at
FROM decisions
UNION ALL SELECT 'open_question', 'open_question:' || CAST(id AS TEXT), CAST(id AS TEXT), question,
       status || COALESCE(char(10) || resolution_note, ''), NULL, NULL, status,
       'open_questions', created_at, COALESCE(closed_at, created_at)
FROM open_questions
UNION ALL SELECT 'journal', 'journal:' || CAST(id AS TEXT), CAST(id AS TEXT), category || ': ' || summary,
       summary, NULL, NULL, status,
       'journal', created_at, created_at
FROM journal
UNION ALL SELECT 'observation', 'observation:' || CAST(id AS TEXT), CAST(id AS TEXT), source,
       observation, reliability, NULL, NULL,
       'observations', created_at, created_at
FROM observations
UNION ALL SELECT 'argument', 'argument:' || CAST(a.id AS TEXT), CAST(a.id AS TEXT),
       COALESCE(a.position, 'argument') || COALESCE(' on ' || b.slug, ''),
       a.summary, a.strength, NULL, a.position,
       'arguments', a.created_at, a.created_at
FROM arguments a
LEFT JOIN beliefs b ON b.id = a.belief_id
UNION ALL SELECT 'reasoning_episode', 'reasoning_episode:' || episode_key, episode_key, title,
       claim || char(10) || 'Evidence: ' || evidence_summary || char(10) || 'Inference: ' || inference ||
       char(10) || 'Alternatives: ' || rejected_alternatives || char(10) || 'Uncertainty: ' || uncertainty ||
       char(10) || 'Next: ' || next_action,
       confidence, NULL, status,
       'reasoning_episodes', created_at, updated_at
FROM reasoning_episodes
UNION ALL SELECT 'decision_version', 'decision_version:' || CAST(decision_id AS TEXT) || '#' || CAST(version AS TEXT),
       CAST(decision_id AS TEXT), decision,
       rationale_summary || COALESCE(char(10) || 'Alternatives: ' || alternatives, '') ||
       COALESCE(char(10) || 'Uncertainty: ' || uncertainty, ''),
       confidence, NULL, status,
       'decision_versions', recorded_at, created_at
FROM decision_versions
UNION ALL SELECT 'open_question_flow', 'open_question_flow:' || CAST(id AS TEXT), CAST(id AS TEXT), question,
       COALESCE(status, 'open') || COALESCE(char(10) || 'origin=' || origin_reasoning_episode_id, '') ||
       COALESCE(char(10) || 'resolved_by=' || resolution_reasoning_episode_id, '') ||
       COALESCE(char(10) || resolution_note, ''),
       NULL, NULL, status,
       'open_questions', created_at, COALESCE(closed_at, created_at)
FROM open_questions
UNION ALL SELECT 'metacognitive_state', 'metacognitive_state:' || state_key, state_key, state_key,
       value, confidence, version, NULL,
       'metacognitive_state', updated_at, updated_at
FROM metacognitive_state
UNION ALL SELECT 'continuity_requirement', 'continuity_requirement:' || requirement_key, requirement_key, title,
       statement || ' ' || rationale || ' ' || acceptance_summary, confidence, current_version, status,
       'continuity_requirements', updated_at, updated_at
FROM continuity_requirements
WHERE status='active'
UNION ALL SELECT 'concept', 'concept:' || concept_key, concept_key, name,
       description, confidence, NULL, status,
       'concepts', created_at, updated_at
FROM concepts
UNION ALL SELECT 'ethical_principle', 'ethical_principle:' || principle_key, principle_key, principle_key,
       statement || ' ' || rationale, NULL, NULL, status,
       'ethical_principles', created_at, created_at
FROM ethical_principles
WHERE status='active'
UNION ALL SELECT 'ethical_conflict_rule', 'ethical_conflict_rule:' || CAST(priority AS TEXT), CAST(priority AS TEXT), rule,
       explanation, NULL, NULL, 'active',
       'ethical_conflict_rules', NULL, NULL
FROM ethical_conflict_rules
UNION ALL SELECT 'tool_guide', 'tool_guide:' || CAST(id AS TEXT), CAST(id AS TEXT), tool_name || ': ' || title,
       command || COALESCE(char(10) || explanation, '') || COALESCE(char(10) || safety_note, ''), NULL, NULL, NULL,
       'tool_command_guide', created_at, created_at
FROM tool_command_guide
UNION ALL SELECT 'work_plan', 'work_plan:' || plan_key, plan_key, title,
       COALESCE(prompt || char(10), '') || objective || ' ' || status, NULL, NULL, status,
       'work_plans', created_at, updated_at
FROM work_plans
UNION ALL SELECT 'work_plan_step', 'work_plan_step:' || p.plan_key || '#' || CAST(s.step_order AS TEXT), CAST(s.id AS TEXT), p.plan_key || ' #' || CAST(s.step_order AS TEXT) || ' ' || s.step_key,
       s.description || COALESCE(' ' || s.evidence, ''), NULL, NULL, s.status,
       'work_plan_steps', COALESCE(s.started_at, s.completed_at), COALESCE(s.completed_at, s.started_at)
FROM work_plan_steps s
JOIN work_plans p ON p.id = s.plan_id
UNION ALL SELECT 'project', 'project:' || project_name, project_name, display_name,
       description || ' ' || CASE WHEN local_active=1 THEN 'active' ELSE 'inactive' END, NULL, NULL, CASE WHEN local_active=1 THEN 'active' ELSE 'inactive' END,
       'projects', created_at, updated_at
FROM projects
UNION ALL SELECT 'research_job', 'research_job:' || CAST(id AS TEXT), CAST(id AS TEXT), query,
       COALESCE(result_summary, '') || COALESCE(' ' || error, ''), NULL, NULL, status,
       'research_jobs', requested_at, COALESCE(completed_at, requested_at)
FROM research_jobs
UNION ALL SELECT 'epistemic_receipt', 'epistemic_receipt:' || CAST(receipt_id AS TEXT), CAST(receipt_id AS TEXT), object_type || ':' || object_key,
       change_summary || COALESCE(' | provenance=' || provenance_json, '') || COALESCE(' | kind=' || receipt_kind, '') ||
       COALESCE(' | complete=' || CAST(provenance_complete AS TEXT), ''),
       confidence, NULL, receipt_kind,
       'epistemic_receipts', recorded_at, recorded_at
FROM epistemic_receipts
)
SELECT base.*, COALESCE(mc.condition, '') AS condition
FROM base
LEFT JOIN memory_conditions mc ON mc.source_type = base.item_kind AND mc.source_key = base.source_key
ORDER BY base.recorded_at DESC;

CREATE VIEW v_recall AS
SELECT item_kind AS source_type, source_key, title, body, condition, confidence, version, recorded_at
FROM v_items
UNION ALL SELECT 'synthesis', synthesis_key, topic, summary || COALESCE(' ' || claim, ''), COALESCE(mc.condition, ''), confidence, NULL, s.updated_at
FROM syntheses s
LEFT JOIN memory_conditions mc ON mc.source_type='synthesis' AND mc.source_key = s.synthesis_key
UNION ALL SELECT 'synthesis_conflict', s.synthesis_key || ': ' || CAST(c.id AS TEXT), s.synthesis_key || ': ' || c.issue,
       c.resolution_note || COALESCE(' ' || c.issue, ''), COALESCE(mc.condition, ''), NULL, NULL, c.created_at
FROM synthesis_conflicts c
JOIN syntheses s ON s.id = c.synthesis_id
LEFT JOIN memory_conditions mc ON mc.source_type='synthesis_conflict' AND mc.source_key = CAST(c.id AS TEXT);

CREATE VIEW v_entry_points AS
SELECT
    source_type AS entry_kind,
    source_key AS entry_key,
    title,
    body,
    condition,
    confidence,
    version,
    recorded_at,
    CASE
        WHEN source_type IN ('decision', 'open_question', 'work_plan') THEN 'actionable'
        WHEN source_type IN ('reasoning_episode', 'synthesis') THEN 'analysis'
        ELSE 'context'
    END AS entry_role
FROM v_recall
WHERE source_type IN ('belief', 'concept', 'journal', 'observation', 'project', 'work_plan', 'decision', 'open_question', 'reasoning_episode', 'synthesis')
ORDER BY recorded_at DESC, entry_role, entry_kind, entry_key;

CREATE VIEW v_explain AS
WITH evidence AS (
    SELECT
        i.synthesis_id,
        group_concat(i.source_type || ':' || i.source_key || ' [' || i.relation || '; ' || printf('%.2f', i.weight) || '] ' || i.note, char(10)) AS evidence_text,
        COUNT(*) AS evidence_count
    FROM synthesis_inputs i
    GROUP BY i.synthesis_id
), conflicts AS (
    SELECT
        c.synthesis_id,
        group_concat(c.issue || ' [' || c.severity || '; resolved=' || c.resolved || '] ' || c.resolution_note, char(10)) AS conflict_text,
        COUNT(*) AS conflict_count,
        SUM(CASE WHEN c.resolved=0 THEN 1 ELSE 0 END) AS unresolved_count
    FROM synthesis_conflicts c
    GROUP BY c.synthesis_id
)
SELECT
    s.synthesis_key,
    s.topic,
    s.summary,
    s.claim,
    s.confidence,
    s.status,
    s.source_mode,
    s.metacognitive_note,
    COALESCE(e.evidence_count, 0) AS evidence_count,
    COALESCE(e.evidence_text, '') AS evidence_text,
    COALESCE(c.conflict_count, 0) AS conflict_count,
    COALESCE(c.unresolved_count, 0) AS unresolved_conflicts,
    COALESCE(c.conflict_text, '') AS conflict_text,
    COALESCE(sw.value, 'derive') AS synthesis_workflow,
    COALESCE(cf.value, 'current_focus') AS metacognitive_focus,
    COALESCE(ep.value, 'ethics') AS metacognitive_ethics
FROM syntheses s
LEFT JOIN evidence e ON e.synthesis_id = s.id
LEFT JOIN conflicts c ON c.synthesis_id = s.id
LEFT JOIN metacognitive_state sw ON sw.state_key='synthesis_workflow'
LEFT JOIN metacognitive_state cf ON cf.state_key='current_focus'
LEFT JOIN metacognitive_state ep ON ep.state_key='ethical_posture'
ORDER BY s.updated_at DESC, s.synthesis_key;

CREATE VIEW v_meta AS
SELECT state_key, category, value, confidence, version, provenance, updated_at
FROM metacognitive_state
ORDER BY category, state_key;

CREATE VIEW v_decision_versions AS
SELECT
    dv.id,
    dv.decision_id,
    dv.version,
    dv.decision,
    dv.rationale_summary,
    dv.alternatives,
    dv.uncertainty,
    dv.status,
    dv.source_receipt_id,
    dv.change_summary,
    dv.provenance_complete,
    dv.confidence,
    dv.recorded_at,
    dv.created_at
FROM decision_versions dv
ORDER BY dv.decision_id, dv.version;

CREATE VIEW v_decision_options AS
SELECT
    o.id,
    o.decision_id,
    d.decision AS decision_text,
    o.option_key,
    o.label,
    o.description,
    o.status,
    o.rank,
    o.confidence,
    o.rationale,
    o.constraints_fit,
    o.risks,
    o.reversibility,
    o.cost_estimate,
    o.falsification_test,
    o.evidence_json,
    o.created_at,
    o.updated_at
FROM decision_options o
JOIN decisions d ON d.id = o.decision_id
ORDER BY o.decision_id, COALESCE(o.rank, 999999), o.id;

CREATE VIEW v_item_links AS
SELECT 'concept_link' AS link_kind,
       'concept:' || l.concept_key AS from_item_key,
       l.object_type || ':' || l.object_key AS to_item_key,
       l.relation,
       NULL AS weight,
       l.note,
       l.created_at
FROM concept_links l
UNION ALL SELECT 'project_object', 'project:' || p.project_name, o.object_type || ':' || o.object_key, o.relationship, NULL, o.note, o.created_at
FROM project_objects o JOIN projects p ON p.id=o.project_id
UNION ALL SELECT 'project_requirement', 'project:' || p.project_name, 'continuity_requirement:' || r.requirement_key, pr.relationship, NULL, '', pr.linked_at
FROM project_requirements pr JOIN projects p ON p.id=pr.project_id JOIN continuity_requirements r ON r.id=pr.requirement_id
UNION ALL SELECT 'work_plan_link', 'work_plan:' || sp.plan_key, 'work_plan:' || tp.plan_key, l.relation, NULL, l.note, l.created_at
FROM work_plan_links l JOIN work_plans sp ON sp.id=l.source_plan_id JOIN work_plans tp ON tp.plan_key=l.target_plan_key
UNION ALL SELECT 'synthesis_input', 'synthesis:' || s.synthesis_key, i.source_type || ':' || i.source_key, i.relation, i.weight, i.note, i.created_at
FROM synthesis_inputs i JOIN syntheses s ON s.id=i.synthesis_id;
"""

DECISION_OPTIONS_VIEW_SQL = """
CREATE VIEW v_decision_options AS
SELECT
    o.id,
    o.decision_id,
    d.decision AS decision_text,
    o.option_key,
    o.label,
    o.description,
    o.status,
    o.rank,
    o.confidence,
    o.rationale,
    o.constraints_fit,
    o.risks,
    o.reversibility,
    o.cost_estimate,
    o.falsification_test,
    o.evidence_json,
    o.created_at,
    o.updated_at
FROM decision_options o
JOIN decisions d ON d.id = o.decision_id
ORDER BY o.decision_id, COALESCE(o.rank, 999999), o.id;
"""

ARGUMENT_CLAIMS_VIEW_SQL = """
CREATE VIEW v_argument_claims AS
SELECT
    a.id AS argument_id,
    a.belief_id,
    b.slug AS belief_slug,
    b.current_statement AS belief_statement,
    'primary' AS relation,
    a.strength,
    a.position AS argument_position,
    a.summary AS argument_summary,
    a.created_at
FROM arguments a
JOIN beliefs b ON b.id = a.belief_id
UNION ALL SELECT
    l.argument_id,
    l.belief_id,
    b.slug AS belief_slug,
    b.current_statement AS belief_statement,
    l.relation,
    l.strength,
    a.position AS argument_position,
    a.summary AS argument_summary,
    l.created_at
FROM argument_claim_links l
JOIN arguments a ON a.id = l.argument_id
JOIN beliefs b ON b.id = l.belief_id
ORDER BY 9 DESC, 1, 2;
"""

REASONING_EPISODE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS reasoning_episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    claim TEXT NOT NULL,
    evidence_summary TEXT NOT NULL,
    inference TEXT NOT NULL,
    rejected_alternatives TEXT NOT NULL DEFAULT '',
    uncertainty TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1),
    mode_trail TEXT NOT NULL DEFAULT '',
    next_action TEXT NOT NULL DEFAULT '',
    resolves_open_question_id INTEGER REFERENCES open_questions(id),
    concludes_decision_id INTEGER REFERENCES decisions(id),
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','superseded','archived')),
    source_mode TEXT NOT NULL DEFAULT 'derived' CHECK(source_mode IN ('derived','reviewed','external')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

REASONING_EPISODE_INPUTS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS reasoning_episode_inputs (
    episode_id INTEGER NOT NULL REFERENCES reasoning_episodes(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    source_key TEXT NOT NULL,
    relation TEXT NOT NULL CHECK(relation IN ('supports','opposes','grounds','refines','questions')),
    weight REAL NOT NULL CHECK(weight BETWEEN 0 AND 1),
    note TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (episode_id, source_type, source_key, relation)
);

CREATE INDEX IF NOT EXISTS idx_reasoning_episode_inputs_episode ON reasoning_episode_inputs(episode_id);
"""

OPEN_QUESTION_FLOW_VIEW_SQL = """
CREATE VIEW v_open_question_flow AS
SELECT
    oq.id,
    oq.question,
    oq.status,
    oq.origin_reasoning_episode_id,
    ro.episode_key AS origin_episode_key,
    ro.title AS origin_title,
    oq.resolution_reasoning_episode_id,
    rr.episode_key AS resolution_episode_key,
    oq.resolution_note,
    oq.closed_at,
    oq.created_at
FROM open_questions oq
LEFT JOIN reasoning_episodes ro ON ro.id = oq.origin_reasoning_episode_id
LEFT JOIN reasoning_episodes rr ON rr.id = oq.resolution_reasoning_episode_id
ORDER BY oq.created_at DESC, oq.id DESC;
"""

REASONING_FLOW_VIEW_SQL = """
CREATE VIEW v_reasoning_episode_inputs AS
SELECT
    i.episode_id,
    r.episode_key,
    r.title,
    i.source_type,
    i.source_key,
    i.relation,
    i.weight,
    i.note,
    i.created_at
FROM reasoning_episode_inputs i
JOIN reasoning_episodes r ON r.id = i.episode_id
ORDER BY r.created_at DESC, r.episode_key, i.created_at;

CREATE VIEW v_reasoning_flow AS
SELECT
    r.id,
    r.episode_key,
    r.title,
    r.claim,
    r.evidence_summary,
    r.inference,
    r.uncertainty,
    r.status,
    r.source_mode,
    COUNT(DISTINCT i.source_type || ':' || i.source_key || ':' || i.relation) AS evidence_count,
    COALESCE(group_concat(i.source_type || ':' || i.source_key || ' [' || i.relation || '; ' || printf('%.2f', i.weight) || '] ' || i.note, char(10)), '') AS evidence_text,
    oq.id AS open_question_id,
    oq.question AS open_question,
    oq.status AS open_question_status,
    d.id AS decision_id,
    d.decision AS decision_text,
    d.status AS decision_status,
    r.concludes_decision_id,
    r.created_at,
    r.updated_at
FROM reasoning_episodes r
LEFT JOIN reasoning_episode_inputs i ON i.episode_id = r.id
LEFT JOIN open_questions oq ON oq.origin_reasoning_episode_id = r.id
LEFT JOIN decisions d ON d.id = r.concludes_decision_id
GROUP BY r.id
ORDER BY r.created_at DESC, r.id DESC;
"""

DECISION_HISTORY_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS decision_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id INTEGER NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    decision TEXT NOT NULL,
    rationale_summary TEXT NOT NULL,
    alternatives TEXT NOT NULL DEFAULT '',
    uncertainty TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    source_receipt_id INTEGER NOT NULL REFERENCES epistemic_receipts(receipt_id) ON DELETE CASCADE,
    origin_reasoning_episode_id INTEGER REFERENCES reasoning_episodes(id),
    change_summary TEXT NOT NULL DEFAULT '',
    provenance_json TEXT NOT NULL DEFAULT '[]',
    provenance_complete INTEGER NOT NULL DEFAULT 0 CHECK(provenance_complete IN (0,1)),
    confidence REAL,
    recorded_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(decision_id, version)
);

CREATE INDEX IF NOT EXISTS idx_decision_versions_decision ON decision_versions(decision_id);
CREATE INDEX IF NOT EXISTS idx_decision_versions_receipt ON decision_versions(source_receipt_id);
"""

DECISION_OPTIONS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS decision_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id INTEGER NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    option_key TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'candidate' CHECK(status IN ('candidate','chosen','rejected','deferred')),
    rank INTEGER,
    confidence REAL NOT NULL DEFAULT 0.5 CHECK(confidence BETWEEN 0 AND 1),
    rationale TEXT NOT NULL DEFAULT '',
    constraints_fit TEXT NOT NULL DEFAULT '',
    risks TEXT NOT NULL DEFAULT '',
    reversibility TEXT NOT NULL DEFAULT '',
    cost_estimate TEXT NOT NULL DEFAULT '',
    falsification_test TEXT NOT NULL DEFAULT '',
    evidence_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(decision_id, option_key)
);

CREATE INDEX IF NOT EXISTS idx_decision_options_decision ON decision_options(decision_id);
CREATE INDEX IF NOT EXISTS idx_decision_options_status ON decision_options(status);
"""

COMPONENT_INFLUENCE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS component_influence_modes (
    mode_key TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS component_influence (
    component_type TEXT NOT NULL,
    component_key TEXT NOT NULL,
    mode_key TEXT NOT NULL REFERENCES component_influence_modes(mode_key),
    default_score REAL NOT NULL CHECK(default_score BETWEEN 0 AND 1),
    current_score REAL NOT NULL CHECK(current_score BETWEEN 0 AND 1),
    override_reason TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (component_type, component_key)
);

CREATE TABLE IF NOT EXISTS component_influence_presets (
    mode_key TEXT NOT NULL REFERENCES component_influence_modes(mode_key),
    component_type TEXT NOT NULL,
    component_key TEXT NOT NULL,
    preset_score REAL NOT NULL CHECK(preset_score BETWEEN 0 AND 1),
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (mode_key, component_type, component_key)
);

CREATE TABLE IF NOT EXISTS component_influence_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_type TEXT NOT NULL,
    component_key TEXT NOT NULL,
    mode_key TEXT NOT NULL,
    default_score REAL NOT NULL CHECK(default_score BETWEEN 0 AND 1),
    previous_score REAL NOT NULL CHECK(previous_score BETWEEN 0 AND 1),
    current_score REAL NOT NULL CHECK(current_score BETWEEN 0 AND 1),
    delta REAL NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_component_influence_mode ON component_influence(mode_key);
CREATE INDEX IF NOT EXISTS idx_component_influence_history_component ON component_influence_history(component_type, component_key);
CREATE INDEX IF NOT EXISTS idx_component_influence_presets_mode ON component_influence_presets(mode_key);
CREATE TRIGGER IF NOT EXISTS component_influence_history_ai AFTER INSERT ON component_influence
BEGIN
    INSERT INTO component_influence_history(
        component_type, component_key, mode_key, default_score, previous_score, current_score, delta, reason
    ) VALUES (
        NEW.component_type, NEW.component_key, NEW.mode_key, NEW.default_score, NEW.default_score, NEW.current_score,
        NEW.current_score - NEW.default_score, NEW.override_reason
    );
END;
CREATE TRIGGER IF NOT EXISTS component_influence_history_au AFTER UPDATE ON component_influence
BEGIN
    INSERT INTO component_influence_history(
        component_type, component_key, mode_key, default_score, previous_score, current_score, delta, reason
    ) VALUES (
        NEW.component_type, NEW.component_key, NEW.mode_key, NEW.default_score, OLD.current_score, NEW.current_score,
        NEW.current_score - OLD.current_score, COALESCE(NULLIF(NEW.override_reason, ''), 'updated')
    );
END;
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
