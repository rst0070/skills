"""Acceptance tests for issue #12: merge-decision as a spec-first brief.

Run from the repo root: python3 -m pytest .github/scripts
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "merge-decision" / "SKILL.md"


def text():
    return SKILL.read_text()


def frontmatter():
    body = text()
    end = body.find("\n---", 4)
    return yaml.safe_load(body[4:end])


def card():
    """The card template: the ````markdown block under the card step."""
    match = re.search(r"````markdown\n(.*?)\n````", text(), re.S)
    assert match, "no ````markdown card template"
    return match.group(1)


def section(heading):
    """Body of a `## heading` section in the skill (not the card)."""
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text(), re.S | re.M)
    assert match, f"no '## {heading}' section"
    return match.group(1)


# Shape: the steps run in the order the issue's flowchart draws.


def test_steps_follow_the_issue_flow():
    steps = [
        "Find the spec",
        "Extract expected behaviors",
        "Spec vs code",
        "Mechanical checks",
        "Suggest",
        "Write the card",
    ]
    positions = []
    for step in steps:
        match = re.search(rf"^## \d+\. {re.escape(step)}", text(), re.M)
        assert match, f"no numbered step '{step}'"
        positions.append(match.start())
    assert positions == sorted(positions)


def test_spec_is_searched_in_pr_body_linked_issue_and_docs():
    body = section_starting("Find the spec")
    assert "PR body" in body
    assert "closingIssuesReferences" in body
    assert "docs/" in body


def test_no_spec_asks_instead_of_inferring():
    body = section_starting("Find the spec")
    assert "PR body is the spec" in body
    assert "stated intent" not in text()
    assert re.search(r"[Dd]o not infer", body)


def test_expected_behaviors_keep_spec_ids_else_e_numbers():
    body = section_starting("Extract expected behaviors")
    assert "own IDs" in body
    assert "E-1" in body


def test_spec_vs_code_runs_in_a_fresh_sub_agent_with_fallback():
    body = section_starting("Spec vs code")
    assert "fresh context" in body
    assert re.search(
        r"If you cannot spawn sub-agents, run [^\n]* one after another in this session"
        r"[^\n]*not independent",
        body,
    )


def test_mechanical_checks_cover_risk_ci_drift_and_weakened_tests():
    body = section_starting("Mechanical checks")
    for term in ["Risk tier", "headRefOid", "Drift", "weakened"]:
        assert term in body, term


# Card: suggestion first, spec vs code first in the body, audit folded.


def test_card_leads_with_suggestion_confidence_and_risk_in_one_line():
    lines = [l for l in card().splitlines() if l.strip()]
    assert lines[0].startswith("# PR #")
    assert "Spec:" in lines[0]
    assert re.fullmatch(
        r"\*\*Suggest: MERGE \| HOLD\*\* · confidence HIGH\|MED\|LOW · risk HIGH\|MED\|LOW .*",
        lines[1],
    ), lines[1]


def test_card_body_order_is_spec_vs_code_then_needs_you_then_details():
    c = card()
    spec = c.index("## Spec vs code")
    needs = c.index("## Needs you")
    details = c.index("<details>")
    assert spec < needs < details
    assert "```mermaid" in c[spec:needs]
    assert "| # | Expected (from spec) | Status | Evidence |" in c[spec:needs]


def test_needs_you_has_at_most_three_items_each_with_suggestion_and_alternative():
    c = card()
    assert "## Needs you (≤3, \"None\" allowed)" in c
    needs = c[c.index("## Needs you") : c.index("<details>")]
    assert "→ **Suggest:" in needs
    assert "alt:" in needs
    assert "?" not in needs.split("\n", 1)[1], "items must suggest, not ask"


def test_audit_sections_are_folded_into_details():
    c = card()
    folded = c[c.index("<details>") : c.index("</details>")]
    for label in ["**Verified**", "**Not verified**", "**Drift**", "**Rollout**"]:
        assert label in folded, label
    assert c.count("\n## ") + c.startswith("## ") == 2, "only two ## sections above the fold"


def test_removed_sections_are_gone():
    t = text()
    assert "Before you merge" not in t
    assert "Decide (you)" not in t
    assert "Decisions made without you" not in t


def test_diagram_legend_marks_deviations_added_and_missing():
    body = section_starting("Write the card")
    for cls in ["classDef deviates", "classDef added", "classDef missing"]:
        assert cls in body, cls
    assert "stroke-dasharray" in body


# Confidence and suggestion.


def test_confidence_levels_are_tied_to_evidence():
    body = section_starting("Suggest")
    assert re.search(r"\*\*HIGH\*\*[^\n]*green[^\n]*cite", body)
    assert re.search(r"\*\*MED\*\*[^\n]*reading the code", body)
    assert re.search(r"\*\*LOW\*\*[^\n]*raise", body)
    assert "lowest" in body


def test_suggest_hold_conditions_are_listed():
    body = section_starting("Suggest")
    assert "HOLD" in body and "MERGE" in body


# Rules and format.


def test_rules_from_the_issue():
    rules = section("Rules")
    assert re.search(r"Suggest, never act", rules)
    for event in ["approve", "request changes", "merge"]:
        assert event in rules, event
    assert "HIGH needs a citation" in rules
    assert "should be split" in rules
    assert re.search(r"blank \"Not verified\" is a failed card", rules, re.I)
    assert "Size is not safety" in rules


def test_default_format_is_mermaid_and_markdown_posted_only_on_yes():
    body = section_starting("Write the card")
    assert "gh pr comment" in body
    assert "another format" in body
    assert "review event" in body


def test_skill_stays_general_and_self_contained():
    t = text()
    assert "spec-discuss" not in t
    assert "wonbin:" not in t


def test_description_names_spec_first_suggestion():
    description = frontmatter()["description"]
    assert len(description) <= 1024
    for term in ["spec", "MERGE or HOLD", "confidence"]:
        assert term in description, term


def section_starting(title):
    """Heading and body of the numbered step whose title starts with `title`.

    Ends at the next numbered step or `## Rules`, so `##` headings inside the
    card template stay in the step.
    """
    match = re.search(
        rf"^(## \d+\. {re.escape(title)}.*?)(?=^## (?:\d+\.|Rules)|\Z)",
        text(),
        re.S | re.M,
    )
    assert match, f"no step starting '{title}'"
    return match.group(1)
