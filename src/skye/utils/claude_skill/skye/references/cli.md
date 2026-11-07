# The `skye` command

```text
skye check FILE...            check .skye files; prints file:line:col message and the fix; exit 1 on errors
skye check --schema           print the JSON Schema of the router, flow and prompt blocks
skye check --registry a,b F   also check registry.NAME against the names a,b
skye new KIND [NAME] [--template T | -t T] [-o FILE | --output FILE] [--force]    a starting .skye file you can edit
skye new --list               the kinds (router, flow, prompt) and their templates
skye skill install [--scope user|project] [--dir DIR] [--force]    install this skill for Claude Code
skye skill print [NAME]       print SKILL.md, or references/NAME.md
skye skill path [--scope user|project] [--dir DIR]                 where the skill is installed
skye skill status [--scope user|project] [--dir DIR]               up to date, outdated or edited (exit 1 if it is not up to date)
```

Exit codes: 0 no error, 1 the checked files have errors, 2 usage or file error.

## Templates (`skye new`)

| Kind | Templates (the first is the default) |
|---|---|
| router | `shorthand`, `full` |
| flow | `sequence`, `branch`, `parallel`, `loop`, `full` |
| prompt | `basic`, `chat` |

`skye new` prints to standard output unless you pass `-o`; it refuses to overwrite a file without `--force`.
Every template passes `skye check`, so the first check of a new file is clean and every later error is yours.

## Checking with the registry

A flow names its steps as `registry.NAME`: names that the Python caller passes in a dictionary. Pass them to the checker so a typo is caught:
`skye check --registry planner,web_search flow.skye`. Without `--registry` those names are not checked.

## This skill

`skye skill install` copies this skill to `~/.claude/skills/skye/` (`--scope project` for `./.claude/skills/skye/`, `--dir DIR` for another
skills folder). After upgrading the package, run `skye skill status`: if it says "outdated", `skye skill install` brings the skill up to date
(a skill nobody edited is replaced without `--force`; a file edited by hand is kept unless you pass `--force`).
