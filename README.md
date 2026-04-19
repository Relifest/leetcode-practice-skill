# LeetCode Practice Skill

`leetcode-practice-skill` is a reusable skill package for Python LeetCode practice repos.

It is designed for Codex / OpenClaw style skill loaders that read a `SKILL.md` entrypoint plus optional `agents/`, `references/`, and `scripts/` resources. The skill focuses on Chinese LeetCode workflows backed by `leetcode.cn`.

## Features

- Scaffold a problem file from an official LeetCode CN problem id
- Route new files into stable category folders such as `哈希`, `链表`, `图论`, and `排序`
- Preserve existing files instead of overwriting solved problems
- Continue a stuck solution without editing the file directly
- Review finished solutions with time complexity, space complexity, and optimization advice
- Fetch the official solution and rewrite it into concise Python explanations
- Generate local `__main__` tests from official examples, including `ListNode` and `TreeNode` helpers when needed

## Repository Layout

```text
.
├── .github/workflows/validate.yml
├── LICENSE
├── README.md
├── tools/validate_repo.py
└── skills/
    └── leetcode-practice/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── references/category-routing.md
        └── scripts/leetcode_cn.py
```

## Requirements

- Python 3.10+
- Network access to `https://leetcode.cn/`
- A Codex / OpenClaw compatible environment that supports local skills

## Install

Clone this repository anywhere on your machine:

```bash
git clone git@github.com:Relifest/leetcode-practice-skill.git
cd leetcode-practice-skill
```

Install the skill into your local skill directory with either a symlink or a copy.

Symlink:

```bash
mkdir -p ~/.codex/skills
ln -s "$(pwd)/skills/leetcode-practice" ~/.codex/skills/leetcode-practice
```

Copy:

```bash
mkdir -p ~/.codex/skills
cp -R skills/leetcode-practice ~/.codex/skills/leetcode-practice
```

If your tool uses a different skill home, replace `~/.codex/skills` with the correct directory.

## Use With A Repo

Point your practice repo to this skill from its project instructions.

Example `AGENTS.md` snippet:

```md
## Default Skill

Use [/absolute/path/to/skills/leetcode-practice/SKILL.md](/absolute/path/to/skills/leetcode-practice/SKILL.md) for LeetCode-related work in this repo.
```

You can also invoke it explicitly in environments that support named skills with:

```text
$leetcode-practice
```

## Script Usage

Fetch official problem data:

```bash
python3 skills/leetcode-practice/scripts/leetcode_cn.py lookup 1
```

Scaffold a file into a practice repo:

```bash
python3 skills/leetcode-practice/scripts/leetcode_cn.py scaffold 912 --workspace /path/to/your/leetcode-repo
```

Force a category when automatic routing is not ideal:

```bash
python3 skills/leetcode-practice/scripts/leetcode_cn.py scaffold 42 --workspace /path/to/your/leetcode-repo --category-override 栈
```

Fetch the official solution together with the official problem payload:

```bash
python3 skills/leetcode-practice/scripts/leetcode_cn.py lookup 1 --include-solution
```

## Validation

Run the repository checks locally before publishing changes:

```bash
python3 -m pip install pyyaml
python3 tools/validate_repo.py
```

The GitHub Actions workflow runs the same validation on every push and pull request.

## Notes

- The scaffold script uses official LeetCode CN data and does not depend on browser automation.
- The generated test block favors runnable local examples over minimal stubs.
- The skill is optimized for Chinese-language LeetCode workflows, but the helper script still uses official English slugs and tags internally.

## License

This repository is released under the MIT License. See [LICENSE](LICENSE).
