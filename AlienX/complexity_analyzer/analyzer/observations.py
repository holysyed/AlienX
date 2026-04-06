"""
analyzer/observations.py
--------------------------
Generates human-readable observations and optimization suggestions
based on the parse data and deduced complexity results.

NOTE: Only ASCII characters are used here so the output is safe on
Windows terminals with legacy (CP-1252) encoding.
"""

from __future__ import annotations

import re
from .complexity import DeductionResult
from .parsers    import ParseResult


def generate_observations(
    code: str,
    parse: ParseResult,
    result: DeductionResult,
) -> tuple[list[str], list[str]]:
    """
    Returns (observations, suggestions).
    observations -- things noticed about the code
    suggestions  -- actionable improvements
    """
    obs: list[str] = []
    sug: list[str] = []

    nesting = parse.get("max_nesting", 0)
    loops   = parse.get("loops", [])
    has_rec = parse.get("has_recursion", False)
    calls   = parse.get("builtin_calls", [])
    worst   = result.worst_case.notation

    # -- Known algorithm --------------------------------------------------
    if result.known_algorithm:
        obs.append(
            f"[OK]  Recognized algorithm: [bold cyan]{result.known_algorithm}[/bold cyan]. "
            f"Standard complexities confirmed."
        )

    # -- Quick Sort caveat ------------------------------------------------
    if result.known_algorithm and "Quick" in result.known_algorithm:
        obs.append(
            "[!!]  Quick Sort worst case is O(n^2) when pivot is always min/max "
            "(e.g., already-sorted input with naive pivot)."
        )
        sug.append(
            "Use median-of-three or randomized pivot selection to avoid worst-case O(n^2) in Quick Sort."
        )

    # -- Exponential ------------------------------------------------------
    if "2^n" in worst or "n!" in worst:
        obs.append(
            "[!!]  Exponential/factorial complexity! "
            "Only feasible for very small inputs (n <= 25)."
        )
        sug.append(
            "Consider Memoization (top-down DP) or Tabulation (bottom-up DP) "
            "to reduce exponential recursion to polynomial time."
        )

    # -- Quadratic --------------------------------------------------------
    if "n^2" in worst or "n2" in worst.replace("n²", "n2"):
        obs.append(
            f"[!!]  O(n^2) complexity -- becomes slow for n > 10,000. "
            f"Nesting depth: {nesting}."
        )
        sug.append(
            "Replace the inner-loop linear search with a hash map/set "
            "to achieve O(n) time (classic space-time trade-off)."
        )

    # -- Cubic or higher --------------------------------------------------
    if "n^3" in worst or ("n^" in worst and "n^2" not in worst and "^n" not in worst):
        obs.append(
            "[!!]  O(n^3) or higher polynomial complexity -- very expensive for n > 1,000."
        )
        sug.append(
            "Look for divide-and-conquer or DP approaches to reduce the polynomial degree."
        )

    # -- Deep nesting -----------------------------------------------------
    if nesting >= 3:
        obs.append(
            f"[!!]  {nesting}-level loop nesting -- a common code-smell for high polynomial complexity."
        )
        sug.append(
            "Flatten deeply nested loops where possible; precompute partial "
            "results with auxiliary data structures."
        )

    # -- Recursion without memoization ------------------------------------
    if has_rec and not re.search(
        r"\bmemo\b|\bcache\b|\bdp\b|\blru_cache\b|\bfunctools\b",
        code, re.IGNORECASE
    ):
        obs.append(
            "[!!]  Recursion without memoization -- may recompute overlapping subproblems."
        )
        sug.append(
            "Add memoization with a dict or @functools.lru_cache "
            "to eliminate redundant recursive calls."
        )

    # -- Built-in sort inside a loop --------------------------------------
    sort_calls = [
        c for c, _ in calls
        if c in ("sorted", "sort", "Array.sort", "Arrays.sort", "Collections.sort")
    ]
    if sort_calls and loops:
        obs.append(
            f"[!!]  Calling {sort_calls[0]}() [O(n log n)] inside a loop -- "
            f"overall complexity inflates to at least O(n^2 log n)."
        )
        sug.append(
            f"Pre-sort the data once outside the loop if the data doesn't change each iteration."
        )

    # -- Linear search inside a loop --------------------------------------
    if nesting >= 2 and re.search(r"\bin\s+\w+|\bindex\s*\(|\bfind\s*\(", code):
        obs.append(
            "[!!]  Linear search (find / 'in list') inside a loop -- leads to at least O(n^2)."
        )
        sug.append(
            "Convert the target collection to a set or dict first; "
            "lookup drops to O(1) average."
        )

    # -- O(n log n) is optimal for comparison-based sorting ---------------
    if "n log n" in worst and result.known_algorithm:
        obs.append(
            "[OK]  O(n log n) -- optimal for comparison-based sorting (proven lower bound)."
        )

    # -- Constant time ----------------------------------------------------
    if worst == "O(1)":
        obs.append(
            "[OK]  O(1) constant time -- does a fixed amount of work regardless of input size."
        )

    # -- Logarithmic ------------------------------------------------------
    if worst == "O(log n)":
        obs.append(
            "[OK]  O(log n) -- excellent! The search space halves at each step."
        )

    # -- Linear O(n) ------------------------------------------------------
    if worst == "O(n)" and not has_rec:
        obs.append(
            "[OK]  O(n) linear time -- the algorithm touches each element at most once."
        )

    # -- Fallback ---------------------------------------------------------
    if not obs:
        obs.append(
            "[OK]  No significant inefficiencies detected in the analyzed structure."
        )

    return obs, sug
