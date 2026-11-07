# Algorithm Complexity Analyzer (AlienX)

AlienX is a desktop and command-line tool for exploring the time and auxiliary-space complexity of code snippets. It includes parsers and analysis rules for Python, C, C++, Java, JavaScript, and pseudocode.

> **Please review results critically.** This project uses static, heuristic analysis and pattern matching; it does not execute programs or prove complexity bounds. Results can be incomplete or incorrect, especially for unfamiliar code patterns.

## Features

- Interactive command-line analyzer and direct source-file mode
- CustomTkinter desktop interface with code editor and sample snippets
- Loop nesting, recursion, common algorithm patterns, and selected built-in operation analysis
- Best, average, worst, and auxiliary-space summaries
- Observations and optimization suggestions

## Quick start

From the repository root:

```bash
cd AlienX/complexity_analyzer
python -m venv .venv
```

Activate the virtual environment, then install dependencies:

```bash
# Windows PowerShell
.venv\\Scripts\\Activate.ps1

# macOS / Linux
source .venv/bin/activate

python -m pip install -r requirements.txt
```

Start the desktop app:

```bash
python app_gui.py
```

Or start the command-line interface:

```bash
python main.py
```

Analyze a file or pass code through standard input:

```bash
python main.py path/to/example.py
python main.py path/to/example.cpp --lang cpp
echo "for i in range(n): pass" | python main.py --stdin
```

## Project layout

```
AlienX/complexity_analyzer/
├── app_gui.py
├── main.py
├── requirements.txt
└── analyzer/
    ├── complexity.py
    ├── engine.py
    ├── formatter.py
    ├── knowledge.py
    ├── languages.py
    ├── observations.py
    └── parsers.py
```

For implementation notes and CLI commands, see the [analyzer README](AlienX/complexity_analyzer/README.md).
