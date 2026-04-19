#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import html
import json
import pprint
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

INDEX_URL = "https://leetcode.cn/api/problems/all/"
GRAPHQL_URL = "https://leetcode.cn/graphql/"
DESCRIPTION_URL = "https://leetcode.cn/problems/{slug}/description/"
TIMEOUT_SECONDS = 20

CATEGORY_PRIORITY = [
    "多维动态规划",
    "图论",
    "二叉树",
    "链表",
    "矩阵",
    "滑动窗口",
    "子串",
    "双指针",
    "哈希",
    "二分查找",
    "栈",
    "堆",
    "排序",
    "回溯",
    "贪心算法",
    "动态规划",
    "普通数组",
    "技巧",
]

VALID_CATEGORIES = set(CATEGORY_PRIORITY)
GRAPH_TAGS = {
    "graph",
    "topological-sort",
    "union-find",
    "minimum-spanning-tree",
    "shortest-path",
    "strongly-connected-component",
}
TREE_TAGS = {"binary-tree", "binary-search-tree"}
TECHNIQUE_TAGS = {
    "bit-manipulation",
    "math",
    "simulation",
    "prefix-sum",
    "sorting",
    "string",
    "trie",
    "design",
}
TYPING_NAMES = [
    "Any",
    "Dict",
    "List",
    "Optional",
    "Set",
    "Tuple",
]
PREDEFINED_CLASS_NAMES = ("ListNode", "TreeNode", "Node")


def http_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {
        "User-Agent": "leetcode-practice-skill/1.0",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {message}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc


def normalize_problem_id(raw: str) -> str:
    return re.sub(r"\s+", "", raw).upper()


def get_problem_index_entry(problem_id: str) -> dict[str, Any]:
    payload = http_json(INDEX_URL)
    normalized_target = normalize_problem_id(problem_id)
    for entry in payload.get("stat_status_pairs", []):
        frontend_id = str(entry["stat"]["frontend_question_id"])
        if normalize_problem_id(frontend_id) == normalized_target:
            return entry
    raise RuntimeError(f"Problem {problem_id!r} was not found on leetcode.cn.")


def graphql_query(title_slug: str, include_solution: bool) -> dict[str, Any]:
    solution_block = " solution { id title content }" if include_solution else ""
    query = (
        "query questionData($titleSlug: String!) {"
        " question(titleSlug: $titleSlug) {"
        "   questionId"
        "   title"
        "   titleSlug"
        "   translatedTitle"
        "   translatedContent"
        "   difficulty"
        "   topicTags { name translatedName slug }"
        "   codeSnippets { lang langSlug code }"
        f"   {solution_block}"
        " }"
        "}"
    )
    payload = {
        "query": query,
        "variables": {"titleSlug": title_slug},
    }
    response = http_json(GRAPHQL_URL, payload)
    if "errors" in response:
        raise RuntimeError(json.dumps(response["errors"], ensure_ascii=False))
    question = response.get("data", {}).get("question")
    if not question:
        raise RuntimeError(f"Question data for {title_slug!r} is empty.")
    return question


def strip_html(raw_html: str) -> str:
    text = raw_html or ""
    substitutions = [
        (r"<sup>(.*?)</sup>", r"^\1"),
        (r"<sub>(.*?)</sub>", r"_\1"),
        (r"<iframe[^>]*>.*?</iframe>", ""),
        (r"<br\s*/?>", "\n"),
        (r"</p\s*>", "\n\n"),
        (r"<p[^>]*>", ""),
        (r"</div\s*>", "\n"),
        (r"<div[^>]*>", ""),
        (r"<li[^>]*>", "\n- "),
        (r"</li\s*>", ""),
        (r"</?(ul|ol|pre|blockquote)[^>]*>", "\n"),
        (r"</?(strong|em|span|code)[^>]*>", ""),
    ]
    for pattern, replacement in substitutions:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\xa0", " ")
    text = re.sub(r"(输入|输出|解释|提示|进阶)[：:]\s*\n+", r"\1：", text)
    text = re.sub(r"提示：\s*-\s*", "提示：\n- ", text)
    lines = [line.strip() for line in text.splitlines()]
    cleaned: list[str] = []
    for line in lines:
        if line:
            cleaned.append(re.sub(r"\s+", " ", line))
        elif cleaned and cleaned[-1] != "":
            cleaned.append("")
    return "\n".join(cleaned).strip()


def sanitize_solution_markdown(content: str | None) -> str | None:
    if not content:
        return None
    text = re.sub(r"\[TOC\]\s*", "", content)
    text = re.sub(r"<iframe[^>]*>.*?</iframe>", "", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text)
    return text.strip()


def extract_python3_snippet(code_snippets: list[dict[str, Any]]) -> str:
    for snippet in code_snippets:
        if snippet.get("langSlug") == "python3":
            code = materialize_predefined_classes(str(snippet.get("code", "")))
            return normalize_python_stub(code)
    raise RuntimeError("Python3 starter code was not found.")


def normalize_python_stub(python_code: str) -> str:
    code = python_code.rstrip()
    if not code:
        return code
    lines: list[str] = []
    for line in code.splitlines():
        if re.fullmatch(r"\s*def\s*", line):
            indent = re.match(r"\s*", line).group(0)
            lines.append(f"{indent}pass")
            continue
        lines.append(line)
    normalized: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        normalized.append(line)
        if not line.strip().endswith(":"):
            index += 1
            continue

        current_indent = len(line) - len(line.lstrip())
        next_index = index + 1
        while next_index < len(lines) and not lines[next_index].strip():
            normalized.append(lines[next_index])
            next_index += 1

        if next_index >= len(lines):
            normalized.append(" " * (current_indent + 4) + "pass")
            break

        next_line = lines[next_index]
        next_indent = len(next_line) - len(next_line.lstrip())
        if next_indent <= current_indent:
            normalized.append(" " * (current_indent + 4) + "pass")

        index = next_index

    return "\n".join(normalized)


def materialize_predefined_classes(python_code: str) -> str:
    code = python_code.strip()
    code = unwrap_predefined_docstring_block(code)
    code = uncomment_predefined_class_blocks(code)
    return code


def unwrap_predefined_docstring_block(python_code: str) -> str:
    match = re.match(r"^\s*(?P<quote>\"\"\"|''')\n?(?P<body>.*?)(?:\n)?(?P=quote)\s*\n*", python_code, flags=re.DOTALL)
    if not match:
        return python_code

    body = match.group("body").strip("\n")
    if "class " not in body and "# class " not in body:
        return python_code

    processed_body = uncomment_predefined_class_blocks(body)
    rest = python_code[match.end() :].lstrip("\n")
    if rest:
        return f"{processed_body}\n\n{rest}"
    return processed_body


def uncomment_predefined_class_blocks(python_code: str) -> str:
    def uncomment_once(line: str) -> str:
        return re.sub(r"^(\s*)#\s?", r"\1", line, count=1)

    lines = python_code.splitlines()
    result: list[str] = []
    in_class_block = False

    for line in lines:
        if re.match(r"^\s*#\s*class\s+[A-Za-z_][A-Za-z0-9_]*\s*[:(]", line):
            result.append(uncomment_once(line))
            in_class_block = True
            continue

        if in_class_block:
            if re.match(r"^\s*#(?:\s{4,}|\t+).*$", line):
                result.append(uncomment_once(line))
                continue
            if re.match(r"^\s*#\s*$", line):
                result.append("")
                continue
            in_class_block = False

        result.append(line)

    return "\n".join(result)


def choose_category(question: dict[str, Any], description_text: str, python_code: str) -> str:
    title = str(question.get("translatedTitle") or question.get("title") or "")
    english_title = str(question.get("title") or "")
    title_text = f"{title} {english_title}".lower()
    tag_slugs = {tag["slug"] for tag in question.get("topicTags", [])}

    if "子串" in title or "substring" in title_text:
        return "子串"

    if "dynamic-programming" in tag_slugs and is_multi_dimensional_dp(title, description_text, python_code):
        return "多维动态规划"

    if GRAPH_TAGS & tag_slugs:
        return "图论"

    if TREE_TAGS & tag_slugs or "TreeNode" in python_code:
        return "二叉树"

    if "linked-list" in tag_slugs or "ListNode" in python_code:
        return "链表"

    if "matrix" in tag_slugs:
        return "矩阵"

    if "sorting" in tag_slugs or "排序" in title or "sort" in title_text:
        return "排序"

    candidates: set[str] = set()
    if "sliding-window" in tag_slugs:
        candidates.add("滑动窗口")
    if "two-pointers" in tag_slugs:
        candidates.add("双指针")
    if "hash-table" in tag_slugs:
        candidates.add("哈希")
    if "binary-search" in tag_slugs:
        candidates.add("二分查找")
    if {"stack", "monotonic-stack"} & tag_slugs:
        candidates.add("栈")
    if "heap-priority-queue" in tag_slugs:
        candidates.add("堆")
    if "sorting" in tag_slugs:
        candidates.add("排序")
    if "backtracking" in tag_slugs:
        candidates.add("回溯")
    if "greedy" in tag_slugs:
        candidates.add("贪心算法")
    if "dynamic-programming" in tag_slugs:
        candidates.add("动态规划")
    if "array" in tag_slugs:
        candidates.add("普通数组")

    for category in CATEGORY_PRIORITY:
        if category in candidates:
            return category

    if TECHNIQUE_TAGS & tag_slugs:
        return "技巧"
    return "技巧"


def is_multi_dimensional_dp(title: str, description_text: str, python_code: str) -> bool:
    signal_text = f"{title}\n{description_text}\n{python_code}"
    keywords = [
        "网格",
        "矩阵",
        "路径",
        "三角形",
        "地下城",
        "编辑距离",
        "交错",
        "回文",
        "匹配",
        "子序列",
        "区间",
        "两字符串",
        "List[List",
        "grid",
        "matrix",
        "interval",
    ]
    return any(keyword in signal_text for keyword in keywords)


def build_typing_imports(python_code: str) -> str:
    used = [name for name in TYPING_NAMES if re.search(rf"\b{name}\b", python_code)]
    if not used:
        return ""
    return f"from typing import {', '.join(used)}"


def sanitize_filename_component(text: str) -> str:
    text = re.sub(r'[<>:"/\\\\|?*]', " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_signature(python_code: str) -> tuple[str, list[str]]:
    try:
        tree = ast.parse(python_code)
    except SyntaxError:
        match = re.search(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)", python_code)
        if not match:
            return "solve", []
        func_name = match.group(1)
        raw_params = match.group(2)
        params = []
        for part in raw_params.split(","):
            name = part.strip()
            if not name or name == "self":
                continue
            name = name.split(":", 1)[0].split("=", 1)[0].strip()
            if name:
                params.append(name)
        return func_name, params

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Solution":
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    params = [arg.arg for arg in item.args.args if arg.arg != "self"]
                    return item.name, params

    return "solve", []


def extract_signature_details(
    python_code: str,
) -> tuple[str, list[str], dict[str, str], str]:
    try:
        tree = ast.parse(python_code)
    except SyntaxError:
        func_name, params = extract_signature(python_code)
        return func_name, params, {}, ""

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Solution":
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    params = [arg.arg for arg in item.args.args if arg.arg != "self"]
                    annotations = {
                        arg.arg: ast.unparse(arg.annotation)
                        for arg in item.args.args
                        if arg.arg != "self" and arg.annotation is not None
                    }
                    return_annotation = ast.unparse(item.returns) if item.returns is not None else ""
                    return item.name, params, annotations, return_annotation

    return "solve", [], {}, ""


def solution_uses_predefined_class_params(python_code: str) -> bool:
    try:
        tree = ast.parse(python_code)
    except SyntaxError:
        return bool(re.search(r"\b(ListNode|TreeNode|Node)\b", python_code))

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Solution":
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    for arg in item.args.args:
                        if arg.arg == "self" or arg.annotation is None:
                            continue
                        annotation_text = ast.unparse(arg.annotation)
                        if any(name in annotation_text for name in PREDEFINED_CLASS_NAMES):
                            return True
                    return False

    return False


def extract_labeled_value(block_text: str, label: str) -> str:
    lines = [line.rstrip() for line in block_text.splitlines()]
    prefixes = (f"{label}：", f"{label}:")
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(prefixes):
            for prefix in prefixes:
                if stripped.startswith(prefix):
                    value = stripped[len(prefix) :].strip()
                    break
            else:
                value = ""
            if value:
                return value

            collected: list[str] = []
            for follow in lines[index + 1 :]:
                candidate = follow.strip()
                if not candidate:
                    if collected:
                        break
                    continue
                if any(
                    candidate.startswith(prefix)
                    for prefix in ("输入：", "输入:", "输出：", "输出:", "解释：", "解释:")
                ):
                    break
                collected.append(candidate)
            return " ".join(collected).strip()
    return ""


def parse_example_assignments(input_text: str, params: list[str]) -> list[tuple[str, str]]:
    assignments = []
    for part in split_top_level(input_text):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        assignments.append((key.strip(), normalize_literal(value.strip())))

    if assignments:
        return assignments

    normalized_input = input_text.strip()
    if normalized_input and len(params) == 1:
        return [(params[0], normalize_literal(normalized_input))]

    return []


def normalize_expected_output(output_text: str) -> str:
    raw = output_text.strip()
    normalized = re.sub(r"\bnull\b", "None", raw)
    normalized = re.sub(r"\btrue\b", "True", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bfalse\b", "False", normalized, flags=re.IGNORECASE)
    try:
        parsed = ast.literal_eval(normalized)
    except Exception:
        return repr(raw)
    return pprint.pformat(parsed, width=88, compact=True)


def extract_examples(description_text: str, params: list[str]) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"(?:^|\n)示例(?:\s*(\d+))?\s*[：:]\s*\n?(.*?)(?=\n示例(?:\s*\d+)?\s*[：:]|\n提示[：:]|\n进阶[：:]|$)",
        re.DOTALL,
    )
    examples: list[dict[str, Any]] = []
    for match in pattern.finditer(description_text):
        block = match.group(2).strip()
        input_text = extract_labeled_value(block, "输入")
        output_text = extract_labeled_value(block, "输出")
        if not input_text or not output_text:
            continue
        examples.append(
            {
                "index": int(match.group(1)) if match.group(1) else len(examples) + 1,
                "input_text": input_text,
                "output_text": output_text,
                "assignments": parse_example_assignments(input_text, params),
                "expected_output_expr": normalize_expected_output(output_text),
            }
        )
    return examples


def candidate_assignment_names(param_name: str) -> list[str]:
    names = [param_name]
    match = re.fullmatch(r"list(\d+)", param_name)
    if match:
        names.append(f"l{match.group(1)}")
    match = re.fullmatch(r"head([A-Z])", param_name)
    if match:
        suffix = match.group(1)
        names.append(f"list{suffix}")
    return names


def find_assignment_value(param_name: str, assignments: dict[str, str]) -> str | None:
    for name in candidate_assignment_names(param_name):
        if name in assignments:
            return assignments[name]
    return None


def is_linked_list_annotation(annotation: str) -> bool:
    compact = annotation.replace(" ", "")
    return "ListNode" in compact and not compact.startswith(("List[", "list["))


def is_linked_list_collection_annotation(annotation: str) -> bool:
    compact = annotation.replace(" ", "")
    return "ListNode" in compact and compact.startswith(("List[", "list["))


def is_node_annotation(annotation: str) -> bool:
    compact = annotation.replace(" ", "")
    return "Node" in compact and "ListNode" not in compact and "TreeNode" not in compact


def is_tree_annotation(annotation: str) -> bool:
    return "TreeNode" in annotation


def listnode_result_serializer(output_text: str) -> str:
    stripped = output_text.strip()
    if stripped.startswith("[") or stripped in {"[]", "null", "None"}:
        return "linked_list_to_list"
    return "node_value"


def build_test_support_block(
    func_name: str,
    param_annotations: dict[str, str],
    return_annotation: str,
) -> str:
    needs_linked_list = (
        any(
            is_linked_list_annotation(annotation)
            or is_linked_list_collection_annotation(annotation)
            for annotation in param_annotations.values()
        )
        or is_linked_list_annotation(return_annotation)
    )
    needs_tree = any(is_tree_annotation(annotation) for annotation in param_annotations.values()) or is_tree_annotation(return_annotation)
    needs_random_list = func_name == "copyRandomList" and (
        any(is_node_annotation(annotation) for annotation in param_annotations.values())
        or is_node_annotation(return_annotation)
    )

    sections: list[str] = []
    if needs_linked_list:
        sections.append(
            "\n".join(
                [
                    "def build_linked_list(values: list[int] | None) -> Optional[ListNode]:",
                    "    if not values:",
                    "        return None",
                    "    dummy = ListNode()",
                    "    current = dummy",
                    "    for value in values:",
                    "        current.next = ListNode(value)",
                    "        current = current.next",
                    "    return dummy.next",
                    "",
                    "def build_linked_list_array(values: list[list[int]] | None) -> list[Optional[ListNode]]:",
                    "    if not values:",
                    "        return []",
                    "    return [build_linked_list(item) for item in values]",
                    "",
                    "def linked_list_to_list(head: Optional[ListNode]) -> list[int]:",
                    "    result: list[int] = []",
                    "    current = head",
                    "    while current:",
                    "        result.append(current.val)",
                    "        current = current.next",
                    "    return result",
                    "",
                    "def build_cyclic_linked_list(values: list[int] | None, pos: int) -> Optional[ListNode]:",
                    "    head = build_linked_list(values)",
                    "    if head is None or pos < 0:",
                    "        return head",
                    "    cycle_entry = None",
                    "    tail = None",
                    "    current = head",
                    "    index = 0",
                    "    while current:",
                    "        if index == pos:",
                    "            cycle_entry = current",
                    "        tail = current",
                    "        current = current.next",
                    "        index += 1",
                    "    if tail is not None and cycle_entry is not None:",
                    "        tail.next = cycle_entry",
                    "    return head",
                    "",
                    "def attach_prefix_to_shared(prefix_values: list[int], shared_head: Optional[ListNode]) -> Optional[ListNode]:",
                    "    if not prefix_values:",
                    "        return shared_head",
                    "    head = build_linked_list(prefix_values)",
                    "    tail = head",
                    "    while tail and tail.next:",
                    "        tail = tail.next",
                    "    if tail is not None:",
                    "        tail.next = shared_head",
                    "    return head",
                    "",
                    "def build_intersecting_linked_lists(",
                    "    list_a_values: list[int],",
                    "    list_b_values: list[int],",
                    "    skip_a: int,",
                    "    skip_b: int,",
                    ") -> tuple[Optional[ListNode], Optional[ListNode]]:",
                    "    shared_head = build_linked_list(list_a_values[skip_a:])",
                    "    head_a = attach_prefix_to_shared(list_a_values[:skip_a], shared_head)",
                    "    head_b = attach_prefix_to_shared(list_b_values[:skip_b], shared_head)",
                    "    return head_a, head_b",
                    "",
                    "def node_value(node: Optional[ListNode]) -> int | None:",
                    "    return node.val if node else None",
                ]
            )
        )

    if needs_random_list:
        sections.append(
            "\n".join(
                [
                    "def build_random_list(values: list[list[int | None]] | None) -> Optional[Node]:",
                    "    if not values:",
                    "        return None",
                    "    nodes = [Node(value[0]) for value in values]",
                    "    for index, (_, random_index) in enumerate(values):",
                    "        if index + 1 < len(nodes):",
                    "            nodes[index].next = nodes[index + 1]",
                    "        if random_index is not None:",
                    "            nodes[index].random = nodes[random_index]",
                    "    return nodes[0]",
                    "",
                    "def random_list_to_list(head: Optional[Node]) -> list[list[int | None]]:",
                    "    if head is None:",
                    "        return []",
                    "    nodes: list[Node] = []",
                    "    current = head",
                    "    while current:",
                    "        nodes.append(current)",
                    "        current = current.next",
                    "    index_map = {node: index for index, node in enumerate(nodes)}",
                    "    result: list[list[int | None]] = []",
                    "    for node in nodes:",
                    "        random_index = index_map.get(node.random) if node.random is not None else None",
                    "        result.append([node.val, random_index])",
                    "    return result",
                ]
            )
        )

    if needs_tree:
        sections.append(
            "\n".join(
                [
                    "def build_binary_tree(values: list[int | None] | None) -> Optional[TreeNode]:",
                    "    if not values:",
                    "        return None",
                    "    nodes = [None if value is None else TreeNode(value) for value in values]",
                    "    child_index = 1",
                    "    for node in nodes:",
                    "        if node is None:",
                    "            continue",
                    "        if child_index < len(nodes):",
                    "            node.left = nodes[child_index]",
                    "            child_index += 1",
                    "        if child_index < len(nodes):",
                    "            node.right = nodes[child_index]",
                    "            child_index += 1",
                    "    return nodes[0]",
                    "",
                    "def binary_tree_to_list(root: Optional[TreeNode]) -> list[int | None]:",
                    "    if root is None:",
                    "        return []",
                    "    queue: list[Optional[TreeNode]] = [root]",
                    "    result: list[int | None] = []",
                    "    index = 0",
                    "    while index < len(queue):",
                    "        node = queue[index]",
                    "        index += 1",
                    "        if node is None:",
                    "            result.append(None)",
                    "            continue",
                    "        result.append(node.val)",
                    "        queue.append(node.left)",
                    "        queue.append(node.right)",
                    "    while result and result[-1] is None:",
                    "        result.pop()",
                    "    return result",
                ]
            )
        )

    return "\n\n".join(section for section in sections if section.strip())


def build_example_case_lines(
    example: dict[str, Any],
    func_name: str,
    params: list[str],
    param_annotations: dict[str, str],
    return_annotation: str,
) -> list[str] | None:
    assignments = {name: value for name, value in example["assignments"]}
    lines = [f"# 测试用例 {example['index']}"]
    arg_names: list[str] = []

    listnode_params = [param for param in params if is_linked_list_annotation(param_annotations.get(param, ""))]
    if set(listnode_params) == {"headA", "headB"} and {"listA", "listB", "skipA", "skipB"} <= assignments.keys():
        lines.append(
            "headA, headB = build_intersecting_linked_lists("
            f"{assignments['listA']}, {assignments['listB']}, {assignments['skipA']}, {assignments['skipB']})"
        )

    for param in params:
        annotation = param_annotations.get(param, "")
        arg_names.append(param)
        if set(listnode_params) == {"headA", "headB"} and param in {"headA", "headB"} and {"listA", "listB", "skipA", "skipB"} <= assignments.keys():
            continue

        value = find_assignment_value(param, assignments)
        if value is None:
            return None

        if is_linked_list_collection_annotation(annotation):
            lines.append(f"{param} = build_linked_list_array({value})")
            continue

        if is_linked_list_annotation(annotation):
            if param == "head" and "pos" in assignments:
                lines.append(f"{param} = build_cyclic_linked_list({value}, {assignments['pos']})")
            else:
                lines.append(f"{param} = build_linked_list({value})")
            continue

        if func_name == "copyRandomList" and is_node_annotation(annotation):
            lines.append(f"{param} = build_random_list({value})")
            continue

        if is_tree_annotation(annotation):
            lines.append(f"{param} = build_binary_tree({value})")
            continue

        lines.append(f"{param} = {value}")

    call_expr = f"Solution().{func_name}({', '.join(arg_names)})"
    if is_linked_list_annotation(return_annotation):
        serializer = listnode_result_serializer(example["output_text"])
        if serializer == "linked_list_to_list":
            lines.append(f"result = linked_list_to_list({call_expr})")
        else:
            lines.append(f"result = node_value({call_expr})")
    elif func_name == "copyRandomList" and is_node_annotation(return_annotation):
        lines.append(f"result = random_list_to_list({call_expr})")
    elif is_tree_annotation(return_annotation):
        lines.append(f"result = binary_tree_to_list({call_expr})")
    else:
        lines.append(f"result = {call_expr}")

    lines.append(
        f"print('测试用例 {example['index']}:', result, '期望输出:', {example['expected_output_expr']})"
    )
    return lines


def split_top_level(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    stack: list[str] = []
    quote = ""
    escape = False

    pairs = {")": "(", "]": "[", "}": "{"}
    for char in text:
        if quote:
            current.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = ""
            continue

        if char in {"'", '"'}:
            quote = char
            current.append(char)
            continue

        if char in "([{":
            stack.append(char)
            current.append(char)
            continue

        if char in ")]}":
            if stack and stack[-1] == pairs[char]:
                stack.pop()
            current.append(char)
            continue

        if char == "," and not stack:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
            continue

        current.append(char)

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def normalize_literal(value: str) -> str:
    normalized = re.sub(r"\bnull\b", "None", value)
    normalized = re.sub(r"\btrue\b", "True", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bfalse\b", "False", normalized, flags=re.IGNORECASE)
    try:
        parsed = ast.literal_eval(normalized)
    except Exception:
        return normalized
    return pprint.pformat(parsed, width=88, compact=True)


def extract_first_example_input(description_text: str) -> list[tuple[str, str]]:
    lines = [line.strip() for line in description_text.splitlines()]
    input_text = ""
    for index, line in enumerate(lines):
        if line.startswith("输入：") or line.startswith("输入:"):
            input_text = line.split("：", 1)[1] if "：" in line else line.split(":", 1)[1]
            input_text = input_text.strip()
            if not input_text:
                for follow in lines[index + 1 :]:
                    if follow:
                        input_text = follow
                        break
            break
    if not input_text:
        return []
    assignments = []
    for part in split_top_level(input_text):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        assignments.append((key.strip(), normalize_literal(value.strip())))
    return assignments


def build_main_block(python_code: str, description_text: str) -> str:
    func_name, params, param_annotations, return_annotation = extract_signature_details(python_code)
    examples = extract_examples(description_text, params)
    if not examples:
        return "\n".join(
            [
                "if __name__ == '__main__':",
                "    # TODO: 根据官方示例补充测试数据",
                "    pass",
            ]
        )

    lines = ["if __name__ == '__main__':"]
    generated_any = False
    for example in examples:
        case_lines = build_example_case_lines(
            example=example,
            func_name=func_name,
            params=params,
            param_annotations=param_annotations,
            return_annotation=return_annotation,
        )
        if case_lines is None:
            continue
        generated_any = True
        lines.extend(f"    {line}" if line else "" for line in case_lines)
        lines.append("")

    if not generated_any:
        return "\n".join(
            [
                "if __name__ == '__main__':",
                "    # TODO: 官方示例与函数参数映射较复杂，请手动补充本地测试数据",
                "    pass",
            ]
        )

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def build_problem_payload(problem_id: str, include_solution: bool) -> dict[str, Any]:
    index_entry = get_problem_index_entry(problem_id)
    title_slug = str(index_entry["stat"]["question__title_slug"])
    question = graphql_query(title_slug, include_solution=include_solution)
    description_text = strip_html(str(question.get("translatedContent") or ""))
    python_code = extract_python3_snippet(question.get("codeSnippets", []))
    category = choose_category(question, description_text, python_code)
    topic_tags = [
        {
            "name": tag["name"],
            "translated_name": tag.get("translatedName"),
            "slug": tag["slug"],
        }
        for tag in question.get("topicTags", [])
    ]
    payload: dict[str, Any] = {
        "frontend_question_id": str(index_entry["stat"]["frontend_question_id"]),
        "question_id": str(question.get("questionId")),
        "title": str(question.get("title") or ""),
        "translated_title": str(question.get("translatedTitle") or question.get("title") or ""),
        "title_slug": str(question.get("titleSlug") or title_slug),
        "difficulty": str(question.get("difficulty") or ""),
        "topic_tags": topic_tags,
        "category": category,
        "description_text": description_text,
        "python_code": python_code,
        "description_url": DESCRIPTION_URL.format(slug=title_slug),
    }
    if include_solution:
        solution = question.get("solution") or {}
        payload["solution_title"] = solution.get("title")
        payload["solution_content"] = sanitize_solution_markdown(solution.get("content"))
    return payload


def build_file_content(problem: dict[str, Any]) -> str:
    description = str(problem["description_text"]).replace('"""', '\\"\\"\\"')
    python_code = str(problem["python_code"])
    func_name, _, param_annotations, return_annotation = extract_signature_details(python_code)
    typing_imports = build_typing_imports(python_code)
    support_block = build_test_support_block(func_name, param_annotations, return_annotation)
    sections = [
        f'"""\n{description}\n"""',
        "from __future__ import annotations",
        f"# 题目链接: {problem['description_url']}",
    ]
    if typing_imports:
        sections.append(typing_imports)
    sections.append(python_code.rstrip())
    if support_block:
        sections.append(support_block)
    sections.append(build_main_block(python_code, str(problem["description_text"])))
    return "\n\n".join(section for section in sections if section.strip()) + "\n"


def write_scaffold(problem: dict[str, Any], workspace: Path, category_override: str | None) -> Path:
    category = category_override or str(problem["category"])
    if category not in VALID_CATEGORIES:
        valid = "、".join(CATEGORY_PRIORITY)
        raise RuntimeError(f"Unknown category {category!r}. Valid categories: {valid}")
    folder = workspace / category
    folder.mkdir(parents=True, exist_ok=True)
    file_name = f"{problem['frontend_question_id']}. {sanitize_filename_component(str(problem['translated_title']))}.py"
    target = folder / file_name
    if target.exists():
        raise RuntimeError(f"Target file already exists: {target}")
    target.write_text(build_file_content(problem), encoding="utf-8")
    return target


def cmd_lookup(args: argparse.Namespace) -> int:
    problem = build_problem_payload(args.problem_id, include_solution=args.include_solution)
    print(json.dumps(problem, ensure_ascii=False, indent=2))
    return 0


def cmd_scaffold(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    if not workspace.exists():
        raise RuntimeError(f"Workspace does not exist: {workspace}")
    problem = build_problem_payload(args.problem_id, include_solution=False)
    target = write_scaffold(problem, workspace, args.category_override)
    result = {
        "frontend_question_id": problem["frontend_question_id"],
        "translated_title": problem["translated_title"],
        "category": args.category_override or problem["category"],
        "file_path": str(target),
        "description_url": problem["description_url"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch and scaffold LeetCode CN problems.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lookup_parser = subparsers.add_parser("lookup", help="Fetch official problem data as JSON.")
    lookup_parser.add_argument("problem_id", help="LeetCode frontend problem id, such as 1 or LCP 82.")
    lookup_parser.add_argument(
        "--include-solution",
        action="store_true",
        help="Include the official solution markdown when available.",
    )
    lookup_parser.set_defaults(func=cmd_lookup)

    scaffold_parser = subparsers.add_parser("scaffold", help="Create a local Python scaffold file.")
    scaffold_parser.add_argument("problem_id", help="LeetCode frontend problem id, such as 1 or LCP 82.")
    scaffold_parser.add_argument("--workspace", required=True, help="Root folder of the practice repo.")
    scaffold_parser.add_argument(
        "--category-override",
        help="Force the target category folder when the automatic routing is not ideal.",
    )
    scaffold_parser.set_defaults(func=cmd_scaffold)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
