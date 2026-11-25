"""Check the plugin manifests and every SKILL.md before merge.

Usage: python3 .github/scripts/validate.py [repo-root]

Fails when the manifest versions differ, or when a SKILL.md breaks the
agentskills.io name/description rules. Each error names the file.
skills-ref is not used because it rejects `disable-model-invocation`.
"""

import json
import re
import sys
from pathlib import Path

import yaml

MANIFESTS = [".claude-plugin/plugin.json", "plugin.json", "gemini-extension.json"]
NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def check_manifests(root):
    errors, versions = [], {}
    for rel in MANIFESTS:
        path = root / rel
        if not path.is_file():
            errors.append(f"{rel}: missing")
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{rel}: invalid JSON ({e})")
            continue
        if data.get("name") != "wonbin":
            errors.append(f"{rel}: name is {data.get('name')!r}, expected 'wonbin'")
        versions[rel] = data.get("version")
    if len(set(versions.values())) > 1:
        reference = versions.get(MANIFESTS[0])
        for rel, version in versions.items():
            if version != reference:
                errors.append(
                    f"{rel}: version {version!r} differs from "
                    f"{MANIFESTS[0]} version {reference!r}"
                )
    return errors


def frontmatter(text):
    if not text.startswith("---\n"):
        raise ValueError("no frontmatter")
    end = text.find("\n---", 4)
    if end == -1:
        raise ValueError("frontmatter is not closed")
    data = yaml.safe_load(text[4:end])
    if not isinstance(data, dict):
        raise ValueError("frontmatter is not a mapping")
    return data


def check_skill(root, path):
    rel = path.relative_to(root).as_posix()
    try:
        data = frontmatter(path.read_text())
    except (ValueError, yaml.YAMLError) as e:
        return [f"{rel}: invalid frontmatter ({str(e).splitlines()[0]})"]
    errors = []
    name, folder = data.get("name"), path.parent.name
    if not isinstance(name, str) or not 1 <= len(name) <= 64 or not NAME.fullmatch(name):
        errors.append(f"{rel}: name {name!r} must be 1-64 chars of [a-z0-9-], no leading, trailing or doubled hyphen")
    elif name != folder:
        errors.append(f"{rel}: name {name!r} does not match folder {folder!r}")
    description = data.get("description")
    if not isinstance(description, str) or not 1 <= len(description) <= 1024:
        errors.append(f"{rel}: description must be 1-1024 characters")
    return errors


def main(argv):
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    errors = check_manifests(root)
    skills = sorted((root / "skills").glob("*/SKILL.md"))
    if not skills:
        errors.append("skills/: no SKILL.md found")
    for path in skills:
        errors.extend(check_skill(root, path))
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"ok: {len(MANIFESTS)} manifests, {len(skills)} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
