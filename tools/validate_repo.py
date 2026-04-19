#!/usr/bin/env python3
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "leetcode-practice"
SKILL_MD = SKILL_DIR / "SKILL.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
SCRIPT_FILE = SKILL_DIR / "scripts" / "leetcode_cn.py"
IGNORED_TOP_LEVEL_DIRS = {".git", ".venv", "venv"}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def validate_frontmatter() -> None:
    if not SKILL_MD.exists():
        fail(f"Missing file: {SKILL_MD}")

    text = SKILL_MD.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        fail("SKILL.md is missing a valid YAML front matter block.")

    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        fail(f"SKILL.md front matter is not valid YAML: {exc}")

    if not isinstance(data, dict):
        fail("SKILL.md front matter must be a YAML mapping.")

    for key in ("name", "description"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            fail(f"SKILL.md front matter requires a non-empty string for '{key}'.")

    body = text[match.end() :].strip()
    if not body:
        fail("SKILL.md must contain a markdown body after the front matter.")


def validate_openai_yaml() -> None:
    if not OPENAI_YAML.exists():
        fail(f"Missing file: {OPENAI_YAML}")

    try:
        data = yaml.safe_load(OPENAI_YAML.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        fail(f"agents/openai.yaml is not valid YAML: {exc}")

    if not isinstance(data, dict):
        fail("agents/openai.yaml must be a YAML mapping.")

    interface = data.get("interface")
    if not isinstance(interface, dict):
        fail("agents/openai.yaml must define an 'interface' mapping.")

    for key in ("display_name", "short_description"):
        value = interface.get(key)
        if not isinstance(value, str) or not value.strip():
            fail(f"agents/openai.yaml requires a non-empty string for interface.{key}.")


def validate_python_script() -> None:
    if not SCRIPT_FILE.exists():
        fail(f"Missing file: {SCRIPT_FILE}")

    try:
        ast.parse(SCRIPT_FILE.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        fail(f"Python syntax error in {SCRIPT_FILE}: {exc}")


def validate_build_artifacts() -> None:
    def is_ignored(path: Path) -> bool:
        try:
            relative = path.relative_to(ROOT)
        except ValueError:
            return False
        parts = relative.parts
        return bool(parts) and parts[0] in IGNORED_TOP_LEVEL_DIRS

    forbidden_dirs = sorted(
        path for path in ROOT.rglob("__pycache__") if path.is_dir() and not is_ignored(path)
    )
    forbidden_files = sorted(path for path in ROOT.rglob("*.pyc") if not is_ignored(path))
    if forbidden_dirs or forbidden_files:
        details = [str(path.relative_to(ROOT)) for path in forbidden_dirs + forbidden_files]
        fail("Repository contains build artifacts:\n- " + "\n- ".join(details))


def main() -> int:
    validate_frontmatter()
    validate_openai_yaml()
    validate_python_script()
    validate_build_artifacts()
    print("[OK] Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
