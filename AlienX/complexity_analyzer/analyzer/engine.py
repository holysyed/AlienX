"""
analyzer/engine.py
───────────────────
Top-level AlgorithmAnalyzer class — wires all sub-modules together
and drives the interactive REPL.
"""

from __future__ import annotations

import time
from typing import Optional

from rich.console import Console
from rich.prompt  import Prompt

from .complexity    import ComplexityEngine
from .formatter     import OutputFormatter
from .languages     import Language, detect_language
from .observations  import generate_observations
from .parsers       import GenericParser, PythonParser
from .demos         import DEMOS, DEMO_MENU

console = Console()

LANG_MAP = {
    "python": Language.PYTHON, "py":   Language.PYTHON,
    "c":      Language.C,
    "cpp":    Language.CPP,    "c++":  Language.CPP,
    "java":   Language.JAVA,
    "js":     Language.JAVASCRIPT, "javascript": Language.JAVASCRIPT,
    "pseudo": Language.PSEUDOCODE,
}


class AlgorithmAnalyzer:
    """Orchestrates the full analysis pipeline."""

    def __init__(self) -> None:
        self.formatter   = OutputFormatter()
        self._complexity = ComplexityEngine()

    # ── Public API ────────────────────────────────────────────────────────────
    def analyze(self, code: str, language: Optional[Language] = None) -> None:
        """Run the full analysis and print the report."""
        if not code.strip():
            console.print("[yellow]No code to analyze.[/yellow]")
            return

        # Step 0 — language detection
        lang = language or detect_language(code)

        # Step 1 — parse
        with console.status("[bold cyan]Parsing code structure...[/bold cyan]", spinner="dots"):
            time.sleep(0.3)
            if lang == Language.PYTHON:
                parser = PythonParser()
                parse_data = parser.parse(code)
                if "parse_error" in parse_data:
                    console.print(
                        f"[yellow]⚠  Python parse error:[/yellow] {parse_data['parse_error']}\n"
                        "[dim]Falling back to generic regex analysis...[/dim]"
                    )
                    parse_data = GenericParser().parse(code, lang)
            else:
                parse_data = GenericParser().parse(code, lang)

        # Step 2 — deduce complexity
        with console.status("[bold cyan]Deducing complexity...[/bold cyan]", spinner="star"):
            time.sleep(0.3)
            result = self._complexity.deduce(parse_data, lang, code)

        # Step 3 — observations
        obs, sug = generate_observations(code, parse_data, result)

        # Step 4 — render
        self.formatter.print_analysis(code, lang, parse_data, result, obs, sug)

    # ── Interactive REPL ──────────────────────────────────────────────────────
    def run_interactive(self) -> None:
        self.formatter.print_usage()

        code_lines:   list[str]         = []
        language:     Optional[Language] = None

        console.print("[cyan]Enter code below (one line at a time). "
                      "Type [bold]analyze[/bold] when done:[/cyan]")
        console.print()

        while True:
            try:
                line = input()
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Goodbye! 👋[/dim]")
                break

            cmd = line.strip().lower()

            if cmd == "exit":
                console.print("[dim]Goodbye! Happy coding! 👋[/dim]")
                break

            elif cmd == "clear":
                code_lines = []
                language   = None
                console.print("[green]✓ Cleared.[/green] Enter new code:")

            elif cmd == "analyze":
                if not code_lines:
                    console.print("[yellow]No code entered yet. Paste code first.[/yellow]")
                else:
                    self.analyze("\n".join(code_lines), language)
                    code_lines = []
                    language   = None
                    console.print("[cyan]Enter next snippet (or type [bold]exit[/bold]):[/cyan]")

            elif cmd.startswith("lang"):
                parts = cmd.split()
                if len(parts) > 1 and parts[1] in LANG_MAP:
                    language = LANG_MAP[parts[1]]
                    console.print(f"[green]✓ Language pinned to:[/green] {language.value}")
                else:
                    console.print(
                        "[yellow]Usage:[/yellow] lang <python|c|cpp|java|js|pseudo>"
                    )

            elif cmd == "demo":
                console.print(DEMO_MENU, end="", markup=True)
                try:
                    choice = input().strip()
                except (EOFError, KeyboardInterrupt):
                    console.print()
                    continue
                if choice in DEMOS:
                    lang_key, demo_code = DEMOS[choice]
                    language = LANG_MAP[lang_key]
                    console.print(
                        f"\n[green]✓ Loaded demo [{choice}][/green] — analyzing...\n"
                    )
                    self.analyze(demo_code, language)
                    language = None
                else:
                    console.print("[dim]Cancelled.[/dim]")

            else:
                code_lines.append(line)
