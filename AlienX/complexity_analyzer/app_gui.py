#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app_gui.py  --  Algorithm Complexity Analyzer: Desktop GUI
==========================================================
A premium CustomTkinter desktop interface for the complexity analyzer.

Run:   python app_gui.py
"""

import sys, os, threading, re, tkinter as tk
from tkinter import filedialog

# ── Ensure analyzer package is importable ──────────────────────
sys.path.insert(0, os.path.dirname(__file__))

import customtkinter as ctk
from analyzer.complexity   import ComplexityEngine, DeductionResult, Complexity
from analyzer.languages    import Language, detect_language
from analyzer.parsers      import PythonParser, GenericParser, ParseResult
from analyzer.observations import generate_observations
from analyzer.demos        import DEMOS

# ═══════════════════════════════════════════════════════════════
#  Design Tokens
# ═══════════════════════════════════════════════════════════════
class T:
    """Design tokens (dark palette)."""
    BG        = "#0c0d12"
    BG2       = "#10121a"
    BG3       = "#161923"
    SURFACE   = "#1a1e2c"
    SURFACE2  = "#222840"
    BORDER    = "#282e44"
    BORDER2   = "#353d5c"

    TEXT      = "#e6e8f0"
    TEXT2     = "#9299b8"
    TEXT3     = "#5c6488"

    INDIGO    = "#6366f1"
    VIOLET    = "#8b5cf6"
    CYAN      = "#22d3ee"
    EMERALD   = "#34d399"
    AMBER     = "#f59e0b"
    ROSE      = "#f43f5e"
    ORANGE    = "#fb923c"
    BLUE      = "#3b82f6"

    FONT      = ("Segoe UI", 13)
    FONT_SM   = ("Segoe UI", 11)
    FONT_XS   = ("Segoe UI", 10)
    FONT_LG   = ("Segoe UI", 18, "bold")
    FONT_XL   = ("Segoe UI", 24, "bold")
    MONO      = ("Consolas", 13)
    MONO_SM   = ("Consolas", 11)
    MONO_LG   = ("Consolas", 16, "bold")
    TITLE     = ("Segoe UI", 14, "bold")

LANG_MAP = {
    "python": Language.PYTHON,  "c": Language.C, "cpp": Language.CPP,
    "java": Language.JAVA, "javascript": Language.JAVASCRIPT,
    "pseudocode": Language.PSEUDOCODE,
}

DEMO_META = {
    "1": ("Bubble Sort",      "O(n^2)",      "python"),
    "2": ("Binary Search",    "O(log n)",     "python"),
    "3": ("Merge Sort",       "O(n log n)",   "python"),
    "4": ("Fibonacci (naive)","O(2^n)",       "python"),
    "5": ("Triple Sum",       "O(n^3)",       "python"),
    "6": ("Quick Sort (C++)", "O(n^2) worst", "cpp"),
}


def complexity_rank(notation: str) -> int:
    n = notation.lower()
    if "n!" in n:        return 10
    if "2^n" in n:       return 9
    if "n^3" in n:       return 8
    if "n^2" in n:       return 7
    if "n log n" in n:   return 6
    if n in ("o(n)",):   return 5
    if "sqrt" in n:      return 4
    if "log n" in n:     return 3
    if "log" in n:       return 2
    if "1" in n:         return 1
    return 5

def rank_color(rank: int) -> str:
    if rank <= 2:  return T.EMERALD
    if rank <= 4:  return T.CYAN
    if rank <= 6:  return T.AMBER
    if rank <= 8:  return T.ORANGE
    return T.ROSE


# ═══════════════════════════════════════════════════════════════
#  Reusable Widget Factories
# ═══════════════════════════════════════════════════════════════
def card_frame(parent, **kw) -> ctk.CTkFrame:
    """Create a surface card with rounded corners."""
    return ctk.CTkFrame(
        parent,
        fg_color=T.SURFACE,
        corner_radius=14,
        border_width=1,
        border_color=T.BORDER,
        **kw,
    )

def section_label(parent, text, color=T.INDIGO) -> ctk.CTkLabel:
    """Small uppercase section label, like a tag."""
    return ctk.CTkLabel(
        parent, text=text.upper(),
        font=("Segoe UI", 9, "bold"),
        text_color=color,
        fg_color=_alpha(color, 0.15),
        corner_radius=4,
        padx=8, pady=2,
    )

def _alpha(hex_color: str, opacity: float) -> str:
    """Darken a hex color by mixing with the background."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    br, bg, bb = 0x0c, 0x0d, 0x12
    nr = int(br + (r - br) * opacity)
    ng = int(bg + (g - bg) * opacity)
    nb = int(bb + (b - bb) * opacity)
    return f"#{nr:02x}{ng:02x}{nb:02x}"


# ═══════════════════════════════════════════════════════════════
#  Main Application
# ═══════════════════════════════════════════════════════════════
class ComplexityApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AlienX")
        self.geometry("1340x820")
        self.minsize(960, 600)
        self.configure(fg_color=T.BG)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._engine = ComplexityEngine()
        self._build_ui()
        self._load_demos()

    # ──────────────────────────────────────────────────────────
    #  UI Construction
    # ──────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=T.BG2, corner_radius=0, height=56)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Brand icon
        icon_frame = ctk.CTkFrame(header, fg_color=T.INDIGO, corner_radius=10,
                                  width=36, height=36)
        icon_frame.pack(side="left", padx=(20, 10), pady=10)
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text="⚡", font=("Segoe UI", 16),
                     text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", pady=8)
        ctk.CTkLabel(title_frame, text="Time Complexity Analyzer",
                     font=("Segoe UI", 15, "bold"), text_color=T.TEXT,
                     anchor="w").pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Expert algorithm analysis tool",
                     font=("Segoe UI", 10), text_color=T.TEXT3,
                     anchor="w").pack(anchor="w")

        # Header right: Open file button
        ctk.CTkButton(
            header, text="Open File", width=90, height=32,
            font=("Segoe UI", 11), fg_color=T.SURFACE2,
            hover_color=T.BORDER2, corner_radius=8,
            command=self._open_file,
        ).pack(side="right", padx=20, pady=12)

        # ── Main split container ────────────────────────────
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=0, pady=0)
        main.columnconfigure(0, weight=4, minsize=380)
        main.columnconfigure(1, weight=7, minsize=480)
        main.rowconfigure(0, weight=1)

        # ── LEFT PANEL ──────────────────────────────────────
        left = ctk.CTkFrame(main, fg_color=T.BG, corner_radius=0,
                            border_width=0)
        left.grid(row=0, column=0, sticky="nsew")

        # Divider line
        divider = ctk.CTkFrame(main, fg_color=T.BORDER, width=1, corner_radius=0)
        divider.grid(row=0, column=0, sticky="nse")

        self._build_left_panel(left)

        # ── RIGHT PANEL ─────────────────────────────────────
        right = ctk.CTkFrame(main, fg_color=T.BG, corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        self._build_right_panel(right)

    # ── LEFT PANEL ───────────────────────────────────────────
    def _build_left_panel(self, parent):
        # ── Demo chips (pack FIRST from bottom so they never get clipped) ──
        demo_frame = ctk.CTkFrame(parent, fg_color="transparent")
        demo_frame.pack(side="bottom", fill="x", padx=16, pady=(2, 14))

        ctk.CTkLabel(demo_frame, text="Examples:",
                     font=("Segoe UI", 10), text_color=T.TEXT3
                     ).pack(side="left", padx=(0, 6))

        self._demo_frame = ctk.CTkFrame(demo_frame, fg_color="transparent")
        self._demo_frame.pack(side="left", fill="x")

        # ── Analyze button (pack from bottom, above demos) ───
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=16, pady=(4, 4))

        self.analyze_btn = ctk.CTkButton(
            btn_frame, text="   Analyze   ", height=44,
            font=("Segoe UI", 14, "bold"),
            fg_color=T.INDIGO, hover_color=T.VIOLET,
            corner_radius=10,
            command=self._run_analysis,
        )
        self.analyze_btn.pack(fill="x")

        ctk.CTkLabel(btn_frame, text="Ctrl+Enter",
                     font=("Segoe UI", 9), text_color=T.TEXT3
                     ).pack(pady=(3, 0))

        self.bind_all("<Control-Return>", lambda e: self._run_analysis())

        # ── Toolbar (pack from top) ─────────────────────────
        toolbar = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        toolbar.pack(side="top", fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(toolbar, text="CODE INPUT", font=("Segoe UI", 9, "bold"),
                     text_color=T.TEXT3).pack(side="left")

        # Language selector
        self._lang_var = ctk.StringVar(value="Auto-detect")
        lang_menu = ctk.CTkOptionMenu(
            toolbar, variable=self._lang_var,
            values=["Auto-detect", "Python", "C", "C++", "Java", "JavaScript", "Pseudocode"],
            width=130, height=30, font=("Segoe UI", 11),
            fg_color=T.SURFACE, button_color=T.SURFACE2,
            button_hover_color=T.BORDER2,
            dropdown_fg_color=T.SURFACE2,
            dropdown_hover_color=T.BORDER2,
            corner_radius=8,
        )
        lang_menu.pack(side="right")

        # Clear button
        ctk.CTkButton(
            toolbar, text="Clear", width=56, height=30,
            font=("Segoe UI", 11), fg_color=T.SURFACE,
            hover_color=_alpha(T.ROSE, 0.2), text_color=T.TEXT2,
            corner_radius=8, command=self._clear_editor,
        ).pack(side="right", padx=(0, 8))

        # ── Code editor (fills remaining space) ──────────────
        editor_border = ctk.CTkFrame(parent, fg_color=T.BORDER, corner_radius=14)
        editor_border.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        editor_inner = ctk.CTkFrame(editor_border, fg_color=T.SURFACE,
                                    corner_radius=12)
        editor_inner.pack(fill="both", expand=True, padx=1, pady=1)

        self.editor = tk.Text(
            editor_inner, wrap="none",
            bg="#181c2a", fg="#e0e4f0",
            insertbackground=T.INDIGO,
            selectbackground=_alpha(T.INDIGO, 0.35),
            selectforeground=T.TEXT,
            font=("Consolas", 13),
            relief="flat", bd=0, padx=16, pady=14,
            undo=True, maxundo=-1,
            highlightthickness=0,
            height=1,
        )
        self.editor.pack(fill="both", expand=True)

        self.editor.insert("1.0", self._default_code())
        self.editor.bind("<KeyRelease>", self._on_editor_key)
        self._apply_syntax_tags()

        # Scrollbar
        scrollbar = ctk.CTkScrollbar(editor_inner, command=self.editor.yview,
                                     fg_color="transparent",
                                     button_color=T.BORDER2)
        scrollbar.pack(side="right", fill="y", pady=4)
        self.editor.configure(yscrollcommand=scrollbar.set)

    # ── RIGHT PANEL ──────────────────────────────────────────
    def _build_right_panel(self, parent):
        # Scrollable container for results
        self._results_scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=T.BORDER2,
            scrollbar_button_hover_color=T.TEXT3,
        )
        self._results_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        self._results_container = self._results_scroll

        # Empty state
        self._empty_frame = ctk.CTkFrame(self._results_container,
                                         fg_color="transparent")
        self._empty_frame.pack(fill="both", expand=True, pady=100)

        ctk.CTkLabel(self._empty_frame, text="Ready to Analyze",
                     font=("Segoe UI", 22, "bold"),
                     text_color=T.TEXT).pack(pady=(40, 6))
        ctk.CTkLabel(self._empty_frame,
                     text="Paste code on the left and click Analyze,\nor pick an example to get started.",
                     font=("Segoe UI", 12), text_color=T.TEXT3,
                     justify="center").pack()

    # ──────────────────────────────────────────────────────────
    #  Actions
    # ──────────────────────────────────────────────────────────
    def _default_code(self):
        return """def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr"""

    def _clear_editor(self):
        self.editor.delete("1.0", "end")
        self.editor.focus_set()

    def _open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("All Code Files", "*.py *.c *.cpp *.h *.java *.js"),
                ("Python", "*.py"), ("C/C++", "*.c *.cpp *.h"),
                ("Java", "*.java"), ("JavaScript", "*.js"),
                ("All Files", "*.*"),
            ]
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    code = f.read()
                self.editor.delete("1.0", "end")
                self.editor.insert("1.0", code)
                self._apply_syntax_tags()
            except Exception as e:
                self._show_error(str(e))

    def _load_demos(self):
        colors = {
            "1": T.ROSE,   "2": T.EMERALD, "3": T.AMBER,
            "4": T.VIOLET, "5": T.ORANGE,  "6": T.BLUE,
        }
        for key, (name, cplx, lang) in DEMO_META.items():
            color = colors.get(key, T.TEXT2)
            btn = ctk.CTkButton(
                self._demo_frame,
                text=f"{name}",
                width=0, height=26,
                font=("Segoe UI", 10),
                fg_color=_alpha(color, 0.15),
                hover_color=_alpha(color, 0.3),
                text_color=color,
                border_width=1, border_color=_alpha(color, 0.25),
                corner_radius=50,
                command=lambda k=key: self._load_demo(k),
            )
            btn.pack(side="left", padx=2)

    def _load_demo(self, key):
        if key in DEMOS:
            lang_key, code = DEMOS[key]
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", code.strip())
            self._apply_syntax_tags()
            # Set language
            lang_names = {
                "python": "Python", "c": "C", "cpp": "C++",
                "java": "Java", "javascript": "JavaScript",
                "pseudocode": "Pseudocode",
            }
            self._lang_var.set(lang_names.get(lang_key, "Auto-detect"))
            self._run_analysis()

    def _resolve_language(self, code):
        lv = self._lang_var.get().lower().replace("++", "pp")
        if lv in LANG_MAP:
            return LANG_MAP[lv]
        return detect_language(code)

    # ──────────────────────────────────────────────────────────
    #  Analysis Pipeline
    # ──────────────────────────────────────────────────────────
    def _run_analysis(self):
        code = self.editor.get("1.0", "end-1c").strip()
        if not code:
            return

        self.analyze_btn.configure(state="disabled", text="Analyzing...")

        # Run in a thread to keep UI responsive
        def worker():
            try:
                lang = self._resolve_language(code)

                if lang == Language.PYTHON:
                    parser = PythonParser()
                    parse_data = parser.parse(code)
                    if "parse_error" in parse_data:
                        parse_data = GenericParser().parse(code, lang)
                else:
                    parse_data = GenericParser().parse(code, lang)

                result = self._engine.deduce(parse_data, lang, code)
                obs, sug = generate_observations(code, parse_data, result)

                self.after(0, lambda: self._render_results(
                    lang, parse_data, result, obs, sug))
            except Exception as e:
                self.after(0, lambda: self._show_error(str(e)))
            finally:
                self.after(0, lambda: self.analyze_btn.configure(
                    state="normal", text="   Analyze   "))

        threading.Thread(target=worker, daemon=True).start()

    # ──────────────────────────────────────────────────────────
    #  Result Rendering
    # ──────────────────────────────────────────────────────────
    def _clear_results(self):
        for w in self._results_container.winfo_children():
            w.destroy()

    def _show_error(self, msg):
        self._clear_results()
        card = card_frame(self._results_container)
        card.pack(fill="x", padx=16, pady=60)
        ctk.CTkLabel(card, text="Error", font=T.TITLE,
                     text_color=T.ROSE).pack(padx=20, pady=(16, 4))
        ctk.CTkLabel(card, text=msg, font=T.FONT_SM,
                     text_color=T.TEXT2, wraplength=400).pack(padx=20, pady=(0, 16))

    def _render_results(self, lang, parse_data, result: DeductionResult,
                        obs, sug):
        self._clear_results()
        container = self._results_container

        # ── 1) Header card (language + algorithm) ────────────
        self._render_header(container, lang, result)

        # ── 2) Complexity overview meter ─────────────────────
        self._render_meter(container, result)

        # ── 3) Four case cards ───────────────────────────────
        self._render_case_cards(container, result)

        # ── 4) Code Breakdown ────────────────────────────────
        self._render_breakdown(container, parse_data, result)

        # ── 5) Recurrence (if recursive) ─────────────────────
        if result.recurrence:
            self._render_recurrence(container, result.recurrence)

        # ── 6) Observations & Suggestions ────────────────────
        self._render_observations(container, obs, sug)

    # ── Header ───────────────────────────────────────────────
    def _render_header(self, parent, lang, result):
        card = card_frame(parent)
        card.pack(fill="x", padx=16, pady=(14, 6))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)

        # Language badge
        lang_colors = {
            "python": T.BLUE, "cpp": T.ORANGE, "c": T.ORANGE,
            "java": T.ROSE, "javascript": T.AMBER, "pseudocode": T.TEXT2,
        }
        lc = lang_colors.get(lang.value, T.INDIGO)
        badge = ctk.CTkLabel(
            row, text=lang.value.upper(),
            font=("Segoe UI", 9, "bold"), text_color=lc,
            fg_color=_alpha(lc, 0.15), corner_radius=6,
            padx=10, pady=4,
        )
        badge.pack(side="left", padx=(0, 12))

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        if result.known_algorithm:
            ctk.CTkLabel(info, text=result.known_algorithm,
                         font=("Segoe UI", 16, "bold"),
                         text_color=T.TEXT, anchor="w").pack(anchor="w")

        desc = self._make_desc(lang, parse_data=None, result=result)
        ctk.CTkLabel(info, text=desc, font=T.FONT_SM,
                     text_color=T.TEXT2, anchor="w").pack(anchor="w")

    def _make_desc(self, lang, parse_data, result):
        l = lang.value.capitalize()
        if result.known_algorithm:
            return f"This {l} snippet implements {result.known_algorithm}."
        return f"Analysis complete for {l} code."

    # ── Complexity Meter ─────────────────────────────────────
    def _render_meter(self, parent, result):
        card = card_frame(parent)
        card.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(card, text="COMPLEXITY OVERVIEW",
                     font=("Segoe UI", 9, "bold"), text_color=T.TEXT3
                     ).pack(pady=(14, 8))

        rank = complexity_rank(result.worst_case.notation)
        pct = min(1.0, rank / 10.0)
        color = rank_color(rank)

        # Meter bar
        meter_bg = ctk.CTkFrame(card, fg_color=T.BG3, corner_radius=6,
                                height=10)
        meter_bg.pack(fill="x", padx=24, pady=(0, 12))
        meter_bg.pack_propagate(False)

        meter_fill = ctk.CTkFrame(meter_bg, fg_color=color, corner_radius=6,
                                  height=10)
        meter_fill.place(relx=0, rely=0, relwidth=pct, relheight=1.0)

        # Values row
        vals = ctk.CTkFrame(card, fg_color="transparent")
        vals.pack(fill="x", padx=20, pady=(0, 14))
        vals.columnconfigure((0, 1, 2, 3), weight=1)

        items = [
            ("Best",    result.best_case,    T.EMERALD),
            ("Average", result.average_case, T.AMBER),
            ("Worst",   result.worst_case,   T.ROSE),
            ("Space",   result.space,        T.CYAN),
        ]
        for col, (label, comp, clr) in enumerate(items):
            cell = ctk.CTkFrame(vals, fg_color="transparent")
            cell.grid(row=0, column=col, sticky="nsew", padx=4)
            ctk.CTkLabel(cell, text=label, font=("Segoe UI", 9),
                         text_color=T.TEXT3).pack()
            notation = comp.notation if comp else "--"
            ctk.CTkLabel(cell, text=notation, font=("Consolas", 12, "bold"),
                         text_color=clr).pack()

    # ── Four Case Cards ──────────────────────────────────────
    def _render_case_cards(self, parent, result):
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=6)
        grid.columnconfigure((0, 1), weight=1, uniform="case")

        cases = [
            ("BEST CASE",    "Omega", result.best_case,    T.EMERALD),
            ("AVERAGE CASE", "Theta", result.average_case, T.AMBER),
            ("WORST CASE",   "Big-O", result.worst_case,   T.ROSE),
            ("SPACE",        "Aux",   result.space,        T.CYAN),
        ]
        for i, (label, notation_label, comp, color) in enumerate(cases):
            r, c = divmod(i, 2)
            self._case_card(grid, label, notation_label, comp, color, r, c)

    def _case_card(self, parent, label, notation_label, comp, color, row, col):
        card = ctk.CTkFrame(
            parent, fg_color=T.SURFACE, corner_radius=12,
            border_width=1, border_color=_alpha(color, 0.25),
        )
        card.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 4))

        # Label badge
        ctk.CTkLabel(
            top, text=label, font=("Segoe UI", 8, "bold"),
            text_color=color, fg_color=_alpha(color, 0.15),
            corner_radius=4, padx=8, pady=2,
        ).pack(side="left")

        # Notation label
        ctk.CTkLabel(
            top, text=notation_label, font=("Consolas", 9),
            text_color=T.TEXT3,
        ).pack(side="right")

        # Big complexity value
        notation = comp.notation if comp else "--"
        ctk.CTkLabel(
            card, text=notation,
            font=("Consolas", 18, "bold"), text_color=color,
            anchor="w",
        ).pack(padx=14, pady=(2, 2), anchor="w")

        # Explanation
        explanation = comp.explanation if comp else ""
        ctk.CTkLabel(
            card, text=explanation, font=("Segoe UI", 10),
            text_color=T.TEXT3, anchor="w", wraplength=320,
        ).pack(padx=14, pady=(0, 12), anchor="w")

    # ── Breakdown ────────────────────────────────────────────
    def _render_breakdown(self, parent, parse_data, result):
        card = card_frame(parent)
        card.pack(fill="x", padx=16, pady=6)

        # Header
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 8))
        section_label(hdr, "Step 1", T.INDIGO).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(hdr, text="Code Breakdown", font=T.TITLE,
                     text_color=T.TEXT).pack(side="left")

        # Grid of breakdown items
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 14))
        grid.columnconfigure((0, 1), weight=1)

        items = self._breakdown_items(parse_data, result)
        for i, (key, val, tag_color) in enumerate(items):
            r, c = divmod(i, 2)
            cell = ctk.CTkFrame(grid, fg_color=T.BG3, corner_radius=10)
            cell.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)
            ctk.CTkLabel(cell, text=key.upper(),
                         font=("Segoe UI", 8, "bold"),
                         text_color=T.TEXT3, anchor="w").pack(
                             padx=12, pady=(10, 2), anchor="w")
            ctk.CTkLabel(cell, text=val, font=("Consolas", 11),
                         text_color=tag_color, anchor="w",
                         wraplength=320).pack(
                             padx=12, pady=(0, 10), anchor="w")

    def _breakdown_items(self, pd, result):
        loops = pd.get("loops", [])
        nd = pd.get("max_nesting", 0)
        has_rec = pd.get("has_recursion", False)
        rec_funcs = pd.get("recursive_funcs", [])
        calls = pd.get("builtin_calls", [])
        conds = pd.get("conditionals", [])
        funcs = pd.get("functions", [])

        nd_color = T.EMERALD if nd <= 1 else (T.AMBER if nd == 2 else T.ROSE)

        items = [
            ("Loops", f"{len(loops)} loop(s)" if loops else "None",
             T.AMBER if loops else T.TEXT3),
            ("Max Nesting", f"Depth {nd}",
             nd_color),
            ("Recursion",
             ", ".join(rec_funcs) if has_rec else "None",
             T.VIOLET if has_rec else T.TEXT3),
            ("Conditionals",
             f"{len(conds)} branch(es)" if conds else "None",
             T.INDIGO if conds else T.TEXT3),
            ("Built-in Calls",
             ", ".join(f"{n}() {c}" for n, c in calls[:3]) if calls else "None",
             T.CYAN if calls else T.TEXT3),
            ("Functions",
             ", ".join(funcs[:5]) if funcs else "-- ",
             T.EMERALD if funcs else T.TEXT3),
        ]

        if result.known_algorithm:
            items.append(
                ("Algorithm Detected", result.known_algorithm, T.VIOLET)
            )
            items.append(
                ("Data Structures",
                 ", ".join(set(pd.get("data_structures", []))) or "None",
                 T.CYAN if pd.get("data_structures") else T.TEXT3)
            )
        else:
            items.append(
                ("Data Structures",
                 ", ".join(set(pd.get("data_structures", []))) or "None",
                 T.CYAN if pd.get("data_structures") else T.TEXT3)
            )
            # Keep it even
            items.append(("Algorithm", "Not recognized", T.TEXT3))

        return items

    # ── Recurrence ───────────────────────────────────────────
    def _render_recurrence(self, parent, rec):
        card = card_frame(parent)
        card.pack(fill="x", padx=16, pady=6)

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 8))
        section_label(hdr, "Step 2", T.VIOLET).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(hdr, text="Recurrence Relation", font=T.TITLE,
                     text_color=T.TEXT).pack(side="left")

        # Equation box
        eq_box = ctk.CTkFrame(card, fg_color=T.BG3, corner_radius=10)
        eq_box.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(eq_box, text=rec.relation,
                     font=("Consolas", 14, "bold"),
                     text_color=T.INDIGO).pack(padx=16, pady=12)

        # Meta
        meta = ctk.CTkFrame(card, fg_color="transparent")
        meta.pack(fill="x", padx=16, pady=(0, 14))

        if rec.master_case:
            self._meta_row(meta, "Theorem", rec.master_case, T.TEXT2)
        self._meta_row(meta, "Solution", rec.solution, T.EMERALD)
        self._meta_row(meta, "Stack Space", rec.space, T.TEXT)

    def _meta_row(self, parent, key, val, color):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=key.upper(),
                     font=("Segoe UI", 9, "bold"),
                     text_color=T.TEXT3, width=90, anchor="w").pack(
                         side="left", padx=(0, 8))
        ctk.CTkLabel(row, text=val, font=("Consolas", 12, "bold"),
                     text_color=color, anchor="w").pack(side="left")

    # ── Observations & Suggestions ───────────────────────────
    def _render_observations(self, parent, obs, sug):
        card = card_frame(parent)
        card.pack(fill="x", padx=16, pady=(6, 16))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 8))
        section_label(hdr, "Analysis", T.CYAN).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(hdr, text="Observations & Suggestions", font=T.TITLE,
                     text_color=T.TEXT).pack(side="left")

        # Observations
        if obs:
            for o in obs:
                text = self._strip_rich_tags(o)
                icon, color = ("✓", T.EMERALD) if text.startswith("[OK]") else ("!", T.AMBER)
                text = text.replace("[OK]", "").replace("[!!]", "").strip()
                self._obs_row(card, icon, text, color)

        # Suggestions
        if sug:
            ctk.CTkFrame(card, fg_color=T.BORDER, height=1, corner_radius=0
                         ).pack(fill="x", padx=16, pady=(8, 8))
            ctk.CTkLabel(card, text="OPTIMIZATION SUGGESTIONS",
                         font=("Segoe UI", 9, "bold"),
                         text_color=T.EMERALD).pack(padx=16, anchor="w")
            for s in sug:
                self._sug_row(card, s)

        # Bottom padding
        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

    def _obs_row(self, parent, icon, text, color):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=3)
        ctk.CTkLabel(row, text=icon, font=("Segoe UI", 13, "bold"),
                     text_color=color, width=22).pack(side="left")
        ctk.CTkLabel(row, text=text, font=("Segoe UI", 11),
                     text_color=T.TEXT2, anchor="w",
                     wraplength=500).pack(side="left", padx=(4, 0))

    def _sug_row(self, parent, text):
        row = ctk.CTkFrame(parent, fg_color=_alpha(T.EMERALD, 0.06),
                           corner_radius=8)
        row.pack(fill="x", padx=16, pady=3)
        ctk.CTkLabel(row, text="->", font=("Consolas", 11, "bold"),
                     text_color=T.EMERALD, width=24).pack(
                         side="left", padx=(10, 4), pady=8)
        ctk.CTkLabel(row, text=text, font=("Segoe UI", 10),
                     text_color=T.TEXT2, anchor="w",
                     wraplength=480).pack(side="left", padx=(0, 10), pady=8)

    @staticmethod
    def _strip_rich_tags(text):
        return re.sub(r"\[/?[a-z_ ]+\]", "", text)

    # ──────────────────────────────────────────────────────────
    #  Syntax Highlighting (basic)
    # ──────────────────────────────────────────────────────────
    def _on_editor_key(self, event=None):
        self.after(50, self._apply_syntax_tags)

    def _apply_syntax_tags(self):
        ed = self.editor
        # Remove old tags
        for tag in ("kw", "fn", "str", "num", "cmt", "op", "bi"):
            ed.tag_remove(tag, "1.0", "end")

        # Style definitions
        ed.tag_configure("kw",  foreground="#c678dd")   # purple keywords
        ed.tag_configure("fn",  foreground="#61afef")   # blue functions
        ed.tag_configure("str", foreground="#98c379")   # green strings
        ed.tag_configure("num", foreground="#d19a66")   # orange numbers
        ed.tag_configure("cmt", foreground="#5c6370")   # grey comments
        ed.tag_configure("op",  foreground="#56b6c2")   # cyan operators
        ed.tag_configure("bi",  foreground="#e5c07b")   # yellow builtins

        code = ed.get("1.0", "end")

        patterns = [
            ("cmt", r"#[^\n]*"),
            ("str", r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"[^"\n]*"|\'[^\'\n]*\''),
            ("kw",  r"\b(def|class|if|elif|else|for|while|return|import|from|"
                    r"as|in|not|and|or|is|None|True|False|try|except|finally|"
                    r"with|yield|lambda|raise|pass|break|continue|global|"
                    r"nonlocal|assert|del|async|await|"
                    r"int|void|char|bool|float|double|long|short|unsigned|"
                    r"public|private|protected|static|const|struct|typedef|"
                    r"include|using|namespace|template|virtual|override|"
                    r"new|delete|this|nullptr|null|var|let|function|"
                    r"extends|implements|interface|abstract|super|"
                    r"switch|case|default|do|goto|enum)\b"),
            ("bi",  r"\b(len|range|print|sorted|enumerate|zip|map|filter|"
                    r"min|max|sum|abs|type|isinstance|list|dict|set|tuple|"
                    r"str|int|float|bool|input|open|super|append|extend|"
                    r"printf|scanf|cout|cin|endl|vector|string|"
                    r"System|Arrays|Collections|ArrayList|HashMap|"
                    r"console|log|Math|Array)\b"),
            ("fn",  r"\b(\w+)\s*(?=\()"),
            ("num", r"\b\d+\.?\d*\b"),
            ("op",  r"[+\-*/%=<>!&|^~]|->|=>|::"),
        ]

        for tag, pattern in patterns:
            for match in re.finditer(pattern, code):
                start_idx = f"1.0+{match.start()}c"
                end_idx   = f"1.0+{match.end()}c"
                ed.tag_add(tag, start_idx, end_idx)

        # Raise priority: comments > strings > keywords
        ed.tag_raise("str")
        ed.tag_raise("cmt")


# ═══════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = ComplexityApp()
    app.mainloop()
