# wonbin-skills

Agent skills I use day to day, packaged as a Claude Code plugin marketplace.

## Install

```
/plugin marketplace add rst0070/skills
/plugin install wonbin@wonbin-skills
```

To try a local checkout instead, run `/plugin marketplace add ./` from the repo root.
Check the manifests with `claude plugin validate .`.

Installed skills are namespaced by the plugin: `wonbin:tdd`, `/wonbin:grill-me`, and so on.

## Layout

```
.claude-plugin/marketplace.json   # the marketplace: lists the plugins below
plugins/wonbin/
  .claude-plugin/plugin.json
  skills/<name>/SKILL.md          # one directory per skill, auto-discovered
```

To add a skill, drop a directory with a `SKILL.md` into `plugins/wonbin/skills/` and
bump `version` in `plugin.json` so installed copies pick up the change.

## Skills

| Skill             | What it does                                                    | Source                                                                                                          |
| ----------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `codebase-design` | Deep-module vocabulary for interface and seam design            | [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md) |
| `tdd`             | Red → green loop and what makes a test worth keeping            | [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md)             |
| `two-axis-review` | Review a diff against the repo's standards and the spec         | [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md)     |
| `grilling`        | Interview the user round by round to stress-test a plan         | [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)       |
| `grill-me`        | User-invocable entry point (`/wonbin:grill-me`) for `grilling`  | [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md)       |
| `show-me`         | Explain the current topic with diagrams and small HTML views    | [humanlayer/skills](https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md)     |

All vendored skills are MIT licensed; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

### Dependencies between skills

- `tdd` calls `codebase-design` for its module/seam vocabulary. It also points at the
  built-in `code-review` skill, which needs no vendoring.
- `grill-me` only delegates to `grilling`, which holds the instructions.

Both pairs ship in the same plugin, so they cannot be installed apart.

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
