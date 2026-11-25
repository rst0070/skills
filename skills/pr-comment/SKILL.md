---
name: pr-comment
description: Only when the user explicitly asks. Run a two-axis review (Standards + Spec) on a GitHub pull request and post the findings as inline PR review comments with `gh`. Each comment says what the issue is, why it matters, and what to change, with show-me style visuals. Findings that need a human decision @-mention a person, the PR author by default.
disable-model-invocation: true
---

Review a GitHub PR with `two-axis-review` (in Claude Code: `wonbin:two-axis-review`), then post each finding as an inline comment on the PR. One review, one notification.

## Process

### 1. Resolve the PR

The user passes a PR number or URL, and optionally who to mention (see step 4). Without a PR, use the one for the current branch. Fetch what the later steps need:

```bash
gh pr view <pr> --json number,url,author,baseRefName,headRefName,headRefOid
gh repo view --json nameWithOwner
```

Follow the user's rules about which `gh` account to use for the repo's owner.

Local `HEAD` must equal `headRefOid`, or the review reads different code from what the comments land on. If it doesn't match, stop and offer `gh pr checkout <pr>`. Don't switch branches without asking.

Run `git fetch origin <baseRefName>`. The fixed point is `origin/<baseRefName>`.

### 2. Run the two-axis review

Load `two-axis-review` (in Claude Code: `wonbin:two-axis-review`). Follow its steps 1–4 with the fixed point from step 1 and these changes:

- Add this line to **both** sub-agent briefs: "For every finding, give `path:line` using the line number in the new version of the file, plus an end line if it spans a range. If a finding has no single place in the diff (for example a missing requirement), mark it `unanchored`."
- Add this line to **both** briefs too: "Mark a finding `needs-human: <the question>` when the code can't settle it and a person must decide. Examples: an ambiguous or contradictory spec line, a product or domain tradeoff, a deliberate-looking deviation from a standard, or a risk to security, data, or money that needs an owner to accept it. Don't mark findings that only need a code fix."
- Raise each sub-agent's word limit to 600, since the anchors take room.
- Skip its step 5. This skill does its own aggregation.
- If you cannot spawn sub-agents, run the two axes one after another in this session and say in the report that the reviews were not independent.

### 3. Anchor each finding

GitHub only accepts inline comments on lines inside a diff hunk. Check every anchor against `gh pr diff <pr>`:

- The line is an added or context line in a hunk on the new side → inline comment, `side: "RIGHT"`.
- The anchor is close but outside a hunk → move it to the nearest changed line that shows the problem.
- Still no valid line, or the finding is `unanchored` → put it in the review body.

Keep each finding's axis label. Never merge a Standards finding with a Spec finding, even when they share a line: post two comments.

### 4. Write each comment

Load `show-me` (in Claude Code: `wonbin:show-me`) and use its formats (diff, pseudocode, call tree, file tree, Mermaid) **inside the comment body**. GitHub renders all of them. Skip its HTML-file option, since a PR comment can't carry one. Pick the smallest visual that makes the point. A one-line rename needs no visual beyond the suggestion.

Every comment uses this shape:

````markdown
**[Standards]** Possible Feature Envy: `applyDiscount` reads `Order` internals

**What is the issue**
One or two sentences. Quote the rule, smell, or spec line it breaks.
<optional visual: the current shape>

**Why it's an issue**
What happens if nothing changes: the bug, the failure case, or the cost to the next person who edits this code. Be concrete.

**Suggested change**
<visual: the target shape>
````

- Use `**[Standards]**` or `**[Spec]**` as the axis label. Baseline smells keep their "Possible …" wording, because they are judgement calls.
- For **Suggested change**, use a GitHub ` ```suggestion ` block when the fix is an exact replacement of the commented lines. The author can then apply it in one click. Otherwise use a `diff` or another show-me visual of the target shape.
- Keep each comment short: no preamble, and no restating of the diff.

#### Mentioning a person

When a finding is marked `needs-human`, end its comment with one line that names the person and asks the question:

```markdown
**Needs your call** @<login>: <the question, answerable in one reply>
```

- The default is the PR author (`author.login`). If the user named someone else, for everything or for one area (for example "@alice for anything in `billing/`"), use that person instead.
- Mention only on `needs-human` findings. A ping on every comment is noise that trains people to ignore it.
- Under **Suggested change**, give your best option, or the options if there is no clear default. The person decides between them.
- An unanchored `needs-human` finding goes in the review body with the same line.

The review body holds what couldn't be anchored, plus one summary line per axis: the finding count and the worst issue *within* that axis. As in two-axis-review, don't rank across axes.

### 5. Preview, then post

Posting is visible to the PR author and reviewers, and can't be quietly undone. Show the user every comment as `path:line` + body, plus the review body. Before asking to post, list who gets mentioned and on which findings: a mention sends a notification. Then ask before posting. Apply any edits they ask for.

On approval, write the review to a scratch JSON file and post it as one review:

```json
{
  "commit_id": "<headRefOid>",
  "event": "COMMENT",
  "body": "<review body>",
  "comments": [
    { "path": "src/order.ts", "line": 42, "side": "RIGHT", "body": "..." },
    { "path": "src/cart.ts", "start_line": 10, "line": 14, "side": "RIGHT", "start_side": "RIGHT", "body": "..." }
  ]
}
```

```bash
gh api repos/<owner>/<repo>/pulls/<number>/reviews -X POST --input review.json
```

Always use `event: "COMMENT"`, never `APPROVE` or `REQUEST_CHANGES`. Those are the user's call.

If GitHub rejects a comment (usually `line must be part of the diff`), move that finding into the review body and retry. Don't drop it. Finish by printing the review URL from the response.
