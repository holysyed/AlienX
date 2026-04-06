"""
analyzer/knowledge.py
----------------------
Static knowledge bases:
  KNOWN_ALGORITHMS  -- pattern -> (name, best, average, worst, space)
  BUILTIN_COSTS     -- function name -> complexity string

NOTE: Only ASCII characters are used so Windows CP-1252 terminals work fine.
      Best/average use Omega/Theta notation spelled out, not Greek letters.
"""

# ─── Known algorithm signatures ──────────────────────────────────────────────
# Key  : regex pattern matched case-insensitively against the full source
# Value: (friendly_name, best, average, worst, space)
KNOWN_ALGORITHMS: dict[str, tuple] = {
    # ── Sorting ──────────────────────────────────────────────────────────
    r"bubble.?sort":    ("Bubble Sort",    "Omega(n)",       "Theta(n^2)",        "O(n^2)",       "O(1)"),
    r"selection.?sort": ("Selection Sort", "Omega(n^2)",     "Theta(n^2)",        "O(n^2)",       "O(1)"),
    r"insertion.?sort": ("Insertion Sort", "Omega(n)",       "Theta(n^2)",        "O(n^2)",       "O(1)"),
    r"merge.?sort":     ("Merge Sort",     "Omega(n log n)", "Theta(n log n)",    "O(n log n)",   "O(n)"),
    r"quick.?sort":     ("Quick Sort",     "Omega(n log n)", "Theta(n log n)*",   "O(n^2)",       "O(log n)"),
    r"heap.?sort":      ("Heap Sort",      "Omega(n log n)", "Theta(n log n)",    "O(n log n)",   "O(1)"),
    r"counting.?sort":  ("Counting Sort",  "Omega(n+k)",     "Theta(n+k)",        "O(n+k)",       "O(k)"),
    r"radix.?sort":     ("Radix Sort",     "Omega(nk)",      "Theta(nk)",         "O(nk)",        "O(n+k)"),
    r"tim.?sort":       ("Tim Sort",       "Omega(n)",       "Theta(n log n)",    "O(n log n)",   "O(n)"),
    r"shell.?sort":     ("Shell Sort",     "Omega(n log n)", "Theta(n log^2 n)",  "O(n^2)",       "O(1)"),

    # ── Searching ────────────────────────────────────────────────────────
    r"binary.?search":  ("Binary Search",  "Omega(1)",       "Theta(log n)",      "O(log n)",     "O(1)"),
    r"linear.?search":  ("Linear Search",  "Omega(1)",       "Theta(n)",          "O(n)",         "O(1)"),
    r"jump.?search":    ("Jump Search",    "Omega(1)",       "Theta(sqrt n)",     "O(sqrt n)",    "O(1)"),

    # ── Graph Traversal ──────────────────────────────────────────────────
    r"\bbfs\b|breadth.?first": ("BFS (Breadth-First)", "Omega(1)", "Theta(V+E)", "O(V+E)", "O(V)"),
    r"\bdfs\b|depth.?first":   ("DFS (Depth-First)",   "Omega(1)", "Theta(V+E)", "O(V+E)", "O(V)"),
    r"dijkstra":               ("Dijkstra's Algorithm", "Omega(E)", "Theta((V+E) log V)", "O((V+E) log V)", "O(V)"),
    r"bellman.?ford":          ("Bellman-Ford",         "Omega(E)", "Theta(VE)",  "O(VE)",  "O(V)"),
    r"floyd.?warshall":        ("Floyd-Warshall",       "Omega(V^3)", "Theta(V^3)", "O(V^3)", "O(V^2)"),
    r"prim|kruskal":           ("Minimum Spanning Tree","Omega(E log E)", "Theta(E log E)", "O(E log E)", "O(V)"),
    r"topological.?sort":      ("Topological Sort",     "Omega(V+E)", "Theta(V+E)", "O(V+E)", "O(V)"),

    # ── Dynamic Programming ──────────────────────────────────────────────
    r"knapsack":         ("0/1 Knapsack (DP)",   "Omega(nW)", "Theta(nW)",  "O(nW)",  "O(nW)"),
    r"longest.?common":  ("LCS (DP)",            "Omega(mn)", "Theta(mn)",  "O(mn)",  "O(mn)"),
    r"edit.?dist":       ("Edit Distance (DP)",  "Omega(mn)", "Theta(mn)",  "O(mn)",  "O(mn)"),
    r"coin.?change":     ("Coin Change (DP)",    "Omega(n)",  "Theta(n*k)", "O(n*k)", "O(n)"),

    # ── String ───────────────────────────────────────────────────────────
    r"\bkmp\b|knuth.?morris": ("KMP String Matching", "Omega(n)",   "Theta(n+m)", "O(n+m)", "O(m)"),
    r"rabin.?karp":           ("Rabin-Karp",           "Omega(n+m)", "Theta(n+m)", "O(nm)",  "O(1)"),

    # ── Classic Recursion ────────────────────────────────────────────────
    r"fibonacci":        ("Fibonacci",             "Omega(1)",    "Theta(2^n) or Theta(n)", "O(2^n) or O(n)", "O(n) or O(1)"),
    r"tower.?of.?hanoi": ("Tower of Hanoi",        "Omega(2^n)",  "Theta(2^n)",   "O(2^n)",  "O(n)"),
    r"factorial":        ("Factorial (recursive)", "Omega(n)",    "Theta(n)",     "O(n)",    "O(n)"),
}

# ─── Built-in / library call costs ───────────────────────────────────────────
BUILTIN_COSTS: dict[str, str] = {
    # Python builtins
    "sorted":     "O(n log n)",
    "sort":       "O(n log n)",
    "min":        "O(n)",
    "max":        "O(n)",
    "sum":        "O(n)",
    "len":        "O(1)",
    "append":     "O(1) amortized",
    "pop":        "O(1)",
    "insert":     "O(n)",
    "remove":     "O(n)",
    "index":      "O(n)",
    "count":      "O(n)",
    "reverse":    "O(n)",
    "enumerate":  "O(n)",
    "zip":        "O(n)",
    "map":        "O(n)",
    "filter":     "O(n)",
    "any":        "O(n)",
    "all":        "O(n)",
    "set":        "O(n)",
    "list":       "O(n)",
    "dict":       "O(n)",
    # Collections
    "bisect":          "O(log n)",
    "bisect_left":     "O(log n)",
    "bisect_right":    "O(log n)",
    "heapify":         "O(n)",
    "heappush":        "O(log n)",
    "heappop":         "O(log n)",
    "nlargest":        "O(n log k)",
    "nsmallest":       "O(n log k)",
    # C++ STL
    "lower_bound":     "O(log n)",
    "upper_bound":     "O(log n)",
    "binary_search":   "O(log n)",
    "find":            "O(n)",
    "push_back":       "O(1) amortized",
    "pop_back":        "O(1)",
    "push":            "O(log n)",
    "emplace":         "O(1) amortized",
    # Java
    "Arrays.sort":       "O(n log n)",
    "Collections.sort":  "O(n log n)",
    "HashMap.get":       "O(1) average",
    "HashMap.put":       "O(1) average",
    "TreeMap.get":       "O(log n)",
    "TreeMap.put":       "O(log n)",
    # JavaScript
    "Array.sort":       "O(n log n)",
    "Array.find":       "O(n)",
    "Array.filter":     "O(n)",
    "Array.map":        "O(n)",
    "Array.reduce":     "O(n)",
    "Array.includes":   "O(n)",
    "Array.indexOf":    "O(n)",
    "Set.has":          "O(1) average",
    "Map.get":          "O(1) average",
}
