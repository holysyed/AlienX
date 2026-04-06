# Algorithm Complexity Analyzer

A fully automated, expert-level **time and space complexity analyzer** for code snippets.
Paste any code and get a rich, step-by-step breakdown in the terminal.

---

## Features

| Feature | Details |
|---|---|
| **Languages** | Python, C, C++, Java, JavaScript, Pseudocode |
| **Loop analysis** | Depth-aware loop detection & nesting level |
| **Recursion** | Recurrence relation derivation + Master Theorem |
| **Known algorithms** | 30+ recognized patterns (sorting, searching, graph, DP, string) |
| **Built-in costs** | 40+ library/built-in call complexities |
| **Case analysis** | Best (Omega), Average (Theta), Worst (O), Space |
| **Observations** | Anti-pattern detection + optimization suggestions |
| **Interactive REPL** | Live multi-snippet analysis session |
| **File mode** | Analyze any source file directly |
| **Built-in demos** | 6 ready-to-run demo snippets |

---

## Quick Start

```bash
# Install the only runtime dependency
pip install rich

# Interactive mode (REPL)
python main.py

# Analyze a file directly
python main.py mybubble_sort.py

# Override language detection
python main.py code.py --lang cpp

# Pipe code via stdin
echo "for i in range(n): pass" | python main.py --stdin
```

---

## Interactive Commands

| Command | Description |
|---|---|
| `analyze` | Run analysis on the code you've pasted |
| `clear` | Discard current snippet and start fresh |
| `lang <x>` | Pin language: `python` `c` `cpp` `java` `js` `pseudo` |
| `demo` | Load one of 6 built-in demo snippets |
| `exit` | Quit |

---

## Analysis Pipeline

```
STEP 1: Code Breakdown
  - Identify all loops (for/while/do) and their nesting depth
  - Detect recursion and which functions recurse
  - Find conditional branches (if/else/switch)
  - Identify built-in / library operations and their known costs

STEP 2: Recurrence Relation (if recursive)
  - Build T(n) = a*T(n/b) + f(n)
  - Apply Master Theorem where applicable
  - Solve for exact complexity

STEP 3: Case Analysis
  - Best Case   : Omega(...)
  - Average Case: Theta(...)
  - Worst Case  : O(...)
  - Space       : O(...) auxiliary

STEP 4: Summary Table + Observations
  - One-line summary of all four cases
  - Anti-pattern flags (nested loops, O(2^n), sort-inside-loop, etc.)
  - Optimization suggestions
```

---

## Project Structure

```
complexity_analyzer/
    main.py                -- Entry point (interactive + file mode)
    requirements.txt       -- Only dependency: rich>=13.0
    analyzer/
        __init__.py
        engine.py          -- Main orchestration + interactive REPL
        languages.py       -- Language enum + auto-detection
        parsers.py         -- Python AST parser + generic regex parser
        complexity.py      -- Complexity deduction engine + Master Theorem
        knowledge.py       -- Known algorithms DB + built-in costs DB
        observations.py    -- Anti-pattern detector + suggestion generator
        formatter.py       -- Rich terminal output renderer
        demos.py           -- 6 built-in demo snippets
```

---

## Recognized Algorithms (auto-detected)

Bubble Sort, Selection Sort, Insertion Sort, Merge Sort, Quick Sort,
Heap Sort, Counting Sort, Radix Sort, Tim Sort, Shell Sort,
Binary Search, Linear Search, Jump Search, Interpolation Search,
BFS, DFS, Dijkstra, Bellman-Ford, Floyd-Warshall, MST (Prim/Kruskal),
Topological Sort, 0/1 Knapsack, LCS, Edit Distance, Coin Change,
KMP, Rabin-Karp, Fibonacci, Tower of Hanoi, Factorial.

---

## Example Output (Bubble Sort)

```
  CODE RECEIVED
  STEP 1 -- Code Breakdown
    [>>] Loops        : for-loop (depth 1), for-loop (depth 2)
    Max Nesting Depth : 2 level(s)
    [AI] Algorithm    : Bubble Sort

  STEP 3 -- Case Analysis
    Best Case    : Omega(n)      -- Best case for Bubble Sort
    Average Case : Theta(n^2)   -- Average case for Bubble Sort
    Worst Case   : O(n^2)       -- Worst case for Bubble Sort
    Space        : O(1)         -- Auxiliary space for Bubble Sort

  Observations:
    [OK]  Recognized algorithm: Bubble Sort
    [!!]  O(n^2) complexity -- becomes slow for n > 10,000
```
