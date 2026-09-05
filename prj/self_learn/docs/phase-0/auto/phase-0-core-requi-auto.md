# Phase 0 auto core requirements

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
- [code] RC011-AUTO: keep auto as the canonical home for automation code and the related support files.

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

### RC011-AUTO
- RC011-AC001-AUTO: the canonical home stays under `imple/V00.00.01/auto/`.
- RC011-AC002-AUTO: every canonical auto module lives in the `auto/` package.
- RC011-AC003-AUTO: the legacy wrappers stay thin and temporary.
- RC011-AC004-AUTO: package-relative imports work inside `auto/`.
- RC011-AC005-AUTO: the CLI trigger surface stays stable for filesystem actions.
- RC011-AC006-AUTO: refresh and checkpoint regenerate and validate the auto docs.
- RC011-AC007-AUTO: tests cover canonical paths and legacy aliases.
- RC011-AC008-AUTO: naming stays aligned across code, docs, and outputs.

## use
This is the canonical phase-0 auto requirements file.
It mirrors the normal phase naming more closely as `docs/phase-0/auto/phase-0-core-requi-auto.md`.
