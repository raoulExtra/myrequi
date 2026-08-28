'''yaml
title: 004-rule-number-uneed-dir
purpose: Define the naming convention for numbered uneed directories.
version: V00.01.00
'''

# 004-rule-number-uneed-dir

This file defines the directory naming convention for `uneed` folders.

## Naming pattern

`NNN-uneed`

## Rules

- `NNN` is a zero-padded number.
- `uneed` is the directory category.
- The number must identify the directory in sequence.
- The directory name should be lowercase and hyphen-separated if needed.
- The directory name must match the intended uneed group.
- When a user directory is created, create an `info.yaml` file inside it.
- `info.yaml` must start with `uneed_cnt: 0`.
- `info.yaml` must start with `uemail: undefined`.
- `info.yaml` must start with `uemail_confirm: false`.

## Version history

- V00.01.00 — Initial draft.
- V00.01.01 — Added user directory bootstrap values for `info.yaml`.
