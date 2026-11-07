# Algorithm Complexity Analyzer

A learning project that estimates time and auxiliary-space complexity for code snippets using static parsing, heuristics, and known algorithm patterns. It supports Python, C, C++, Java, JavaScript, and pseudocode.

**Limitations:** The analyzer does not execute code or prove complexity bounds. Its estimates may be incomplete or wrong when code uses patterns it does not recognize. Use the output as a learning aid and check the reasoning yourself.

## Setup

Run these commands from this directory:

```bash
python -m venv .venv
```

Activate the environment, then install dependencies:

```bash
# Windows PowerShell
.venv\\Scripts\\Activate.ps1

# macOS / Linux
source .venv/bin/activate

python -m pip install -r requirements.txt
```

## Run

Desktop interface:

```bash
python app_gui.py
```

Command-line interactive mode:

```bash
python main.py
```

Analyze a source file or standard input:

```bash
python main.py path/to/example.py
python main.py path/to/example.cpp --lang cpp
echo "for i in range(n): pass" | python main.py --stdin
```

## Included analysis

- Loop counts and nesting depth
- Recursion patterns and selected recurrence relations
- Common sorting, searching, graph, dynamic-programming, and string algorithms
- Best, average, worst, and auxiliary-space estimates
- Observations and optimization suggestions

The analysis is rule-based and supports a finite set of patterns. See the source in `analyzer/` to understand how each estimate is produced.
