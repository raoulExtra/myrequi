# Plan 6: Add test organization

1. Inspect the target project's existing pytest configuration and markers.
2. Define or preserve markers appropriate to the project, such as `unit`, `sit`, and `uat`.
3. Define component metadata for the project's actual core and extension boundaries without changing behavior.
4. Test phase- and component-specific selection.
5. Move files only after path assumptions are tested; commit organization separately.

Do not assume a particular extension name, directory layout, or marker set.
