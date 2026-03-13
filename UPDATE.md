# Autoquant update

The goal is to update your internal prompts with the latest knowledge on the autoquant framework by reviewing the docs diffs.

README.md serves as the single source of truth of how autoquant works. INSTALL.md and UPDATE.md define install/update behavior.

The only system/local prompts you can update are: AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, HEARTBEAT.md

Running an autoquant update works like this:

1) Run:
   autoquant pull-docs
   autoquant get-update-diffs
   Check what changes where made to docs
2) make a list of diffs with impact analysis on your current prompts.
3) make a concrete list of changes to make to your own prompts and knowledge base. 
update user on progress so far and wait for approval before making changes.

4) when ready to make an update, run:
   ```bash
   autoquant run-update
   autoquant --help
   ```
5) Check the commands available and Update your prompts with the latest knowledge and CLI commands as planned in step 3