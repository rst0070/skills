---
name: merge-decision
description: 'Produce the handoff card a maintainer reads instead of the diff before merging a PR: a risk banner from the paths touched, the few items only a human can decide, evidence checked against CI rather than the PR''s claims, and an explicit "not verified" list. Use when the user asks "what do I need to watch", "is this safe to merge", "merge decision for PR N", or hands over a PR they will not read line by line.'
---

Build the card that replaces reading the code. It is written for someone who will decide in a few minutes, so it leads with what they must judge and ends with what nobody checked. It never says "merge"; the decision stays with the human.

## Inputs

A PR number or URL (default: the current branch's PR). A spec, if the user names one or the PR body links one; otherwise work from the PR's stated intent and say so in the card.

```bash
gh pr view <pr> --json number,url,title,body,author,baseRefName,headRefName,headRefOid,additions,deletions,files
gh pr checks <pr>
gh pr diff <pr>
```

## 1. Risk tier from paths, never from size

Classify by what the diff touches. The highest matching tier wins. Line count never changes the tier.

| Tier | Paths or content |
|---|---|
| HIGH | schema or data migrations; auth, permissions, tenant or organization scoping; billing, credits, payments; deletes or bulk updates; secrets, CI, deploy config; external calls that write |
| MEDIUM | public API shapes (serializers, routes, response fields); background tasks; caches; anything with a feature flag |
| LOW | everything else |

The user can add repo-specific patterns in the request ("treat `whizchat/hooks/backends/` as HIGH"). State which files set the tier.

## 2. Verify evidence, do not read claims

For every claim in the PR body ("tests pass", "lint clean", "verified on dev"), find its backing:

- a CI check in `gh pr checks` that is green at `headRefOid`, or
- a command you re-run yourself now, or
- an attached artifact (recording, log) you can open.

Mark each claim `VERIFIED (<check or command>)` or `UNBACKED`. A ticked checkbox or a sentence is not evidence. If the PR body has no claims at all, run the repo's test and lint commands yourself and record the result.

## 3. Audit acceptance criteria (sub-agent, fresh context, read-only)

Brief: the spec's ACs (or the PR's intent, if no spec), the diff, the test files in the diff. Task: for each AC, `PASS` / `FAIL` / `UNCERTAIN` with the test name and `path:line` that shows it, one line of reason. Also list behavior in the diff that no AC asked for. Under 400 words.

## 4. Check drift and tests

Mechanical, by you:

- files touched outside the spec's scope or inside its never-touch paths
- tests deleted, skipped, or with weakened assertions (`git diff <base>...HEAD -- <test globs>`, look for removed asserts, added skips, widened expectations)
- new suppression comments (`noqa`, `type: ignore`, `nosec`, `eslint-disable`, `IgnoreMigration`)

## 5. Write the card

````markdown
# Merge decision — PR #<n> <title>

**Risk: HIGH | MEDIUM | LOW** — set by <files>

## Decide (you)
≤5 items. Only what code cannot settle: AC marked FAIL/UNCERTAIN, product-intent
ambiguities, migration locking / rollback, data-loss paths, UNBACKED claims that matter.
Each item: what it is, where (path:line), and the question to answer.

## Decisions made without you
Judgement calls visible in the diff or PR body where the spec was silent.

## Verified
One line each: claim · how it was checked · result · sha.

## Findings and disposition
From the AC audit and drift check: "fixed in <sha>" / "kept because <ref>" / "open".

## Not verified
Mandatory. What no test, check, or run covered. "None" is allowed; blank is not.

## Out-of-scope changes
Files outside scope or never-touch. Should be "None".

## Rollout
Revert profile (one commit? data migration?), feature flag if any, what to watch after merge and for how long.

## Before you merge, answer this
One question about the invariant this change touches, e.g. "What breaks if <X> is no longer written only by <Y>?"
If you cannot answer it from the card, ask the agent "why" until you can.
````

Print the card. Offer, once, to post it as a PR comment; post only on a yes, with `gh pr comment`, never as a review event.

## Rules

- **Never approve, request changes, or merge.** The card informs; the human decides.
- **Unbacked beats pleasant.** A green CI link outranks any sentence in the PR body; a missing link is reported as UNBACKED, not assumed.
- **Blank "Not verified" is a failed card.** If you are unsure what was not verified, that is the content.
- **Size is not safety.** A three-line migration is HIGH; a 900-line refactor behind a flag with green mutation tests may be LOW.
