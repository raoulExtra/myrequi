# Phase 0 auto core review

## review questions
- Is auto clearly identified as the home for project automations?
- Does the versioned docs and implementation layout show up explicitly?
- Do the companion files use the phase-0/auto naming pattern?
- Can the auto subproject grow without confusing the phase 0 story?
- Do the old wrappers remain thin and temporary?
- Are imports package-safe inside the `auto/` folder?
- Does the CLI still expose the known filesystem management triggers?
- Do refresh and checkpoint still regenerate and validate the auto docs?
- Do the tests cover both canonical auto paths and legacy aliases?
- Is the naming aligned across code, docs, and generated outputs?

## current view
These requirements keep the auto subproject visible, versioned, and easy to maintain alongside the phase 0 story.

## type legend

- `manual`: human checked, exception only.
- `code`: mostly code checked.
- `auto_ai`: automation drives the AI-supported work.

## core requirements
- [code] RC001-AUTO: define auto as the project automation subproject.
- [code] RC002-AUTO: keep the versioned implementation layout under `imple/V00.00.01/auto/`.
- [code] RC003-AUTO: keep a stable docs companion file for the auto subproject.
- [code] RC004-AUTO: keep the auto documentation small and easy to review.
- [code] RC005-AUTO: keep thin legacy wrappers at the old paths until migration is complete.
- [code] RC006-AUTO: keep imports package-safe and self-contained inside `auto/`.
- [code] RC007-AUTO: keep the CLI trigger surface stable for manual filesystem actions.
- [code] RC008-AUTO: keep refresh and checkpoint able to regenerate and validate the auto docs.
- [code] RC009-AUTO: keep tests covering both the canonical paths and the legacy aliases.
- [code] RC010-AUTO: keep naming aligned across code, docs, and generated outputs.

## acceptance criteria
### RC001-AUTO
- RC001-AC001-AUTO: auto is described as the place where project automations live.
- RC001-AC002-AUTO: the description stays visible in the phase 0 story.

### RC002-AUTO
- RC002-AC001-AUTO: the implementation path includes a versioned `auto/` directory.
- RC002-AC002-AUTO: the versioned layout is explicit and reusable.

### RC003-AUTO
- RC003-AC001-AUTO: the docs companion file exists under `docs/phase-0/auto/`.
- RC003-AC002-AUTO: the companion keeps the same close-to-phase naming pattern as the phase docs.

### RC004-AUTO
- RC004-AC001-AUTO: the file stays short enough to scan quickly.
- RC004-AC002-AUTO: the file can be updated without breaking the older phase docs.

### RC005-AUTO
- RC005-AC001-AUTO: the old module paths still work during migration.
- RC005-AC002-AUTO: the wrappers clearly point to the canonical `auto/` modules.

### RC006-AUTO
- RC006-AC001-AUTO: package-relative imports work inside the `auto/` folder.
- RC006-AC002-AUTO: the modules do not depend on hidden path hacks.

### RC007-AUTO
- RC007-AC001-AUTO: the CLI keeps the known manual triggers available.
- RC007-AC002-AUTO: filesystem management actions still work from the same command surface.

### RC008-AUTO
- RC008-AC001-AUTO: refresh regenerates the auto docs without manual fixes.
- RC008-AC002-AUTO: checkpoint can validate the auto docs before committing.

### RC009-AUTO
- RC009-AC001-AUTO: tests cover the canonical auto paths.
- RC009-AC002-AUTO: tests still cover the legacy aliases while they exist.

### RC010-AUTO
- RC010-AC001-AUTO: filenames, doc references, and generated outputs use the same naming scheme.
- RC010-AC002-AUTO: the naming stays obvious enough for a future move or cleanup.

## use
This is the canonical phase-0 auto review file.
It mirrors the normal phase naming more closely as `docs/phase-0/auto/phase-0-core-review-auto.md`.
