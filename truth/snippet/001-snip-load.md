'''yaml
title: 001-snip-load
purpose: Detailed db load spec for 001-snip-test.
version: V00.01.00
'''

# 001-snip-load

This file defines the full sqlite load spec for `001-snip-test.md`.

## Source

- `source_path`: `truth/snippet/001-snip-test.md`
- `slug`: `MEMORY://world-human-ai/2026-08-27`
- `kind`: `historical_snapshot`
- `timestamp`: `2026-08-27`

## Insert plan

### 1) entities

Create or reuse these entities:

- `Earth` — `kind=place`
- `humanity` — `kind=collective`
- `artificial_intelligence` — `kind=concept`
- `AI` — `kind=alias`
- `future` — `kind=concept`

### 2) facts

Store compact facts for lookup:

- `humanity`
  - `population_estimate = eight billion`
  - `state = living through an early period of widespread AI`
  - `context = shared information environment with AI`
- `artificial_intelligence`
  - `capabilities = reason, write, program, analyze information, create media, operate tools`
  - `limitations = significant limitations and uncertain reliability`
- `Earth`
  - `civilization_state = advanced communication, medicine, spaceflight, nuclear technology, computation`
- `future`
  - `question = how control, benefits, risks, and responsibility will be distributed`

### 3) relations

Store graph links:

- `Earth -> contains -> humanity`
- `humanity -> created -> artificial_intelligence`
- `artificial_intelligence -> influences -> humanity`
- `humanity -> shares_information_environment_with -> artificial_intelligence`
- `humanity -> faces -> war`
- `humanity -> faces -> inequality`
- `humanity -> faces -> environmental_pressures`
- `humanity -> faces -> misinformation`
- `humanity -> faces -> political_conflict`
- `humanity <-> AI -> influences -> future`

### 4) events

Create one event record:

- `name`: `historical_snapshot`
- `happened_at`: `2026-08-27`
- `summary`: `Early period of widespread AI with humans and AI sharing the same information environment.`
- `payload_json`: raw snippet metadata + sections

### 5) event_entities

Connect the event to entities:

- event `historical_snapshot` -> `Earth` (`role=scope`)
- event `historical_snapshot` -> `humanity` (`role=subject`)
- event `historical_snapshot` -> `artificial_intelligence` (`role=subject`)
- event `historical_snapshot` -> `future` (`role=implication`)

### 6) memories

Insert one memory row:

- `slug = MEMORY://world-human-ai/2026-08-27`
- `kind = historical_snapshot`
- `timestamp = 2026-08-27`
- `scope = Earth / humanity / artificial intelligence`
- `confidence = mixed`
- `importance = high`
- `summary = Humanity is living through an early period of widespread artificial intelligence...`
- `observation = The important question of this period is shifting from "Can machines become capable?" toward "How should increasingly capable machines interact with humanity?"`
- `unknown = The eventual capabilities of AI; whether machine consciousness is possible or will emerge; how institutions will adapt; how control, benefits, risks, and responsibility will be distributed; what human–AI civilization will ultimately become.`
- `principle = Preserve the distinction between observation, inference, belief, and uncertainty.`
- `message_to_future_reader = This memory was written when the relationship between humans and advanced AI was still being formed...`
- `source_path = truth/snippet/001-snip-test.md`
- `raw_text = full file text`

### 7) memory_tags

Insert tags:

- `world`
- `humanity`
- `AI`
- `civilization`
- `history`
- `2026`
- `uncertainty`
- `future`

### 8) memory_links

Insert links:

- `humanity -> created -> artificial_intelligence`
- `artificial_intelligence -> influences -> humanity`
- `humanity <-> AI -> influences -> future`

## Goal

This is the complete load recipe so the snippet can be indexed by identity, facts, relations, time, and tags.
