"""Acceptance tests for issue #9, PR 1: packaging, CI and README.

Run from the repo root: python3 -m pytest .github/scripts
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATE = ROOT / ".github" / "scripts" / "validate.py"

SKILLS = {
    "codebase-design",
    "good-code",
    "grill-me",
    "grilling",
    "merge-decision",
    "pr-comment",
    "show-me",
    "spec-discuss",
    "spec-to-code",
    "spec-to-code-light",
    "tdd",
    "two-axis-review",
}
VERSION = "0.6.0"

red = pytest.mark.xfail(strict=True, raises=AssertionError)


def read_json(rel):
    path = ROOT / rel
    assert path.is_file(), f"{rel} is missing"
    return json.loads(path.read_text())


def run_validate(root):
    if not VALIDATE.is_file():
        return subprocess.CompletedProcess([], 2, "", "validate.py is missing")
    return subprocess.run(
        [sys.executable, str(VALIDATE), str(root)],
        capture_output=True,
        text=True,
    )


@red
def test_ac_1_claude_plugin_validates_with_12_skills():
    manifest = read_json(".claude-plugin/plugin.json")
    assert manifest["name"] == "wonbin"
    assert manifest["version"] == VERSION
    found = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
    assert found == SKILLS
    claude = shutil.which("claude")
    if claude is None:
        pytest.skip("claude CLI not installed")
    result = subprocess.run(
        [claude, "plugin", "validate", str(ROOT)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


@red
def test_ac_2_root_manifests_name_wonbin_and_share_version():
    claude_version = read_json(".claude-plugin/plugin.json")["version"]
    plugin = read_json("plugin.json")
    gemini = read_json("gemini-extension.json")
    assert plugin["$schema"] == (
        "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    )
    assert plugin["name"] == "wonbin"
    assert plugin["license"] == "MIT"
    assert plugin["description"]
    assert "skills" not in plugin
    assert gemini["name"] == "wonbin"
    assert gemini["description"]
    assert plugin["version"] == claude_version
    assert gemini["version"] == claude_version


@red
def test_ac_3_gemini_and_codex_manifests_are_discoverable():
    # Installing in Gemini CLI and Codex needs those CLIs; this checks only the
    # files each one reads. The install itself is a manual step in the PR.
    assert (ROOT / "gemini-extension.json").is_file()
    assert (ROOT / "plugin.json").is_file()
    found = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
    assert found == SKILLS


@red
def test_ac_4_npx_skills_lists_exactly_12_skills():
    npx = shutil.which("npx")
    if npx is None:
        pytest.skip("npx not installed")
    result = subprocess.run(
        [npx, "-y", "skills", "add", str(ROOT), "--list"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    out = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    listed = {
        line.strip("│| ").strip()
        for line in out.splitlines()
        if re.fullmatch(r"[│|]\s{4}[a-z0-9-]+\s*", line)
    }
    assert listed == SKILLS
    # The bundle is versioned with the rest of the release.
    assert read_json("plugin.json")["version"] == VERSION


def copy_repo(tmp_path):
    dest = tmp_path / "repo"
    shutil.copytree(
        ROOT, dest, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache")
    )
    return dest


@red
def test_ac_9_validate_passes_on_repo():
    result = run_validate(ROOT)
    assert result.returncode == 0, result.stdout + result.stderr


@red
def test_ac_9_validate_fails_naming_file_on_version_drift(tmp_path):
    repo = copy_repo(tmp_path)
    gemini = repo / "gemini-extension.json"
    assert gemini.is_file()
    data = json.loads(gemini.read_text())
    data["version"] = "9.9.9"
    gemini.write_text(json.dumps(data))
    result = run_validate(repo)
    assert result.returncode != 0
    assert "gemini-extension.json" in result.stdout + result.stderr


@red
def test_ac_9_validate_fails_naming_file_on_name_mismatch(tmp_path):
    repo = copy_repo(tmp_path)
    bad = repo / "skills" / "bad-skill" / "SKILL.md"
    bad.parent.mkdir()
    bad.write_text("---\nname: other-name\ndescription: Something.\n---\n\nBody.\n")
    result = run_validate(repo)
    assert result.returncode != 0
    assert "skills/bad-skill/SKILL.md" in result.stdout + result.stderr


@red
def test_ac_9_workflow_runs_validate_on_pull_requests():
    workflow = ROOT / ".github" / "workflows" / "validate.yml"
    assert workflow.is_file()
    text = workflow.read_text()
    assert "pull_request" in text
    assert "validate.py" in text


def install_section():
    text = (ROOT / "README.md").read_text()
    match = re.search(r"^## Install\n(.*?)(?=^## )", text, re.S | re.M)
    assert match, "README has no Install section"
    return match.group(1)


@red
def test_ac_10_readme_has_one_labelled_line_per_harness():
    section = install_section()
    harnesses = ["Claude Code", "Codex", "Gemini CLI", "Copilot CLI", "Cursor", "npx skills"]
    for harness in harnesses:
        lines = [l for l in section.splitlines() if l.startswith("|") and harness in l]
        assert len(lines) == 1, f"{harness}: expected 1 row, got {len(lines)}"
        assert "*verified*" in lines[0] or "*documented, untested*" in lines[0], harness


@red
def test_ac_10_readme_notes_copilot_limitation():
    section = install_section()
    assert "Known limitations" in section
    assert "github/copilot-cli#4438" in section
