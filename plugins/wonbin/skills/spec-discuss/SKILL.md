---
name: spec-discuss
description: Turn a feature idea, bug, or change request into a task spec through a short interview. The spec is a markdown file a human can review in minutes and an agent can implement without asking. Use when the user wants to "write a spec", "discuss the spec", "shape this before coding", or hands over a half-formed idea.
---

Interview the user, then write one markdown spec with a fixed shape. The human owns the acceptance criteria; the agent proposes, the human approves. The spec is done when its ready checklist passes, not when it is long.

## Output

A markdown file. Default location is `docs/specs/<slug>.md` in the current repo; the user can name any other path or say "Notion" (then write the file first and paste it there). Say where you wrote it.

The file has this shape. Keep every section; write `None` rather than deleting one.

````markdown
---
status: draft | ready
owner: <person who approves the AC>
---

# <title>

## Intent
Three lines at most: who needs this, why now, what changes for them.

## Contract
Typed inputs and outputs, API or model shapes, error vocabulary, and invariants
("X is written only by Y", "Z is idempotent"). What the result MEANS, not how it is built.

## Acceptance criteria
AC-1  Given <state>, when <action>, then <observable result>.
AC-2  ...
One behavior per line. Each AC becomes one named test.

## Scope
In: <modules, endpoints, files allowed to change>
Out of scope: <explicit non-goals, including tempting adjacent fixes>
Never touch: <paths an implementer must not edit, e.g. migrations/, auth/, tests of other modules>
Change budget: <max files / max lines, or "none">

## Open questions
- [NEEDS CLARIFICATION] <question>
(Empty when ready.)

## PR plan
PR 1: <vertical slice, which ACs, ≤ ~400 lines>
PR 2: ...
Migrations and schema changes get their own PR.

## Verification plan
How the implementer proves each AC (test command), and how a QA pass exercises it as a user (environment, steps).

## Decisions
- <decision> because <reason>  (keeps the "why" for the next reader)
````

## Process

### 1. Find the facts before asking

Facts are your job; decisions are the user's. Before the first question, dispatch a sub-agent to read the code the idea touches: current behavior, existing seams, tests, and any earlier spec or doc. Never ask the user something you could look up.

### 2. Interview in rounds

Ask only the questions whose prerequisites are settled, all of them in one round, numbered, each with your recommended answer:

```
❓ Q1 — <title>: <question, with options if there are natural ones>
➡️ <your recommendation>
```

Wait for answers, then recompute the next round. A question that depends on an open one belongs to a later round. Stop when nothing is left silently assumed. Typical rounds:

1. Intent and the one behavior that matters most.
2. Contract: shapes, errors, invariants. Show the shape, do not describe it (see step 3).
3. Scope edges: what is tempting but out, what must never be touched.
4. Slicing: what the first PR proves on its own.

### 3. Show, don't narrate

When a question is about shape or flow, put a small visual in the question: a `diff` of the target interface, a Mermaid sequence of the call path, a file tree of what changes, or pseudocode of the rule. The user decides faster from a picture than from a paragraph. Keep each visual to what the question needs.

### 4. Draft, then confirm the AC one by one

Write the file with `status: draft`. Then list the ACs and ask the user to accept, edit, or drop each. An AC the user did not accept does not stay in the file. Record every "because" in **Decisions**.

### 5. Ready check

Flip `status: ready` only when all of these hold. Report the list with ✓/✗; a ✗ keeps the spec in draft and names what is missing.

- Open questions is empty: no `[NEEDS CLARIFICATION]` anywhere in the file.
- Every AC is one observable behavior with a Given/When/Then, numbered, and accepted by the user.
- Scope has a non-empty **Never touch** line and an explicit **Out of scope** line.
- PR plan has at least one slice, and each slice names its ACs.
- Verification plan names a runnable command.
- Contract contains no implementation steps (no "then call", "loop over", library names unless they are the product).

## Rules

- **Short beats complete.** Three to seven ACs is normal. If the list passes ten, the task is two specs.
- **No "how" in the spec.** The implementer chooses the mechanism; the spec fixes meaning, boundaries, and proof.
- **Write the uncertainty down, never fill it.** A gap you are tempted to guess becomes a `[NEEDS CLARIFICATION]` line.
- **The spec is the handoff.** Anything the implementer would need to ask you belongs in the file, not in the chat.
