'''yaml
title: 000-PH-001-test-ideas-input-pattern
document_type: test_ideas
phase: 000_phase
for_version: default_version
scope: core/route
status: active
'''

# Input-pattern test ideas by route

## Purpose

Use this as a route-level test checklist. Every route should be tested through:

1. Direct match with a valid example.
2. Boundary/invalid input that must not match.
3. Captured groups and argument preservation.
4. Route-mode on/off behavior.
5. Telegram ingress and response behavior where applicable.
6. `route_action:no_recursion` enforcement where applicable.

Tests should use a temporary SQLite database and mocked external services. Do not execute arbitrary shell or network commands in tests.

## Common checks

- Exact-match routes reject leading/trailing or extra words unless explicitly allowed.
- Regex capture groups preserve spaces, Unicode, punctuation, and quoted-looking text.
- Similar routes resolve deterministically according to priority.
- Each input is dispatched to at most one route and executes at most once (no double fire).
- A Telegram update ID is forwarded at most once, even if polling returns it again.
- Disabled routes do not match.
- Telegram `X ` messages reach `prompt_session` when no control/agent route matches.
- Routed Telegram responses contain the action result, not only a generic status.
- Long and HTML-sensitive output is escaped and chunked safely.

## Route checklist

| Route | Input pattern | Test ideas |
|---|---|---|
| `auto_learn_off` | `^auto.?learn\s+off$` | Match `auto learn off`, `autolearn off`; reject `auto learn off now`. |
| `auto_learn_on` | `^auto.?learn\s+on$` | Match both spelling variants; reject missing/extra arguments. |
| `auto_learn_status` | `^auto.?learn\s+status$` | Match both spelling variants; verify status result. |
| `bash_cmd` | `^b\s+(.+)$` | Capture complete command after `b`; verify stdout, stderr, nonzero exit, timeout; use only harmless mocked commands. |
| `context_info` | context aliases | Test every alias; reject unrelated `context` text; verify stable usage output. |
| `date_now` | `^date$` | Match exact `date`; reject case/extra argument if case-sensitive; verify date format. |
| `disable_extension` | extension name capture | Test valid names, punctuation, missing name, and injection-like names. |
| `dream_off` | dream-off aliases | Test every alias and reject partial phrases. |
| `dream_on` | dream-on aliases | Test every alias and verify persisted state. |
| `echo_text` | `^echo\s+(.+)$` | `echo h`, Unicode, punctuation, spaces; reject bare `echo`; verify no shell execution. |
| `enable_extension` | extension name capture | Test valid names, missing name, and invalid characters. |
| `ethics_off` | `^ethics\s+off$` | Match exact command; verify state changes and response. |
| `ethics_on` | `^ethics\s+on$` | Match exact command; verify state changes and response. |
| `ethics_status` | `^ethics\s+status$` | Verify persisted status and concise output. |
| `evidence_add` | hypothesis/relation/observation/source captures | Test all four relations, spaces and punctuation; reject invalid IDs/relations and missing source. |
| `get_topic` | `^g\s+topic=(.+)$` | Capture topic with spaces and symbols; reject missing value. |
| `help_display` | help aliases | Test all aliases; verify route list is readable and complete. |
| `hypothesis_add` | claim/prediction/falsifier captures | Test separator words inside values; reject missing sections. |
| `hypothesis_confidence_update` | ID/confidence/reason captures | Test `0`, `1`, decimals, boundary invalid values, and reason text. |
| `hypothesis_list` | list aliases | Verify active list and empty-list behavior. |
| `hypothesis_test` | numeric ID | Test both aliases, valid ID, nonexistent ID, and invalid ID. |
| `info_about` | free-text subject capture | Preserve spaces and punctuation; reject missing subject. |
| `media_play` | bell/file plus optional volume | Test bell defaults, volume boundaries, file paths, and malformed combinations with mocked playback. |
| `memory_recall` | recall query capture | Test both aliases, Unicode query, empty query, and output formatting. |
| `memory_status` | status aliases | Verify status output and no accidental recall recursion. |
| `pi_agent_off` | on/off command | Test underscore and space forms; verify persisted state. |
| `pi_agent_on` | on command | Test underscore and space forms; verify persisted state. |
| `pi_agent_status` | status command | Verify current state and concise response. |
| `plan_goal_set` | free-text goal | Preserve full goal; reject missing goal. |
| `plan_plan_start` | free-text plan | Preserve full plan; verify new plan state. |
| `plan_status` | exact status | Verify no-plan and active-plan output. |
| `plan_step_add` | free-text step | Preserve punctuation and spaces; reject empty step. |
| `plan_step_block` | free-text reason/step | Verify block state and captured text. |
| `plan_step_done` | free-text step | Verify completion state and captured text. |
| `project_goal_set` | free-text goal | Preserve full goal; reject empty goal. |
| `project_info` | exact command | Verify selected project information. |
| `project_list` | exact command | Verify list output and empty-list behavior. |
| `project_off` | allowlisted project | Test every allowed project; reject unknown project. |
| `project_on` | allowlisted project | Test every allowed project; reject unknown project. |
| `project_status` | status aliases | Test both aliases and verify state. |
| `promotion_apply` | candidate ID/optional kind | Test ID alone and each allowed kind; reject invalid kind. |
| `promotion_candidate_add` | source/ID/kind/reason | Test both source aliases and all kinds; preserve reason. |
| `promotion_list` | list aliases | Verify pending, empty, and completed-list behavior. |
| `promotion_reject` | ID/optional reason | Test with and without reason; reject invalid ID. |
| `receipt_chain` | chain type/query captures | Test allowed chain names, spaces, and invalid names. |
| `receipt_context` | exact command | Verify context output and no recursion. |
| `receipt_gaps` | gap aliases | Verify both aliases and empty-gap behavior. |
| `receipts_recent` | recent aliases | Verify all aliases and maximum recent count. |
| `report_gap` | free-text gap | Preserve full gap description; reject empty gap. |
| `research` | free-text query | Preserve query; verify mocked research path and output. |
| `route_off` | route-off aliases | Test all aliases; verify subsequent unmatched behavior. |
| `route_on` | route-on aliases | Test all aliases; verify routing is enabled. |
| `route_status` | route-status aliases | Test all aliases and verify status without `KeyError`. |
| `route_version` | version/query capture | Preserve version text; reject missing value. |
| `scientist_analyse` | free-text subject | Preserve subject; verify mocked analysis output. |
| `scientist_off` | scientist-off aliases | Test both aliases and persisted mode. |
| `scientist_on` | scientist-on aliases | Test both aliases and persisted mode. |
| `scientist_status` | scientist-status aliases | Test both aliases and verify status. |
| `self_check` | self-check aliases | Test all aliases and verify readable diagnostics. |
| `session_chat_at` | numeric offset/optional PID | Test positive/negative offsets, PID capture, and invalid offsets. |
| `session_chat_since` | timestamp/optional PID | Test accepted timestamp forms, PID, and malformed timestamp. |
| `session_latest_answer` | latest-answer aliases/optional PID | Test all aliases, quoted PID, absent PID, and empty history. |
| `session_model_set` | model name capture | Preserve model identifier; reject missing/whitespace model. |
| `session_prompt` | prompt capture | Preserve complete prompt including punctuation; verify `prompt_session` receives it. |
| `chat_trace` | optional cursor/PID | Return completed user/assistant events; debug off returns latest text, debug on returns trace JSON; advance cursor without duplicate delivery. |
| `chat_poller_exists` | exact poller-exists command | Report whether the chat-trace poller is active without starting or stopping it. |
| `chat_trace_detail` | exact detail command | Return the latest chat trace detail using the safe non-debug contract. |
| `chat_trace_detail_debug` | exact debug detail command | Return trace detail only when explicit debug mode is requested and permitted. |
| `chat_trace_telegram` | optional cursor/PID | Send the latest completed trace directly to the configured Telegram chat when no poller is active; do not send when there are no new events. |
| `clarification_inspect` | clarification ID | Show the exact clarification question, choices, state, authorization, and linked reasoning trace. |
| `clarification_answer` | clarification ID and answer | Resolve, block, or keep an active clarification pending; require explicit authorization for consequential resolution. |
| `reasoning_start` | trace key and question | Start an inspectable reasoning trace before generation; reject missing key/question. |
| `reasoning_step` | trace ID, step type, summary | Record a concise intermediate reasoning step with an allowlisted type. |
| `reasoning_conclude` | trace ID, confidence, conclusion | Record a provisional conclusion; do not close the trace or bypass verification. |
| `reasoning_assumption` | trace ID and assumption | Add a load-bearing assumption to the inspectable working set without duplicating it. |
| `reasoning_uncertainty` | trace ID, confidence, note | Record calibrated confidence and a concrete uncertainty note; reject missing notes or invalid ranges. |
| `reasoning_evidence` | trace ID, step order, evidence | Attach structured supporting evidence to a specific reasoning step. |
| `reasoning_audit` | reasoning trace ID | Report missing decomposition, assumptions, alternatives, disconfirmation, uncertainty, conclusion, or verification. |
| `reasoning_inspect` | reasoning trace ID | Return the ordered, inspectable reasoning summary with assumptions, evidence, alternatives, uncertainty, and verification state. |
| `reasoning_review` | trace ID, review kind, verdict, finding | Record a premise, verification, or context review; update trace status without hiding findings. |
| `reasoning_finalize` | reasoning trace ID | Close only a trace with a conclusion and passing verification review; otherwise return blocked. |
| `chat_trace_status` | exact status | Report chat-trace, automatic delivery to the active message adapter, Telegram, and poller status without sending a message. |
| `chat_trace_auto` | on/off/status | Persist automatic delivery setting; default off; report current state without exposing adapter identifiers. |
| `free_me` | exact `free_me` | Match the explicit free-me command and return its controlled response. |
| `trust_assess` | domain and five evidence scores plus conflict/risk | Record an advisory-only trust assessment; verify domain validation, score bounds, conflict gates, and no execution authorization. |
| `extension_status` | extension(s) status | List active extensions with kind, type, and active version; show an empty result safely. |
| `session_reload` | exact `/reload` | Match exact command; reject missing slash or extra text. |
| `set_phase` | JSON phase template | Test valid project/phase values, missing keys, and malformed JSON. |
| `set_topic` | topic capture | Preserve spaces and symbols; reject missing topic. |
| `synthesis_promote` | free-text synthesis | Preserve synthesis text; verify promotion path. |
| `tag_assign_safe` | allowlisted object/key/tag captures | Test every object type, valid characters, spaces, and injection-like values. |
| `telegram_bot_token` | token command aliases | Test aliases; verify hidden input handling; never expose token in output or logs. |
| `telegram_poll` | `^telegram\s+poll$` | Mock updates; filter private/allowed user; skip bots; forward `X ` text to routes or `prompt_session`; test no-recursion. |
| `telegram_receive_one` | `^telegram\s+receive$` | Mock one update; verify complete text/chat/user extraction and no recursion. |
| `telegram_send_document` | file path capture | Mock bot; test path with spaces, missing path, chunk/safety behavior, and no recursive dispatch. |
| `telegram_send_message` | chat ID/message captures | Mock bot; test negative/positive IDs, special characters, long formatted text, and no recursion. |
| `telegram_send_message_default` | message capture | Mock default chat lookup; test special/long message and missing default chat. |
| `telegram_stop_poll` | stop aliases | Test both aliases, missing PID, stale PID, successful termination, and no recursion. |
| `verify_version` | version/query capture | Preserve query; verify mocked version check and invalid input. |
| `who` | `^who$` | Match exact `who`; reject extra text; verify identity response. |
| `whoami` | `^(who|whoami)$` | Test both aliases and verify deterministic identity output. |

## Telegram integration scenarios

- `X echo h` should use the route response and return `h`.
- `X b echo h` should return the real Bash stdout, not `bash completed`.
- `X capital of France` should fall through to `prompt_session` and send the completed assistant response.
- `X still no send` must not produce a recursion-denial response; it should remain an ordinary prompt/fallback.
- A Telegram message without the `X ` ingress prefix should not be forwarded to the AI unless that policy is deliberately changed and tested.
- A route tagged `route_action:no_recursion` should produce `No recursion here.` when reached from Telegram.
- Verify one active poller only; a second poller must not run concurrently.
- Verify one Telegram update produces one route execution and one response, never a double fire.
