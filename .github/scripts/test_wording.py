"""Acceptance tests for issue #9, PR 2: portable skill wording.

Run from the repo root: python3 -m pytest .github/scripts
"""

import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"
MANUAL_ONLY = ["grill-me", "pr-comment", "spec-to-code", "spec-to-code-light"]
EXPLICIT_SENTENCE = "Only when the user explicitly asks."
REVIEW_STYLE = [
    "skills/two-axis-review/SKILL.md",
    "skills/pr-comment/SKILL.md",
    "skills/merge-decision/SKILL.md",
    "skills/codebase-design/DESIGN-IT-TWICE.md",
]
# (file, skill it loads) pairs the spec names.
CROSS_REFS = [
    ("grill-me", "grilling"),
    ("pr-comment", "two-axis-review"),
    ("pr-comment", "show-me"),
    ("tdd", "codebase-design"),
]



def skill_text(name):
    return (SKILLS / name / "SKILL.md").read_text()


def frontmatter(name):
    text = skill_text(name)
    end = text.find("\n---", 4)
    return yaml.safe_load(text[4:end])


def test_ac_5_no_skill_mentions_the_skill_tool():
    hits = [
        p.relative_to(ROOT).as_posix()
        for p in SKILLS.glob("*/SKILL.md")
        if "Skill tool" in p.read_text()
    ]
    assert hits == []


def test_ac_5_cross_skill_references_use_bare_name_with_hint():
    for skill, target in CROSS_REFS:
        hint = f"`{target}` (in Claude Code: `wonbin:{target}`)"
        assert hint in skill_text(skill), f"{skill} -> {target}"
    for path in SKILLS.glob("*/SKILL.md"):
        text = path.read_text()
        for match in re.finditer(r"wonbin:([a-z0-9-]+)", text):
            target = match.group(1)
            start = text.rfind("`" + target + "` (in Claude Code: `", 0, match.start())
            assert start != -1 and match.start() - start < 40 + len(target), (
                f"{path.relative_to(ROOT)}: bare `wonbin:{target}` without the bare-name form"
            )


@pytest.mark.parametrize("name", MANUAL_ONLY)
def test_ac_6_manual_only_skill_is_not_implicit(name):
    meta = frontmatter(name)
    assert meta.get("disable-model-invocation") is True
    assert meta["description"].startswith(EXPLICIT_SENTENCE + " ")
    openai = SKILLS / name / "agents" / "openai.yaml"
    assert openai.is_file(), f"{openai.relative_to(ROOT)} is missing"
    policy = yaml.safe_load(openai.read_text()).get("policy", {})
    assert policy.get("allow_implicit_invocation") is False


def test_ac_7_spec_to_code_stops_without_sub_agents_before_step_1():
    text = skill_text("spec-to-code")
    guard = re.search(r"If you cannot spawn sub-agents, stop[^\n]*spec-to-code-light", text)
    assert guard, "no stop-and-suggest-spec-to-code-light guard"
    step_1 = text.index("\n## 1.")
    assert guard.start() < step_1


@pytest.mark.parametrize("rel", REVIEW_STYLE)
def test_ac_7_review_style_skill_has_sequential_fallback(rel):
    text = (ROOT / rel).read_text()
    assert re.search(
        r"If you cannot spawn sub-agents, run [^\n]* one after another in this session"
        r"[^\n]*not independent",
        text,
    ), rel


@pytest.mark.parametrize("name", ["spec-to-code", "spec-to-code-light"])
def test_ac_8_repo_discovery_reads_agents_md_before_claude_md(name):
    assert "(AGENTS.md, CLAUDE.md, CONTRIBUTING" in skill_text(name)


def test_every_manifest_is_at_0_7_0():
    for rel in [".claude-plugin/plugin.json", "plugin.json", "gemini-extension.json"]:
        assert json.loads((ROOT / rel).read_text())["version"] == "0.7.0", rel
