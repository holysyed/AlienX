"""
analyzer/complexity.py
───────────────────────
Complexity deduction engine.

  Step 1 — attempts known-algorithm detection (short-circuit)
  Step 2 — analyses recursion → recurrence relation → Master Theorem
  Step 3 — falls back to loop-nesting heuristics + builtin-cost blending
  Step 4 — estimates space complexity
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .knowledge import KNOWN_ALGORITHMS, BUILTIN_COSTS
from .languages import Language


# ─── Data classes ─────────────────────────────────────────────────────────────
@dataclass
class Complexity:
    notation:     str
    explanation:  str


@dataclass
class RecurrenceResult:
    relation:     str            # e.g. "T(n) = 2T(n/2) + O(n)"
    solution:     str            # e.g. "O(n log n)"
    master_case:  Optional[str]  # e.g. "Master Theorem Case 2"
    space:        str            # stack space


@dataclass
class DeductionResult:
    known_algorithm: Optional[str]            # friendly name if detected
    recurrence:      Optional[RecurrenceResult]
    best_case:       Complexity
    average_case:    Optional[Complexity]
    worst_case:      Complexity
    space:           Complexity


# ─── Complexity ordering (higher index = more expensive) ──────────────────────
_ORDER = [
    "O(1)", "O(log log n)", "O(log n)", "O(sqrt n)",
    "O(n)", "O(n log n)", "O(n log^2 n)",
    "O(n^2)", "O(n^2 log n)", "O(n^3)", "O(n^k)",
    "O(2^n)", "O(n!)",
]

def _order(notation: str) -> int:
    # normalise any stray Greek that might appear
    notation = notation.replace("Omega", "O").replace("Theta", "O").rstrip("*")
    for i, n in enumerate(_ORDER):
        if n == notation:
            return i
    return 5  # default to O(n) tier


# ─── Main engine ──────────────────────────────────────────────────────────────
class ComplexityEngine:
    """Deduce time and space complexity from parsed analysis data."""

    def deduce(self, parse_data: dict[str, Any], language: Language, code: str) -> DeductionResult:

        # ── Step 1: known algorithm? ──────────────────────────────────────
        algo = self._detect_known_algo(code)
        if algo:
            name, best, avg, worst, space_str = algo
            return DeductionResult(
                known_algorithm=name,
                recurrence=None,
                best_case   = Complexity(best,      f"Best case for {name}"),
                average_case= Complexity(avg,       f"Average case for {name}"),
                worst_case  = Complexity(worst,     f"Worst case for {name}"),
                space       = Complexity(space_str, f"Auxiliary space for {name}"),
            )

        loops           = parse_data.get("loops", [])
        max_nesting     = parse_data.get("max_nesting", 0)
        has_recursion   = parse_data.get("has_recursion", False)
        rec_funcs       = parse_data.get("recursive_funcs", [])
        builtin_calls   = parse_data.get("builtin_calls", [])

        # ── Step 2: recursion analysis ────────────────────────────────────
        recurrence: Optional[RecurrenceResult] = None
        if has_recursion and rec_funcs:
            recurrence = self._analyze_recursion(code, rec_funcs, max_nesting)

        if recurrence:
            comp = recurrence.solution
            space_str = recurrence.space
            return DeductionResult(
                known_algorithm=None,
                recurrence=recurrence,
                best_case   = Complexity(comp,     "Recursive call - minimum path"),
                average_case= Complexity(comp,     "Recursive call - expected path"),
                worst_case  = Complexity(comp,     "Recursive call - maximum depth"),
                space       = Complexity(space_str,"Recursion call-stack depth"),
            )

        # ── Step 3: loop-nesting heuristics ──────────────────────────────
        is_log = self._is_logarithmic(code)

        if not loops:
            base_worst = "O(1)"
            base_best  = "Omega(1)"
        elif is_log and max_nesting <= 1:
            base_worst = "O(log n)"
            base_best  = "Omega(1)"
        elif max_nesting == 1:
            base_worst = "O(n)"
            base_best  = "Omega(1)"
        elif max_nesting == 2:
            base_worst = "O(n^2)"
            base_best  = "Omega(n)"
        elif max_nesting == 3:
            base_worst = "O(n^3)"
            base_best  = "Omega(n^2)"
        else:
            base_worst = f"O(n^{max_nesting})"
            base_best  = f"Omega(n^{max_nesting - 1})"

        # Does a built-in call dominate?
        builtin_max = self._dominant_builtin(builtin_calls)
        final_worst = self._blend(base_worst, builtin_max, max_nesting)

        # quick early-exit detection
        has_early_exit = bool(re.search(r"\breturn\b", code)) and max_nesting >= 1
        best_str = base_best if not has_early_exit else "Omega(1)"

        # ── Step 4: space ─────────────────────────────────────────────────
        space_str = self._estimate_space(code, parse_data, max_nesting)

        return DeductionResult(
            known_algorithm=None,
            recurrence=None,
            best_case   = Complexity(best_str,    "Minimum work - e.g., early return or trivial input"),
            average_case= Complexity(final_worst, "Expected complexity over uniformly distributed inputs"),
            worst_case  = Complexity(final_worst, "Maximum work - no early exits, full iteration"),
            space       = Complexity(space_str,   "Auxiliary memory beyond input size"),
        )

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _detect_known_algo(self, code: str) -> Optional[tuple]:
        code_lower = code.lower()
        for pattern, info in KNOWN_ALGORITHMS.items():
            if re.search(pattern, code_lower):
                return info
        return None

    def _is_logarithmic(self, code: str) -> bool:
        """Detect binary-search or halving-loop patterns."""
        patterns = [
            r"\bmid\b.*//\s*2",
            r"\bmid\b.*>>\s*1",
            r"\blow\b.*\bhigh\b.*\bmid\b",
            r"\bleft\b.*\bright\b.*\bmid\b",
            r"\bstart\b.*\bend\b.*\bmid\b",
            r"\bn\s*[/]{1,2}=\s*2",
            r"\bn\s*>>=\s*1",
            r"\bi\s*\*=\s*2",
            r"\bi\s*[/]{1,2}=\s*2",
        ]
        for pat in patterns:
            if re.search(pat, code, re.IGNORECASE):
                return True
        return False

    def _analyze_recursion(
        self,
        code: str,
        func_names: list[str],
        loop_nesting: int,
    ) -> RecurrenceResult:
        """Build and solve a recurrence relation for a recursive function."""
        func = func_names[0]

        # Count recursive calls (appearances of function name − 1 for definition)
        call_count = max(
            len(re.findall(r"\b" + re.escape(func) + r"\s*\(", code)) - 1, 1
        )

        # Detect the sub-problem size relationship
        divide_by = "n-1"  # default (linear recursion)
        if re.search(r"n\s*[/]{1,2}\s*2|mid|>>", code):
            divide_by = "n/2"
        elif re.search(r"n\s*[/]{1,2}\s*3", code):
            divide_by = "n/3"

        # Extra work per level
        extra = "O(n)" if loop_nesting >= 1 else "O(1)"

        # Build recurrence string
        if divide_by == "n/2":
            rel = f"T(n) = {call_count}T(n/2) + {extra}"
        elif divide_by == "n/3":
            rel = f"T(n) = {call_count}T(n/3) + {extra}"
        else:
            rel = f"T(n) = {call_count}T(n-1) + {extra}"

        # Solve
        solution, master_case, space = self._solve_recurrence(
            call_count, divide_by, extra
        )

        return RecurrenceResult(
            relation    = rel,
            solution    = solution,
            master_case = master_case,
            space       = space,
        )

    @staticmethod
    def _solve_recurrence(
        a: int, divide_by: str, extra: str
    ) -> tuple[str, Optional[str], str]:
        """
        Apply Master Theorem: T(n) = a·T(n/b) + f(n)
          Case 1: f(n) = O(n^c) where c < log_b(a)  → O(n^log_b(a))
          Case 2: f(n) = O(n^log_b(a))               → O(n^log_b(a) · log n)
          Case 3: f(n) dominates                     → O(f(n))
        """
        import math

        b_map = {"n/2": 2, "n/3": 3, "n-1": 1}
        b = b_map.get(divide_by, 2)

        if divide_by == "n-1":
            # Linear recursion — no Master Theorem
            if a == 1:
                if extra == "O(1)":
                    return "O(n)", None, "O(n)"
                if extra == "O(n)":
                    return "O(n^2)", None, "O(n)"
            if a == 2:
                if extra == "O(1)":
                    return "O(2^n)", None, "O(n)"
                return "O(2^n)", None, "O(n)"
            return "O(a^n)", None, "O(n)"

        log_b_a = math.log(a, b) if b > 1 else 0

        if extra == "O(1)":
            # f(n) = O(n^0)
            if log_b_a > 0:
                master = f"Master Theorem Case 1 → O(n^log_{b}({a})) = O(n^{log_b_a:.2f})"
                solution = f"O(n^{log_b_a:.2f})" if log_b_a != 1 else "O(n)"
            else:
                master = "Trivial — single call with O(1) work → O(log n)"
                solution = "O(log n)"
            space = "O(log n)"
        elif extra == "O(n)":
            # f(n) = O(n^1)
            if abs(log_b_a - 1.0) < 0.01:
                master = f"Master Theorem Case 2 → O(n log n)"
                solution = "O(n log n)"
            elif log_b_a > 1.0:
                master = f"Master Theorem Case 1 → O(n^{log_b_a:.2f})"
                solution = f"O(n^{log_b_a:.2f})"
            else:
                master = "Master Theorem Case 3 → O(n)"
                solution = "O(n)"
            space = "O(log n)"
        else:
            master = None
            solution = "O(n log n)"  # safe conservative estimate
            space = "O(log n)"

        return solution, master, space

    @staticmethod
    def _dominant_builtin(calls: list[tuple[str, str]]) -> Optional[str]:
        if not calls:
            return None
        best = max(calls, key=lambda x: _order(x[1]))
        return best[1]

    @staticmethod
    def _blend(loop_worst: str, builtin: Optional[str], nesting: int) -> str:
        """Return the dominant complexity between loop and any built-in calls."""
        if not builtin:
            return loop_worst
        # If O(n log n) builtin is called inside an O(n) loop → O(n² log n)
        if "n log n" in builtin and nesting >= 1:
            return "O(n^2 log n)"
        # Otherwise take the higher of the two
        if _order(builtin) > _order(loop_worst):
            return builtin
        return loop_worst

    @staticmethod
    def _estimate_space(
        code: str, parse_data: dict[str, Any], nesting: int
    ) -> str:
        # 2-D arrays / grids
        if re.search(r"\[\s*\[|\bnp\.zeros\s*\(\s*\(|\bnp\.ones\s*\(\s*\(|int\[n\]\[n\]|new int\[n\]\[n\]", code):
            return "O(n^2)"

        # Recursion call-stack
        if parse_data.get("has_recursion"):
            if re.search(r"n\s*[/]{1,2}\s*2|mid|>>", code):
                return "O(log n)"
            return "O(n)"

        # Explicit n-sized allocations
        if re.search(r"\w+\s*=\s*\[\s*\]\s*|\bnew\s+\w+\[\s*n\s*\]|ArrayList<|vector<", code):
            return "O(n)"

        # Hash structures
        if re.search(r"\{\s*\}|\bdict\(\)|\bHashMap\b|\bunordered_map\b|\bSet\b|\bset\(\)", code):
            return "O(n)"

        # Simple variables only
        return "O(1)"
