- if context unclear pick automatic most probable answer. You use pi inside IDE Zed.
- we use python3 in WSL ubuntu on windows
- The project uses SQLite databases. 
- The main one is continuity.db on the workspace root
- add. access to db via prj/continuity_db/imple/V00.00.01/core/continuity_db_helper.py
- use this py via recall argument as user chat support on all unclear.
 1. Always start with LIMIT 10 + a filter (status, name pattern) to preview
 2. Only if the preview looks relevant, then expand the query
 3. Prefer using memory_command.py recall API over raw SQL when 
 4. if user choices: use numbers for your choices
- dont read the memory.md
- if in plans folder you see <number>-plan.md files work on those and
move completed work plans to the done folder.
