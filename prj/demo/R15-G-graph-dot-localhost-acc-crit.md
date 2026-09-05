'''yaml
title: R15-G-graph-dot-localhost-acc-crit
requirement_id: R15-G
source_requirement: R15-G-graph-dot-localhost.md
'''

# Acceptance criteria for R15-G

## Requirement
- [R15-G requirement](R15-G-graph-dot-localhost.md)

## Verification ideas
- The graph-localhost provider accepts a `-dot <dotfile>` option.
- The provider converts the DOT file to PNG using Graphviz.
- The provider serves the PNG on localhost.
- Opening the local root URL shows the rendered PNG in a browser.
- A reviewer can confirm the PNG is produced from the DOT file.
