# LeetCode Practice Skill

[English](README.md)

`leetcode-practice-skill` 是一个面向 Python LeetCode 练习仓库的可复用 skill 包。

它适用于 Codex / OpenClaw 风格的 skill 加载器。这类加载器通常会读取 `SKILL.md` 作为入口，并可配合 `agents/`、`references/`、`scripts/` 等资源使用。这个 skill 主要面向基于 `leetcode.cn` 的中文 LeetCode 工作流。

## 功能

- 根据 LeetCode CN 题号脚手架生成题目文件
- 将新文件路由到稳定的分类目录，例如 `哈希`、`链表`、`图论`、`排序`
- 保留已有题解文件，不覆盖已经做过的题目
- 在用户卡题时继续分析思路，但不直接修改原文件
- 对已完成解法进行复杂度与优化点分析
- 获取官方题解并改写成简洁的 Python 说明
- 根据官方样例生成本地可运行的 `__main__` 测试，必要时补齐 `ListNode`、`TreeNode` 等辅助结构

## 仓库结构

```text
.
├── .github/workflows/validate.yml
├── LICENSE
├── README.md
├── README.zh-CN.md
├── tools/validate_repo.py
└── skills/
    └── leetcode-practice/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── references/category-routing.md
        └── scripts/leetcode_cn.py
```

## 依赖

- Python 3.10+
- 可访问 `https://leetcode.cn/`
- 支持本地 skills 的 Codex / OpenClaw 兼容环境

## 安装

先把仓库克隆到本地任意位置：

```bash
git clone git@github.com:Relifest/leetcode-practice-skill.git
cd leetcode-practice-skill
```

然后通过软链接或复制的方式安装到本地 skill 目录。

软链接方式：

```bash
mkdir -p ~/.codex/skills
ln -s "$(pwd)/skills/leetcode-practice" ~/.codex/skills/leetcode-practice
```

复制方式：

```bash
mkdir -p ~/.codex/skills
cp -R skills/leetcode-practice ~/.codex/skills/leetcode-practice
```

如果你的工具使用了不同的 skill 根目录，把 `~/.codex/skills` 替换成对应路径即可。

## 在练习仓库中使用

在你的算法练习仓库项目说明中引用这个 skill。

示例 `AGENTS.md`：

```md
## Default Skill

Use [/absolute/path/to/skills/leetcode-practice/SKILL.md](/absolute/path/to/skills/leetcode-practice/SKILL.md) for LeetCode-related work in this repo.
```

如果环境支持按名称显式调用 skill，也可以直接使用：

```text
$leetcode-practice
```

## 脚本用法

获取官方题目数据：

```bash
python3 skills/leetcode-practice/scripts/leetcode_cn.py lookup 1
```

向练习仓库脚手架生成题目文件：

```bash
python3 skills/leetcode-practice/scripts/leetcode_cn.py scaffold 912 --workspace /path/to/your/leetcode-repo
```

当自动分类不理想时，强制指定分类：

```bash
python3 skills/leetcode-practice/scripts/leetcode_cn.py scaffold 42 --workspace /path/to/your/leetcode-repo --category-override 栈
```

连同官方题解一起拉取官方题目数据：

```bash
python3 skills/leetcode-practice/scripts/leetcode_cn.py lookup 1 --include-solution
```

## 校验

发布前可以在本地运行仓库校验：

```bash
python3 -m pip install pyyaml
python3 tools/validate_repo.py
```

GitHub Actions 也会在每次 push 和 pull request 时运行同样的校验。

## 说明

- 脚手架脚本直接使用官方 LeetCode CN 数据，不依赖浏览器自动化。
- 生成的测试代码优先保证本地可运行，而不是只给最小占位。
- 这个 skill 主要面向中文 LeetCode 工作流，但脚本内部仍会使用官方英文 slug 和 tags。

## 许可证

本仓库基于 MIT License 发布。详见 [LICENSE](LICENSE)。
