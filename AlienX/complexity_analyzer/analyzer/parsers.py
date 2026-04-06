"""
analyzer/parsers.py
────────────────────
Code structure parsers.

• PythonParser  – uses the stdlib `ast` module (precise)
• GenericParser – regex-based fallback for C/C++/Java/JS/pseudo
"""

from __future__ import annotations

import ast
import re
from typing import Any

from .knowledge import BUILTIN_COSTS
from .languages import Language


# ─── Result type ─────────────────────────────────────────────────────────────
ParseResult = dict[str, Any]
"""
Keys produced by both parsers:
  loops           : list[str]
  max_nesting     : int
  has_recursion   : bool
  recursive_funcs : list[str]
  builtin_calls   : list[tuple[str, str]]   # (name, complexity)
  conditionals    : list[str]
  data_structures : list[str]
  functions       : list[str]               # all top-level function names
"""


# ─────────────────────────────────────────────────────────────────────────────
# Python parser (AST-based)
# ─────────────────────────────────────────────────────────────────────────────
class PythonParser:
    """Precise structural analysis of Python source using the AST module."""

    def parse(self, code: str) -> ParseResult:
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return {"parse_error": str(exc)}

        visitor = _PythonVisitor()
        visitor.visit(tree)

        return {
            "loops":           visitor.loops,
            "max_nesting":     visitor.max_depth,
            "has_recursion":   bool(visitor.recursive_funcs),
            "recursive_funcs": list(visitor.recursive_funcs),
            "builtin_calls":   visitor.builtin_calls,
            "conditionals":    visitor.conditionals,
            "data_structures": visitor.data_structures,
            "functions":       list(visitor.function_names),
        }


class _PythonVisitor(ast.NodeVisitor):
    """Walk the Python AST and collect structural metadata."""

    def __init__(self) -> None:
        self.loops:           list[str]        = []
        self.max_depth:       int              = 0
        self.conditionals:    list[str]        = []
        self.builtin_calls:   list[tuple]      = []
        self.data_structures: list[str]        = []
        self.function_names:  set[str]         = set()
        self.recursive_funcs: set[str]         = set()
        self._loop_depth:     int              = 0

    # ── Loops ──────────────────────────────────────────────────────────────
    def visit_For(self, node: ast.For) -> None:
        self._loop_depth += 1
        self.max_depth = max(self.max_depth, self._loop_depth)
        iter_desc = self._iter_desc(node.iter)
        self.loops.append(
            f"for-loop  (depth {self._loop_depth}) — iterating over {iter_desc}"
        )
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_While(self, node: ast.While) -> None:
        self._loop_depth += 1
        self.max_depth = max(self.max_depth, self._loop_depth)
        self.loops.append(f"while-loop (depth {self._loop_depth}) — line {node.lineno}")
        self.generic_visit(node)
        self._loop_depth -= 1

    visit_AsyncFor = visit_For  # treat async for like a normal for

    # ── Conditionals ───────────────────────────────────────────────────────
    def visit_If(self, node: ast.If) -> None:
        self.conditionals.append(f"if-statement at line {node.lineno}")
        self.generic_visit(node)

    # ── Data structures ────────────────────────────────────────────────────
    def visit_List(self, node: ast.List) -> None:
        self.data_structures.append("list literal")
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        self.data_structures.append("dict literal")
        self.generic_visit(node)

    def visit_Set(self, node: ast.Set) -> None:
        self.data_structures.append("set literal")
        self.generic_visit(node)

    # ── Function definitions (collect names + detect recursion) ────────────
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_names.add(node.name)
        # Check for recursive call inside this function body
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                name = _call_name(child)
                if name == node.name:
                    self.recursive_funcs.add(node.name)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    # ── Calls (builtins) ───────────────────────────────────────────────────
    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node)
        if name in BUILTIN_COSTS:
            entry = (name, BUILTIN_COSTS[name])
            if entry not in self.builtin_calls:
                self.builtin_calls.append(entry)
        self.generic_visit(node)

    # ── Helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _iter_desc(iter_node: ast.expr) -> str:
        if isinstance(iter_node, ast.Call):
            fname = _call_name(iter_node)
            if fname == "range":
                n = len(iter_node.args)
                if n == 1:
                    return "range(n)"
                if n == 2:
                    return "range(start, n)"
                parts = []
                for a in iter_node.args:
                    parts.append(str(a.value) if isinstance(a, ast.Constant) else "?")
                return f"range({', '.join(parts)})"
            return f"{fname}(...)"
        if isinstance(iter_node, ast.Name):
            return iter_node.id
        return "iterable"

    # make static method accessible via self
    _iter_desc = staticmethod(_iter_desc.__func__) if hasattr(_iter_desc, '__func__') else _iter_desc


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Generic parser (regex-based — C / C++ / Java / JS / pseudocode)
# ─────────────────────────────────────────────────────────────────────────────
class GenericParser:
    """Regex-based structural analysis for non-Python languages."""

    # Patterns
    _LOOP_RE  = re.compile(r"\b(for|while|do)\b")
    _OPEN_RE  = re.compile(r"\{")
    _CLOSE_RE = re.compile(r"\}")
    _IF_RE    = re.compile(r"\b(if|else\s+if|elif|switch)\s*[\(\s]")

    def parse(self, code: str, language: Language) -> ParseResult:
        lines = code.splitlines()
        loops:        list[str]   = []
        conditionals: list[str]   = []
        max_nesting:  int         = 0
        depth:        int         = 0   # brace depth
        loop_depth:   int         = 0   # how deep in loops we are

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track brace depth  
            opens  = stripped.count("{")
            closes = stripped.count("}")

            if self._LOOP_RE.search(stripped):
                loop_depth += 1
                max_nesting = max(max_nesting, loop_depth)
                loops.append(
                    f"{self._LOOP_RE.search(stripped).group(1)}-loop "
                    f"(depth {loop_depth}) at line {i}"
                )

            if self._IF_RE.search(stripped):
                conditionals.append(f"conditional at line {i}")

            depth += opens - closes
            # Heuristic: if we closed braces we may have exited loops
            if closes > opens and loop_depth > 0:
                loop_depth = max(0, loop_depth - (closes - opens))

        # Detect function names and recursion
        func_names = self._find_functions(code, language)
        recursive_funcs = self._find_recursion(code, func_names)

        # Built-in calls
        builtin_calls = [
            (name, cost)
            for name, cost in BUILTIN_COSTS.items()
            if re.search(r"\b" + re.escape(name) + r"\s*[\.(]", code)
        ]

        # Data structures (rough heuristic)
        data_structures = []
        if re.search(r"ArrayList|vector<|List<|\[\]", code):
            data_structures.append("dynamic array")
        if re.search(r"HashMap|unordered_map|Map<|dict", code):
            data_structures.append("hash map")
        if re.search(r"HashSet|unordered_set|Set<", code):
            data_structures.append("hash set")
        if re.search(r"Stack|stack<|Deque|deque<", code):
            data_structures.append("stack/deque")
        if re.search(r"PriorityQueue|priority_queue", code):
            data_structures.append("priority queue")

        return {
            "loops":           loops,
            "max_nesting":     max_nesting,
            "has_recursion":   bool(recursive_funcs),
            "recursive_funcs": list(recursive_funcs),
            "builtin_calls":   builtin_calls,
            "conditionals":    conditionals,
            "data_structures": data_structures,
            "functions":       list(func_names),
        }

    # ── Helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _find_functions(code: str, language: Language) -> set[str]:
        patterns = {
            Language.JAVA:       r"(?:public|private|protected|static|\s)+\w[\w<>\[\]]*\s+(\w+)\s*\(",
            Language.CPP:        r"(?:[\w:*&]+\s+)+(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{",
            Language.C:          r"(?:[\w*]+\s+)+(\w+)\s*\([^)]*\)\s*\{",
            Language.JAVASCRIPT: r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\())",
        }
        pat = patterns.get(language, r"\b(\w+)\s*\(")
        names: set[str] = set()
        for m in re.finditer(pat, code):
            for grp in m.groups():
                if grp and grp not in {"if", "while", "for", "switch", "return"}:
                    names.add(grp)
        return names

    @staticmethod
    def _find_recursion(code: str, func_names: set[str]) -> set[str]:
        recursive: set[str] = set()
        for name in func_names:
            # definition + at least one call inside
            pattern = re.compile(r"\b" + re.escape(name) + r"\s*\(")
            if len(pattern.findall(code)) >= 2:
                recursive.add(name)
        return recursive
