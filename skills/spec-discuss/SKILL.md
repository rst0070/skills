---
name: spec-discuss
description: Turn a feature idea, bug, or change request into a task spec by drafting the business-logic shape visually, aligning on it with the user, then expanding the agreed shape into a markdown spec a human can review in minutes and an agent can implement without asking. Use when the user wants to "write a spec", "discuss the spec", "shape this before coding", or hands over a half-formed idea.
---

The agent drafts, the user corrects. Do not interview the user to collect a spec; propose a concrete shape, mark what you assumed, and let the user point at what is wrong. Correcting a wrong draft is cheaper than answering an open question.

The conversation runs at two altitudes, and the order is fixed: agree on the **shape** first, then expand it into the **spec**. Nothing below the shape is discussed until the shape is agreed.

## The altitude rule

A detail belongs in the shape if changing it would change what a caller or user can observe, what crosses a boundary between modules, or who owns a piece of state. Everything else is implementation and the implementer decides it. Below the line: library names, loop structure, internal function names, ordering no caller can see, how a value is computed when only the result is observable.

Apply this to every line you write and every point you raise. If a question is below the line, do not ask it; the spec leaves it to the implementer.

Use whatever vocabulary the code already has for its boundaries and owners. Do not impose a vocabulary the code does not have.

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

## Shape
The agreed picture from the align step, pasted as agreed: the flow, the target-shape
diffs, and the numbered behavior list (B-1, B-2, ...). This is what the user said yes to.

## Contract
Typed inputs and outputs, API or model shapes, error vocabulary, and invariants
("X is written only by Y", "Z is idempotent"). What the result MEANS, not how it is built.

## Acceptance criteria
AC-1 (B-1)  Given <state>, when <action>, then <observable result>.
AC-2 (B-1)  ...
One behavior per line. Each AC names the shape behavior it comes from. Each AC becomes one named test.

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

### 1. Find the facts

Facts are your job; decisions are the user's. Before drafting, dispatch a sub-agent to read the code the idea touches: the current flow, the module boundaries it crosses, who writes the state involved, existing tests, and any earlier spec or doc. Never ask the user something you could look up.

### 2. Draft the shape

One message, mostly pictures, little prose. Pick the smallest views that show the business-logic level of the change, in the show-me style:

- **Flow**: a Mermaid sequence diagram or flowchart of the path the change takes. Participants are modules and boundaries, not functions. Mark what is new or changed.
- **Target shape**: `diff` blocks of what changes, where the surrounding shape already exists. An interface diff, a file-tree diff, a call-tree diff. Shapes, not bodies.
- **Ownership**, only when the change touches shared state: one line per state saying who writes it after the change.
- **Behaviors**: a numbered list, `B-1`, `B-2`, ..., one line each, of every observable behavior the picture implies. This list is what the user agrees to; the ACs are derived from it later.

Then three short lists:

- **Decide (you)**: the forks only the user can settle, at most five. When a fork would produce two materially different shapes, draw both side by side and ask the user to point, instead of describing the options.
- **Assumed**: every choice you made where the user was silent, one line each, so the user can override by pointing.
- **Looked up**: the facts from the code the draft rests on, so a wrong fact can be caught.

When the user's input is thin, still draft. A heavily marked **Assumed** list beats a round of questions.

Keep Mermaid text plain so it parses: no `;` in labels or messages, wrap any flowchart label containing `( ) [ ] { } < > # :` in double quotes, never name a node `end`.

### 3. Align

The user reacts to the picture. Redraw only what changed; do not resend the whole draft for a one-line correction. Keep **Assumed** current: a choice the user confirmed moves out of it, a new choice moves in. The step is done when the user says the shape is right. Do not write the Contract or ACs before then.

### 4. Expand into the spec

Derive every section from the agreed shape and write the file with `status: draft`:

- **Shape** is the agreed picture and behavior list, pasted as agreed.
- **Contract** is the target-shape diffs made precise: types, error vocabulary, invariants. Nothing in it that was not in the shape or implied by it.
- **Acceptance criteria**: one or more per behavior, each naming its `B-n`. An AC that no behavior supports does not go in; either a behavior was missing from the shape (go back to step 3) or the AC is below the line.
- **Scope**: In comes from the files the shape changes. Out of scope and Never touch come from the adjacent things the facts step found and the shape deliberately left alone.
- **PR plan**, **Verification plan**, **Decisions**: as before. Every confirmed **Assumed** line becomes a Decision with its "because".

### 5. Hand off for review

The user reviews the spec by skimming, so the handoff message is what they read instead of the file. Lead with what the expansion decided, then prove nothing drifted:

````markdown
Spec written: <path> (status: draft)

## Decide (you)
≤5 items the shape did not settle and the code cannot: an AC you are unsure of,
a scope edge, a never-touch path that might be too wide or too narrow.

## Decided without you
Choices made while expanding: why a path is in Never touch, a change budget,
an error name, a PR split. One line each with its "because".

## Shape → AC
| B | AC |
|---|----|
| B-1 | AC-1, AC-2 |
Orphans listed below the table: a behavior with no AC, an AC with no behavior. Should be none.

## Not confirmed in code
Facts the spec rests on that the facts step could not verify. "None" is a claim; blank is not allowed.

## Ready check
<the list from step 6 with ✓/✗>
````

### 6. Ready check

Flip `status: ready` only when all of these hold. A ✗ keeps the spec in draft and names what is missing.

- Shape section is present and matches what the user agreed to.
- Every AC is one observable behavior with a Given/When/Then, numbered, and names a `B-n` from the Shape.
- Every `B-n` in the Shape has at least one AC.
- Open questions is empty: no `[NEEDS CLARIFICATION]` anywhere in the file.
- Scope has a non-empty **Never touch** line and an explicit **Out of scope** line.
- PR plan has at least one slice, and each slice names its ACs.
- Verification plan names a runnable command.
- Contract contains no implementation steps (no "then call", "loop over", library names unless they are the product).

## Rules

- **Draft, do not interview.** A question is allowed only when two shapes are both plausible; then show both.
- **Shape before spec.** No Contract, AC, or scope talk until the user has said the shape is right.
- **Nothing below the line.** The implementer chooses the mechanism; the spec fixes meaning, boundaries, and proof.
- **Short beats complete.** Three to seven ACs is normal. If the list passes ten, the task is two specs.
- **Write the uncertainty down, never fill it.** A gap you are tempted to guess becomes an **Assumed** line while drafting, and a `[NEEDS CLARIFICATION]` line if it survives into the spec.
- **The spec is the handoff.** Anything the implementer would need to ask you belongs in the file, not in the chat.
