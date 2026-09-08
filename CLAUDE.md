# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

This is an empty project scaffold — there is no application code yet. The entire contents are agent-skill configuration:

```
skills-lock.json                                      pins vendored skills to upstream sources
.agents/skills/<name>/                                the actual skill files
.claude/skills/<name> -> ../../.agents/skills/<name>  symlink for Claude Code discovery
```

There is no build system, package manifest, test suite, linter config, or git repository — so there are no build/lint/test commands to run. Don't go searching for them. Anything a task needs here has to be created first, and the choice of stack is still open.

## Skills layout

`.agents/skills/` is the real storage location; `.claude/skills/` holds only symlinks pointing back into it. One copy on disk serves both Claude Code and any other agent tooling that reads `.agents/`. Editing through either path modifies the same file — there is no sync step and no second copy to keep current.

Follow the same pattern for a new skill: create the directory under `.agents/skills/`, then symlink it into `.claude/skills/`. A skill is a directory containing a `SKILL.md` whose YAML frontmatter carries `name` and `description`.

## skills-lock.json

Records per skill: the upstream `source` (`anthropics/skills`), `sourceType` (`github`), the `skillPath` within that repo, and a `computedHash`.

That hash is not a plain digest of the file — `sha256sum .agents/skills/frontend-design/SKILL.md` does not equal the recorded `computedHash`, so it covers some normalized form of the content. Don't use `sha256sum` to test whether a vendored skill has drifted from its pinned version, and don't hand-edit `computedHash` to force a match.

Currently vendored: `frontend-design` (Apache 2.0, full terms in its `LICENSE.txt`) — design guidance for building new UI or reshaping existing UI. It comes from upstream, so prefer re-pulling it over editing it in place; local edits are invisible to the lockfile.
