---
name: leetcode-practice
description: "Use this skill when working in a Python LeetCode practice repo: fetch official problem data from leetcode.cn by problem number, scaffold categorized solution files, continue stuck solutions without editing them, review completed answers, and compare better official approaches."
---

# LeetCode Practice

## Overview

Use this skill when the user is solving LeetCode or other algorithm problems in a Python practice repo. It standardizes file scaffolding, category routing, solution continuation, complexity review, and official-solution comparison.

## Trigger Cases

- The user only gives a LeetCode problem number such as `1`, `42`, or `LCP 82`
- The user says a specific problem is stuck or they cannot finish the code
- The user says a specific problem is completed
- The user asks whether there is a better solution or what the official solution does
- The user says the problem is not from LeetCode and provides the source and statement
- The user says they do not know how to solve the problem and wants a full explanation

## Workflow

### Scaffold by problem number

1. Run `scripts/leetcode_cn.py scaffold <题号> --workspace <repo根目录>`.
2. If the category is ambiguous, review [references/category-routing.md](references/category-routing.md) and rerun with `--category-override <目录名>` when needed.
3. Never overwrite an existing solution file. If the target file already exists, read that file instead of recreating it.
4. The generated file must contain:
   - the official Chinese description from `leetcode.cn`
   - the official Python3 starter code
   - any LeetCode predefined helper classes materialized as real Python classes instead of staying inside comments or a triple-quoted block
   - the required `typing` imports so the generated file can be parsed locally without type-name errors
   - an `if __name__ == '__main__':` block that includes all official examples as labeled test cases
   - real local test data for predefined structures such as `ListNode` and `TreeNode`, instead of passing raw Python lists to methods that expect node objects
   - a printed result and expected output for each official example when the example can be mapped cleanly to the function signature
5. Keep the filename format as `<题号>. <中文题名>.py`.
6. Use the stable category folders from the repo and route sorting-focused problems to `排序`.

### Continue a stuck solution

- Open the existing file first and read the current code together with the user's idea.
- Continue strictly along the user's current direction unless that direction is fundamentally broken.
- If the direction is broken, explain the smallest correction before giving code.
- Do not edit the file. Reply with the continuation code and explanation only.
- Keep the answer short: idea, code, and the key pitfall.

### Review a completed solution

- Read the existing file and analyze the submitted code as written.
- Report:
  - time complexity
  - space complexity
  - concrete optimization points
  - whether the current approach is already optimal for this problem class
- Do not edit the file.

### Summary command

- If the user says `总结`, treat it as a request to summarize the current finished solution style.
- Read the existing file first and summarize the user's actual implemented method, not a different ideal solution.
- For each implemented solution method, produce:
  - one concise summary sentence in comment style
  - time complexity
  - space complexity
- If the user asks to write the summary into the file, add the summary comments immediately above the corresponding method and do not change the algorithm body unless the user also asks for fixes.
- If the current solution is still incomplete or local examples obviously fail, say so first and do not mark it as a finished-summary version until fixed.

### Better solutions and official answers

- Fetch the official solution with `scripts/leetcode_cn.py lookup <题号> --include-solution`.
- Base the answer on the official solution first, then rewrite it into concise and practical language.
- Give `1-3` approaches only when they are meaningfully different.
- For each approach, include the idea, time complexity, space complexity, and Python code.
- If the official solution cannot be fetched, say so briefly and then provide the best verified approaches.

### Non-LeetCode problems

- Use the source named by the user as the top-level folder, creating it if needed.
- Create the file as `<题号或标识>. <题名>.py` when an identifier exists. Otherwise use `<题名>.py`.
- Put the provided statement into a top docstring and create a Python scaffold that matches the described function signature or input/output format.

### Full teaching mode

- When the user clearly cannot solve the problem, explain:
  - how to recognize the problem pattern
  - the core algorithm
  - why it works
  - the complete Python code
- Prefer a direct explanation over long theory.

## Response Style

- All replies in this repo must be clear, concise, and direct.
- Prefer concrete steps, complexity, and code over long background.
- When the request is analysis, review, or advice, do not modify files unless the user explicitly asks for edits.

## Resources

- `scripts/leetcode_cn.py`: fetches official LeetCode CN problem data, official solution content, and scaffolds files.
- `references/category-routing.md`: category mapping, override rules, and folder conventions.
