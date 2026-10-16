---
name: spec-to-code
description: Implement a ready task spec end to end and open a draft PR, using separate sub-agents for tests, implementation, review, and refutation so none of them can grade its own work. The user says where the spec is in plain words ("the spec is docs/specs/foo.md", a Notion link, a pasted block). Use when the user says "implement the spec", "spec to code", "build this from the spec", or hands over a spec and asks for a PR.
disable-model-invocation: true
---

Orchestrate the spec → PR loop. This skill never writes code itself: it briefs sub-agents, checks their output mechanically, and stops when a check fails. The spec is the only input; if the spec cannot answer a question, the loop stops and hands the question back.

## 0. Read the spec and the repo

**Spec.** Read it from wherever the user pointed (file, URL, pasted text). It must have, in some form: intent, acceptance criteria (numbered AC-n), scope with never-touch paths, a PR plan, and a verification plan. If any is missing, or an open `[NEEDS CLARIFICATION]` remains, stop and list what is missing. Do not guess a spec into readiness.

**Repo.** Discover from the repo's own files (CLAUDE.md, CONTRIBUTING, Makefile, package.json, pyproject, CI config) and state in one message before starting:

- test command and the test directory globs
- base branch and branch naming
- commit convention, and the expected-fail marker the test framework uses (`xfail(strict=True)`, `it.fails`, `test.fail()`)
- lint/format command
- how CI status is read (`gh pr checks`)

Create the feature branch from the base branch. Never work on the base branch.

## 1. Per PR-plan slice, run the loop

Work one slice of the spec's PR plan at a time. Each slice gets its own PR.

### 1a. Test author (sub-agent, fresh context)

Brief: the spec's ACs for this slice, the test command, the test directory, the repo's test conventions. Task: one test per AC, named after the AC, asserting the observable behavior through the public interface; expected values from the spec, never recomputed the way the code would. Mark each test with the expected-fail marker. Run the tests and paste the failure output. Commit `test(<scope>): <behavior> [red]`.

Orchestrator check: run the test command yourself. Every new test must fail, and fail for the behavior's reason (assertion), not import or fixture errors. Record the red commit SHA.

### 1b. Developer (sub-agent, fresh context)

Brief: the spec (contract, scope, never-touch), the red tests to make pass, the test command, repo standards. State plainly: "You may not edit, delete, skip, or weaken any test file. You may remove the expected-fail marker only. Tests are the oracle; if a test looks wrong, stop and report it instead of changing it." Task: minimal implementation; remove the markers; commit `<feat|fix>(<scope>): <behavior> [green]`. Report must end with an evidence receipt:

```
command: <exact test command>
exit:    <code>
sha:     <commit>
```

Orchestrator checks, in order, each one a stop on failure:

1. `git diff --stat <red-sha>..HEAD -- <test globs>` touches only marker lines. Anything else: revert the test changes, re-run, and if still red, stop and report "developer modified tests".
2. Diff file list ⊆ spec scope; nothing under never-touch; within change budget.
3. Run the test command yourself. The receipt's claim is not evidence; your run is.
4. Run lint/format.

### 1c. Reviewer (sub-agent, fresh context, read-only tools)

Brief: the diff against the base branch, the spec, the repo's standards files. Nothing from the developer's transcript. Task: report only (a) AC that is missing, partial, or implemented wrong, with the AC number; (b) correctness bugs with `path:line`; (c) changes the spec did not ask for. No style notes; no "consider". Under 400 words. A reviewer told to find gaps will find some: tell it that "no findings" is an acceptable answer.

### 1d. Refuter (sub-agent, fresh context)

Brief: the diff, the spec, and the reviewer's findings. Task: for each finding, try to show it is wrong or already handled, citing `path:line`. Output per finding: `STANDS` or `REFUTED: <reason>`. Only `STANDS` findings continue.

### 1e. One fix cycle

Send `STANDS` findings to a fresh developer sub-agent with the same rules as 1b. Repeat checks 1–4. If findings remain after this cycle, stop and hand back: the spec, not the code, is probably what needs to change.

### 1f. Open the draft PR

Push the branch and open a **draft** PR against the base branch. Body:

```markdown
## Intent
<spec intent, one paragraph>

## Acceptance criteria
| AC | Test | Status |
| AC-1 | tests/.../test_x.py::test_ac_1 | pass |

## Evidence
- tests: `<command>` exit 0 at <sha>, CI: <check name>
- lint: `<command>` exit 0 at <sha>

## Not verified
<what no test or run covered; "None" is a claim, blank is not allowed>

## Decisions made without the author
<judgement calls the sub-agents made where the spec was silent>

## Out-of-scope changes
<files touched outside spec scope; should be "None">

## Review
<findings that STOOD and how each was fixed: "fixed in <sha>" / "kept because <reason>">
```

Print the PR URL. Then continue with the next slice, branching from this slice's branch if the plan says the slices stack, otherwise from the base branch.

## Stop conditions

Stop and report rather than improvise when:

- the spec is not ready (section 0)
- a test fails for the wrong reason, or a test never went red
- the developer touched tests, scope, or never-touch paths
- the same finding survives two fix attempts
- any command the receipt claims passed fails when you run it

## Never

- edit a test after the red commit, in any sub-agent or yourself
- merge, approve, or push to the base branch
- treat a sub-agent's "tests pass" as evidence; run the command
