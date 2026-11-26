# wonbin-skills

Agent skills I use day to day, packaged as a Claude Code plugin marketplace.

## Install

One repo, one `skills/` folder. Each harness finds it through its own manifest.

| Harness | Install | Status |
| ------- | ------- | ------ |
| Claude Code | `/plugin marketplace add rst0070/skills` then `/plugin install wonbin@wonbin-skills` | *verified* |
| Codex | `codex plugin marketplace add rst0070/skills` (reads `plugin.json`) | *documented, untested* |
| Gemini CLI | `gemini extensions install https://github.com/rst0070/skills` (reads `gemini-extension.json`) | *documented, untested* |
| Copilot CLI | `copilot plugin marketplace add rst0070/skills` then `copilot plugin install wonbin@wonbin-skills` | *documented, untested* |
| Cursor | Add `rst0070/skills` as a plugin from GitHub (reads `plugin.json`) | *documented, untested* |
| npx skills | `npx skills add rst0070/skills` (OpenCode, Amp, Goose, Cline, Kiro, Windsurf and others) | *verified* |

*Verified* means the install was run against this repo. *Documented, untested* means
the line follows the vendor's docs; change it to *verified* once someone installs it.

To try a local checkout instead, run `/plugin marketplace add ./` from the repo root
(or `gemini extensions link .`, `codex plugin marketplace add ./`, `npx skills add . --list`).
Check the manifests with `claude plugin validate .` and `python3 .github/scripts/validate.py`.

Installed skills are namespaced by the plugin in Claude Code: `wonbin:tdd`, `/wonbin:grill-me`, and so on.

### Known limitations

- Copilot CLI ignores `disable-model-invocation: true`
  ([github/copilot-cli#4438](https://github.com/github/copilot-cli/issues/4438)), so it
  may run the manual-only skills (`grill-me`, `pr-comment`, `spec-to-code`,
  `spec-to-code-light`) without being asked. The flag is kept because the other
  harnesses honour it.

## Layout

```
.claude-plugin/
  marketplace.json         # the marketplace: lists the plugin at ./
  plugin.json              # Claude Code manifest: the repo root is the plugin
plugin.json                # Agent Plugins manifest (Codex, Cursor, Copilot CLI)
gemini-extension.json      # Gemini CLI manifest
.github/workflows/validate.yml  # CI: versions match, SKILL.md frontmatter valid
skills/<name>/SKILL.md     # one directory per skill, auto-discovered
```

To add a skill, drop a directory with a `SKILL.md` into `skills/` and bump
`version` in all three manifests so installed copies pick up the change. CI fails
if the three versions differ.

## Skills

| Skill             | What it does                                                    | Source                                                                                                          |
| ----------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `codebase-design` | Deep-module vocabulary for interface and seam design            | [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md) |
| `tdd`             | Red → green loop and what makes a test worth keeping            | [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md)             |
| `two-axis-review` | Review a diff against the repo's standards and the spec         | [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md)     |
| `grilling`        | Interview the user round by round to stress-test a plan         | [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)       |
| `grill-me`        | User-invocable entry point (`/wonbin:grill-me`) for `grilling`  | [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md)       |
| `show-me`         | Explain the current topic with diagrams and small HTML views    | [humanlayer/skills](https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md)     |
| `pr-comment`      | Post a two-axis review as inline PR comments (`/wonbin:pr-comment`) | Local                                                                                                           |
| `spec-discuss`    | Draft the business-logic shape visually, align, then expand it into a task spec | Local                                                                                                           |
| `spec-to-code`    | Implement a ready spec with test-author / developer / reviewer / refuter sub-agents and open a draft PR (`/wonbin:spec-to-code`) | Local |
| `spec-to-code-light` | Implement a ready spec test-first in one session, no sub-agents or review; git checks keep the tests frozen after red (`/wonbin:spec-to-code-light`) | Local |
| `good-code`       | Reference on what good code is, architecturally: dependency direction, seams, contracts, vocabulary, failure, ownership, enforcement. Information only | Local |
| `merge-decision`  | Spec-first brief for a reviewer who will not read the diff: spec vs code as a diagram and table, a MERGE/HOLD suggestion with evidence-tied confidence, at most three calls for the human | Local |

All vendored skills are MIT licensed; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

### Dependencies between skills

- `tdd` calls `codebase-design` for its module/seam vocabulary. It also points at the
  built-in `code-review` skill, which needs no vendoring.
- `grill-me` only delegates to `grilling`, which holds the instructions.
- `pr-comment` runs `two-axis-review` for the findings and uses `show-me` formats in
  each comment body.

- `spec-discuss`, `spec-to-code`, `spec-to-code-light`, `merge-decision` and `good-code` are self-contained: they load no
  other skill, so each can be copied to another plugin on its own.

All of these ship in the same plugin, so they cannot be installed apart.

### Local changes to vendored skills

- `tdd` and `grill-me` call their partner skill by its namespaced name
  (`wonbin:codebase-design`, `wonbin:grilling`). A bare name fails as ambiguous when
  another installed plugin (e.g. `mattpocock-skills`) ships a skill with the same name.
- `two-axis-review` is upstream's `code-review`, renamed so it is never confused with
  Claude Code's built-in `code-review` (which hunts correctness bugs and applies
  cleanups, a different job). The issue-tracker lookup is dropped from the
  spec-source step: it reads a user-supplied path first, then `docs/spec/`,
  `docs/plan/`, `specs/` and `.scratch/`. Upstream's `agents/openai.yaml` (Codex
  packaging) is not vendored.
- `show-me`: only `SKILL.md` is vendored. The one edit is Prettier adding semicolons
  to the embedded TypeScript sample.

These are copies, not a subscription. Re-download from upstream to pick up changes,
or edit them in place to make them our own.

## License

[MIT](LICENSE). Vendored skills keep their original MIT notices in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
