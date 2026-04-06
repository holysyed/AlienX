#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Algorithm Complexity Analyzer  v1.0
=====================================
Expert time & space complexity analysis tool.
Supports: Python, C, C++, Java, JavaScript, Pseudocode

Usage:
  Interactive:   python main.py
  File mode:     python main.py mycode.py
  Piped stdin:   echo "for i in range(n): pass" | python main.py --stdin
  Override lang: python main.py code.py --lang cpp
"""

# ── Ensure UTF-8 output on Windows legacy terminals (before any Rich imports) ──
import os
import sys
import io

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "buffer") and sys.stdout.encoding and \
        sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer") and sys.stderr.encoding and \
        sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Bootstrap rich (install if missing) ──────────────────────────────────────
try:
    from rich.console import Console
except ImportError:
    import subprocess
    print("Installing 'rich' library (one-time setup)...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich"], check=True)
    print("Done! Starting analyzer...\n")
    from rich.console import Console

from analyzer.engine    import AlgorithmAnalyzer
from analyzer.languages import Language

console = Console()

# ─────────────────────────────────────────────────────────────────────────────
LANG_MAP = {
    "python": Language.PYTHON,  "py":          Language.PYTHON,
    "c":      Language.C,
    "cpp":    Language.CPP,     "c++":         Language.CPP,
    "java":   Language.JAVA,
    "js":     Language.JAVASCRIPT, "javascript": Language.JAVASCRIPT,
    "pseudo": Language.PSEUDOCODE,
}

EXT_MAP = {
    "py":   Language.PYTHON,
    "c":    Language.C,
    "cpp":  Language.CPP,
    "java": Language.JAVA,
    "js":   Language.JAVASCRIPT,
}


def main() -> None:
    app = AlgorithmAnalyzer()
    app.formatter.print_header()

    # ── CLI argument mode ─────────────────────────────────────────────────
    if len(sys.argv) > 1:
        import argparse
        import textwrap

        parser = argparse.ArgumentParser(
            prog="complexity_analyzer",
            description="Algorithm Complexity Analyzer -- time & space complexity analysis",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=textwrap.dedent("""\
                Examples:
                  python main.py bubble_sort.py
                  python main.py code.py --lang cpp
                  echo "for i in range(n): pass" | python main.py --stdin
            """),
        )
        parser.add_argument("file",    nargs="?",  help="Source file to analyze")
        parser.add_argument("--lang",  choices=list(LANG_MAP.keys()),
                            help="Override language detection")
        parser.add_argument("--stdin", action="store_true",
                            help="Read code from stdin")
        args = parser.parse_args()

        language = LANG_MAP.get(args.lang) if args.lang else None

        if args.stdin or not args.file:
            code = sys.stdin.read()
        else:
            try:
                with open(args.file, "r", encoding="utf-8") as fh:
                    code = fh.read()
                if not language:
                    ext = args.file.rsplit(".", 1)[-1].lower()
                    language = EXT_MAP.get(ext)
            except FileNotFoundError:
                console.print(f"[bold red]Error:[/bold red] File '{args.file}' not found.")
                sys.exit(1)

        app.analyze(code, language)

    # ── Interactive mode ──────────────────────────────────────────────────
    else:
        app.run_interactive()


if __name__ == "__main__":
    main()
