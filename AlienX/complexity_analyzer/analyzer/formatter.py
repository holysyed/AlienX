"""
analyzer/formatter.py
──────────────────────
Rich-powered terminal output formatter.
Produces the full analysis report in the prescribed layout.
"""

from __future__ import annotations

from typing import Any

from rich import box
from rich.align   import Align
from rich.console import Console
from rich.panel   import Panel
from rich.rule    import Rule
from rich.syntax  import Syntax
from rich.table   import Table
from rich.text    import Text

from .complexity import DeductionResult
from .languages  import Language
from .parsers    import ParseResult


import sys
import io

# Force UTF-8 on Windows legacy terminals so Rich box-drawing characters
# and any UTF-8 text in output don't hit cpXXXX codec errors.
if sys.stdout.encoding and sys.stdout.encoding.lower() in ("cp1252", "cp850", "cp437", "ascii"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

console = Console(highlight=False)



class OutputFormatter:

    # ── Public interface ──────────────────────────────────────────────────────
    def print_header(self) -> None:
        console.print()
        header = Panel(
            Align.center(
                Text.from_markup(
                    "[bold bright_cyan]*** Algorithm Complexity Analyzer ***[/bold bright_cyan]\n"
                    "[dim]Expert time & space complexity analysis tool[/dim]\n"
                    "[dim]Python | C | C++ | Java | JavaScript | Pseudocode[/dim]"
                )
            ),
            box=box.DOUBLE_EDGE,
            style="bright_cyan",
            padding=(1, 6),
        )
        console.print(header)
        console.print()

    def print_usage(self) -> None:
        console.print("[bold bright_cyan]Welcome![/bold bright_cyan]  Paste your code snippet and type [bold]analyze[/bold] when done.\n")
        t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        t.add_column("cmd",  style="bold yellow", width=12)
        t.add_column("desc", style="white")
        t.add_row("analyze",  "Run analysis on the entered code")
        t.add_row("clear",    "Discard current snippet and start fresh")
        t.add_row("lang <x>", "Override language  python|c|cpp|java|js|pseudo")
        t.add_row("demo",     "Load a built-in demo snippet")
        t.add_row("exit",     "Quit the program")
        console.print(t)
        console.print()

    def print_analysis(
        self,
        code:    str,
        lang:    Language,
        parse:   ParseResult,
        result:  DeductionResult,
        obs:     list[str],
        sug:     list[str],
    ) -> None:
        lang_name = lang.value.upper()

        # ── Code Received ──────────────────────────────────────────────────
        console.print(Rule("[bold blue]  CODE RECEIVED[/bold blue]", style="blue"))
        console.print()
        syntax = Syntax(code, lang.value, theme="monokai",
                        line_numbers=True, background_color="default")
        console.print(Panel(syntax,
                            title=f"[bold]{lang_name} Snippet[/bold]",
                            border_style="blue", padding=(0, 1)))
        desc = self._code_description(parse, result, lang)
        console.print(Panel(f"[italic]{desc}[/italic]",
                            title="[dim]Description[/dim]",
                            border_style="dim", padding=(0, 1)))
        console.print()

        # ── Step 1: Code Breakdown ─────────────────────────────────────────
        console.print(Rule("[bold yellow]  STEP 1 -- Code Breakdown[/bold yellow]", style="yellow"))
        console.print()
        console.print(self._breakdown_table(parse, result))
        console.print()

        # ── Step 2: Recurrence Relation ────────────────────────────────────
        rec = result.recurrence
        if rec:
            console.print(Rule("[bold magenta]  STEP 2 -- Recurrence Relation[/bold magenta]", style="magenta"))
            console.print()
            body = Text()
            body.append("  Relation  :  ", style="dim")
            body.append(f"{rec.relation}\n", style="bold white")
            if rec.master_case:
                body.append("  Theorem   :  ", style="dim")
                body.append(f"{rec.master_case}\n", style="cyan")
            body.append("  Solution  :  ", style="dim")
            body.append(f"{rec.solution}", style="bold green")
            console.print(Panel(body,
                                title="[bold magenta]Recurrence Analysis[/bold magenta]",
                                border_style="magenta", padding=(1, 2)))
            console.print()

        # ── Step 3: Case Analysis ──────────────────────────────────────────
        console.print(Rule("[bold green]  STEP 3 -- Case Analysis[/bold green]", style="green"))
        console.print()

        cases = [
            ("Best Case",    "Omega (Best)",   result.best_case,    "green"),
            ("Average Case", "Theta (Average)", result.average_case, "blue"),
            ("Worst Case",   "O     (Worst)",   result.worst_case,   "red"),
        ]
        for label, notation, comp, color in cases:
            if comp is None:
                continue
            body = Text()
            body.append("  Notation  :  ", style="dim")
            body.append(f"{notation}\n", style="dim")
            body.append("  Result    :  ", style="dim")
            body.append(f"{comp.notation}\n", style=f"bold {color}")
            body.append("  Reason    :  ", style="dim")
            body.append(comp.explanation, style="white")
            console.print(Panel(body,
                                title=f"[bold {color}]{label}[/bold {color}]",
                                border_style=color, padding=(0, 2)))

        # Space
        body = Text()
        body.append("  Result    :  ", style="dim")
        body.append(f"{result.space.notation}\n", style="bold cyan")
        body.append("  Reason    :  ", style="dim")
        body.append(result.space.explanation, style="white")
        console.print(Panel(body,
                            title="[bold cyan]  Space Complexity (Auxiliary)[/bold cyan]",
                            border_style="cyan", padding=(0, 2)))
        console.print()

        # ── Step 4: Summary Table ──────────────────────────────────────────
        console.print(Rule("[bold white]  STEP 4 -- Summary Table[/bold white]", style="white"))
        console.print()
        console.print(self._summary_table(result))
        console.print()

        # ── Observations & Suggestions ─────────────────────────────────────
        console.print(Rule("[bold yellow]  Observations & Suggestions[/bold yellow]", style="yellow"))
        console.print()
        if obs:
            obs_text = "\n".join(obs)
            console.print(Panel(obs_text,
                                title="[bold]Observations[/bold]",
                                border_style="yellow", padding=(0, 1)))
        if sug:
            sug_text = "\n".join(f"->  {s}" for s in sug)
            console.print(Panel(sug_text,
                                title="[bold green]Optimization Suggestions[/bold green]",
                                border_style="green", padding=(0, 1)))
        if not obs and not sug:
            console.print("[dim]No additional observations.[/dim]")
        console.print()
        console.print(Rule(style="dim"))
        console.print()

    # ── Private helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _code_description(parse: ParseResult, result: DeductionResult, lang: Language) -> str:
        loops    = parse.get("loops", [])
        nesting  = parse.get("max_nesting", 0)
        has_rec  = parse.get("has_recursion", False)
        lang_str = lang.value.capitalize()

        if result.known_algorithm:
            return (
                f"This {lang_str} snippet implements "
                f"[bold]{result.known_algorithm}[/bold]."
            )
        if has_rec and loops:
            return (
                f"This {lang_str} function is [bold]recursive[/bold] and also contains "
                f"{len(loops)} loop(s) with max nesting depth {nesting}."
            )
        if has_rec:
            funcs = parse.get("recursive_funcs", [])
            return (
                f"This {lang_str} function ([italic]{', '.join(funcs)}[/italic]) "
                f"calls itself [bold]recursively[/bold]."
            )
        if not loops:
            return (
                f"This {lang_str} snippet contains no loops -- "
                f"likely a constant-time (O(1)) sequence of operations."
            )
        return (
            f"This {lang_str} snippet has [bold]{len(loops)}[/bold] loop(s) "
            f"with a maximum nesting depth of [bold]{nesting}[/bold]."
        )

    @staticmethod
    def _breakdown_table(parse: ParseResult, result: DeductionResult) -> Table:
        t = Table(show_header=True, header_style="bold yellow",
                  box=box.ROUNDED, border_style="yellow", padding=(0, 1))
        t.add_column("Component",  style="bold", width=24)
        t.add_column("Details",    style="white")

        # Loops
        loops = parse.get("loops", [])
        loop_str = "\n".join(f"+ {l}" for l in loops) if loops else "[dim]None[/dim]"
        t.add_row("[>>] Loops", loop_str)

        # Nesting depth
        nd = parse.get("max_nesting", 0)
        color = "green" if nd <= 1 else ("yellow" if nd == 2 else "red")
        t.add_row("Max Nesting Depth", f"[{color}]{nd} level(s)[/{color}]")

        # Recursion
        if parse.get("has_recursion"):
            funcs = ", ".join(parse.get("recursive_funcs", []))
            t.add_row("[<<] Recursion", f"[magenta]Yes -- {funcs}[/magenta]")
        else:
            t.add_row("[<<] Recursion", "[green]None detected[/green]")

        # Conditionals
        conds = parse.get("conditionals", [])
        if conds:
            cond_str = "\n".join(f"+ {c}" for c in conds[:6])
            if len(conds) > 6:
                cond_str += f"\n  ... and {len(conds)-6} more"
            t.add_row("[??] Conditionals", cond_str)
        else:
            t.add_row("[??] Conditionals", "[dim]None[/dim]")

        # Built-in calls
        calls = parse.get("builtin_calls", [])
        if calls:
            call_str = "\n".join(f"+ {n}()  ->  {c}" for n, c in calls)
            t.add_row("[LIB] Built-in Calls", call_str)
        else:
            t.add_row("[LIB] Built-in Calls", "[dim]None detected[/dim]")

        # Data structures
        ds = parse.get("data_structures", [])
        if ds:
            t.add_row("[DS]  Data Structures", ", ".join(set(ds)))

        # Functions
        funcs_list = parse.get("functions", [])
        if funcs_list:
            t.add_row("[fn]  Functions", ", ".join(funcs_list[:8]))

        # Detected algorithm
        if result.known_algorithm:
            t.add_row("[AI]  Algorithm Detected",
                      f"[bold bright_cyan]{result.known_algorithm}[/bold bright_cyan]")

        return t

    @staticmethod
    def _summary_table(result: DeductionResult) -> Table:
        t = Table(show_header=True, header_style="bold white",
                  box=box.DOUBLE_EDGE, border_style="white", padding=(0, 2))
        t.add_column("Case",       justify="center", style="bold",  width=16)
        t.add_column("Notation",   justify="center",                width=12)
        t.add_column("Complexity", justify="center",                width=16)
        t.add_column("Reason",                                       width=42)

        rows = [
            ("Best Case",    "Omega(...)", result.best_case,    "green"),
            ("Average Case", "Theta(...)", result.average_case, "blue"),
            ("Worst Case",   "O(...)",     result.worst_case,   "red"),
            ("Space",        "O(...)",     result.space,        "cyan"),
        ]
        for label, notation, comp, color in rows:
            if comp is None:
                continue
            reason = comp.explanation
            if len(reason) > 55:
                reason = reason[:52] + "..."
            t.add_row(
                f"[{color}]{label}[/{color}]",
                f"[dim]{notation}[/dim]",
                f"[bold {color}]{comp.notation}[/bold {color}]",
                reason,
            )
        return t
