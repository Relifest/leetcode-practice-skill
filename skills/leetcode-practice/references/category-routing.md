# Category Routing

Use one stable folder per problem. Prefer the obvious subject category first: graph, tree, linked list, and matrix should stay in their own folders even if the common solution uses a generic technique such as two pointers or hashing.

## Folder List

- 哈希
- 双指针
- 滑动窗口
- 子串
- 普通数组
- 排序
- 矩阵
- 链表
- 二叉树
- 图论
- 回溯
- 二分查找
- 栈
- 堆
- 贪心算法
- 动态规划
- 多维动态规划
- 技巧

## Default Routing Rules

1. If the Chinese title contains `子串` or the English title contains `substring`, route to `子串`.
2. If the problem is clearly multi-dimensional DP, route to `多维动态规划`.
3. If the tags clearly indicate a subject category, use it first:
   - `graph`, `topological-sort`, `union-find`, `minimum-spanning-tree`, `shortest-path` -> `图论`
   - `binary-tree`, `binary-search-tree`, or `TreeNode` signature -> `二叉树`
   - `linked-list` or `ListNode` signature -> `链表`
   - `matrix` -> `矩阵`
4. Otherwise prefer this technique priority:
   - `sliding-window` -> `滑动窗口`
   - `two-pointers` -> `双指针`
   - `hash-table` -> `哈希`
   - `binary-search` -> `二分查找`
   - `stack`, `monotonic-stack` -> `栈`
   - `heap-priority-queue` -> `堆`
   - `sorting` -> `排序`
   - `backtracking` -> `回溯`
   - `greedy` -> `贪心算法`
   - `dynamic-programming` -> `动态规划`
   - `array` -> `普通数组`
5. Everything else goes to `技巧`.

## Multi-Dimensional DP Heuristics

Treat the problem as `多维动态规划` when `dynamic-programming` is present and at least one of these signals is obvious:

- grid or matrix state
- path counting or path cost
- two-string DP
- interval DP
- triangle or dungeon style state transition
- the starter code uses `List[List[...]]` together with DP

If the generated category still feels wrong, rerun the scaffold command with `--category-override`.

## Stability Rules

- If the file already exists in a folder, keep that existing location.
- Do not duplicate the same problem in multiple folders unless the user explicitly asks.
- When the official tags and the common interview technique disagree, prefer the clearer subject folder for graph, tree, linked list, and matrix problems.

## Common Examples

- `1. 两数之和` -> `哈希`
- `3. 无重复字符的最长子串` -> `子串`
- `11. 盛最多水的容器` -> `双指针`
- `160. 相交链表` -> `链表`
- `42. 接雨水` -> `双指针` by default, unless the repo already keeps it under `栈`
- `62. 不同路径` -> `多维动态规划`
- `912. 排序数组` -> `排序`
