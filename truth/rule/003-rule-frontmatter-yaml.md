'''yaml
title: 003-rule-frontmatter-yaml
purpose: Define the frontmatter YAML convention for markdown files.
version: V00.01.00
'''

# 003-rule-frontmatter-yaml

This file defines the frontmatter format used in markdown documents.

## Frontmatter pattern

'''yaml
title: <document-title>
purpose: <short-purpose>
version: VAA.BB.CC
'''

## Rules

- Frontmatter must appear at the top of the file.
- Frontmatter must be YAML.
- Frontmatter must be enclosed by `'''yaml` start and end markers.
- Required keys are `title`, `purpose`, and `version`.
- Values should be clear and concise.

## Version history

- V00.01.00 — Initial draft.
- V00.01.01 — Updated frontmatter marker rule to use apo yaml delimiters.
