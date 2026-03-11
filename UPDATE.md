# Autoquant update

The goal of an update is to update your internal prompts with the latest knowledge on the autoquant framework by ready git diffs, specifically diff in README.md

README.md serves as the single source of truth of how autoquant works. Diffs in other files/code are just extra details in case they might help. 

The only system/local prompts you can update are: AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, HEARTBEAT.md

Running an autoquant update works like this:

1) run git diff with latest commit to understand deltas. focus on README.md
2) make a list of diffs with impact analysis on your current prompts.
3) make a concrete list of changes to make to your own prompts and knowledge base. 
update user on progress so far and wait for approval before making changes.

4) when ready to make an update, run:
   "$AUTOQUANT_WORKSPACE/venv/autoquant/bin/pip" install --upgrade --force-reinstall "git+https://github.com/dev0xx1/autoquant.git@main#subdirectory=autoquant"

5) Update your prompts as planned in step 3