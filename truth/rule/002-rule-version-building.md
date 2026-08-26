'''yaml
title: 002-rule-version-building
purpose: Define the version building convention for markdown files.
version: V00.02.00
'''

# 002-rule-version-building

This file defines the version building convention used by rule documents.

## Version pattern

`VAA.BB.CC`

### Parts

- `V` marks the value as a version.
- `AA` is the major version.
- `BB` is the minor version.
- `CC` is the patch version.

### Rules

- Each part must be zero-padded to two digits.
- Version numbers must increase in a clear sequence.
- A structural or meaning change increases the major part.
- A content refinement increases the minor part.
- A small correction increases the patch part.

### Example

- `V00.01.00`
- `V00.02.00`
- `V01.00.00`

## Version history

- V00.02.00 — Initial draft of the version building rule.
