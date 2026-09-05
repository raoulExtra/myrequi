# Auto prompt core requirements

## core requirements
- [code] RC012-AUTO: provide a lightweight prompt helper for automation questions.
- [code] RC013-AUTO: support one-line questions without options.
- [code] RC014-AUTO: support questions with numbered options.
- [code] RC015-AUTO: support an optional note and default answer.
- [code] RC016-AUTO: stay non-interactive-safe when stdin is not a TTY.
- [code] RC017-AUTO: expose the prompt helper through the CLI trigger surface.

## acceptance criteria
### RC012-AUTO
- RC012-AC001-AUTO: the helper lives under `auto/` and is importable as a package module.
- RC012-AC002-AUTO: the helper does not depend on external libraries beyond the standard library.

### RC013-AUTO
- RC013-AC001-AUTO: a one-line question can be asked without options or defaults.
- RC013-AC002-AUTO: the answer is returned as a plain string.

### RC014-AUTO
- RC014-AC001-AUTO: options are displayed as numbered choices.
- RC014-AC002-AUTO: entering the option number returns the option text.

### RC015-AUTO
- RC015-AC001-AUTO: a note is printed before the prompt when provided.
- RC015-AC002-AUTO: an empty input returns the default when one is set.

### RC016-AUTO
- RC016-AC001-AUTO: non-interactive mode reads `SELF_LEARN_ANSWER` from the environment.
- RC016-AC002-AUTO: non-interactive mode falls back to the default when no env var is set.

### RC017-AUTO
- RC017-AC001-AUTO: the CLI exposes an `ask` subcommand with `--options`, `--note`, and `--default`.
- RC017-AC002-AUTO: the CLI returns the answer as JSON.

## use
This file defines the requirements for the auto prompt helper.
It keeps the interactive automation surface small and testable.
