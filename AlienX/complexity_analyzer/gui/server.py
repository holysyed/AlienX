#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui/server.py
--------------
Flask API server that wraps the complexity analyzer and serves the web UI.

Run:  python gui/server.py
Then open: http://localhost:5000
"""

import os
import sys
import json
import time

# Ensure parent directory is on path so 'analyzer' package resolves
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request, jsonify, send_from_directory

from analyzer.engine      import AlgorithmAnalyzer
from analyzer.languages   import Language, detect_language
from analyzer.parsers     import PythonParser, GenericParser
from analyzer.complexity  import ComplexityEngine
from analyzer.observations import generate_observations
from analyzer.demos       import DEMOS

app = Flask(__name__, static_folder="static")

_engine    = ComplexityEngine()
_analyzer  = AlgorithmAnalyzer()

# ── Language map ──────────────────────────────────────────────────────────────
LANG_MAP = {
    "python": Language.PYTHON,
    "c":      Language.C,
    "cpp":    Language.CPP,
    "java":   Language.JAVA,
    "javascript": Language.JAVASCRIPT,
    "pseudocode": Language.PSEUDOCODE,
    "auto":   None,
}


# ── Helper: convert dataclasses to JSON-safe dicts ───────────────────────────
def _complexity_to_dict(c):
    if c is None:
        return None
    return {"notation": c.notation, "explanation": c.explanation}


def _recurrence_to_dict(r):
    if r is None:
        return None
    return {
        "relation":    r.relation,
        "solution":    r.solution,
        "master_case": r.master_case,
        "space":       r.space,
    }


def _complexity_rank(notation: str) -> int:
    """Return 0-10 rank so the UI can color-code complexity."""
    n = notation.lower()
    if "n!" in n:        return 10
    if "2^n" in n:       return 9
    if "n^3" in n or "n3" in n: return 8
    if "n^2" in n or "n2" in n: return 7
    if "n^2 log" in n:   return 7
    if "n log n" in n:   return 6
    if n == "o(n)":      return 5
    if "sqrt" in n:      return 4
    if "log n" in n:     return 3
    if "log log" in n:   return 2
    if n in ("o(1)", "omega(1)", "theta(1)"): return 1
    return 5


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/demos", methods=["GET"])
def get_demos():
    """Return all built-in demo snippets."""
    result = []
    meta = {
        "1": {"name": "Bubble Sort",     "complexity": "O(n^2)",    "lang": "python"},
        "2": {"name": "Binary Search",   "complexity": "O(log n)",  "lang": "python"},
        "3": {"name": "Merge Sort",      "complexity": "O(n log n)","lang": "python"},
        "4": {"name": "Fibonacci (naive)","complexity": "O(2^n)",   "lang": "python"},
        "5": {"name": "Triple Sum",      "complexity": "O(n^3)",    "lang": "python"},
        "6": {"name": "Quick Sort",      "complexity": "O(n^2) worst","lang": "cpp"},
    }
    for key, (lang_key, code) in DEMOS.items():
        info = meta.get(key, {})
        result.append({
            "id":         key,
            "name":       info.get("name", f"Demo {key}"),
            "complexity": info.get("complexity", "?"),
            "language":   lang_key,
            "code":       code.strip(),
        })
    return jsonify(result)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Main analysis endpoint.

    Request body (JSON):
        { "code": "...", "language": "python" | "auto" | ... }

    Response (JSON):
        Full structured analysis result.
    """
    data = request.get_json(force=True, silent=True) or {}
    code     = data.get("code", "").strip()
    lang_key = data.get("language", "auto").lower()

    if not code:
        return jsonify({"error": "No code provided."}), 400

    # Detect / resolve language
    language = LANG_MAP.get(lang_key)  # None means auto-detect
    if language is None:
        language = detect_language(code)

    # Parse
    if language == Language.PYTHON:
        parser     = PythonParser()
        parse_data = parser.parse(code)
        if "parse_error" in parse_data:
            parse_data = GenericParser().parse(code, language)
    else:
        parse_data = GenericParser().parse(code, language)

    # Deduce complexity
    result = _engine.deduce(parse_data, language, code)

    # Observations
    obs, sug = generate_observations(code, parse_data, result)

    # Build response
    worst_rank = _complexity_rank(result.worst_case.notation)

    response = {
        "language":         language.value,
        "detected_language": language.value,
        "description":      _make_description(parse_data, result, language),
        "known_algorithm":  result.known_algorithm,

        # Step 1
        "breakdown": {
            "loops":           parse_data.get("loops", []),
            "max_nesting":     parse_data.get("max_nesting", 0),
            "has_recursion":   parse_data.get("has_recursion", False),
            "recursive_funcs": parse_data.get("recursive_funcs", []),
            "builtin_calls":   parse_data.get("builtin_calls", []),
            "conditionals":    parse_data.get("conditionals", []),
            "functions":       parse_data.get("functions", []),
            "data_structures": parse_data.get("data_structures", []),
        },

        # Step 2
        "recurrence": _recurrence_to_dict(result.recurrence),

        # Step 3
        "complexity": {
            "best":    _complexity_to_dict(result.best_case),
            "average": _complexity_to_dict(result.average_case),
            "worst":   _complexity_to_dict(result.worst_case),
            "space":   _complexity_to_dict(result.space),
        },

        "worst_rank": worst_rank,  # 1-10, used for color coding

        # Step 4
        "observations": obs,
        "suggestions":  sug,
    }

    return jsonify(response)


def _make_description(parse_data, result, language):
    loops    = parse_data.get("loops", [])
    nesting  = parse_data.get("max_nesting", 0)
    has_rec  = parse_data.get("has_recursion", False)
    lang_str = language.value.capitalize()

    if result.known_algorithm:
        return f"This {lang_str} snippet implements {result.known_algorithm}."
    if has_rec and loops:
        return (f"This {lang_str} function is recursive and also contains "
                f"{len(loops)} loop(s) with max nesting depth {nesting}.")
    if has_rec:
        funcs = parse_data.get("recursive_funcs", [])
        return (f"This {lang_str} function ({', '.join(funcs)}) calls itself recursively.")
    if not loops:
        return f"This {lang_str} snippet contains no loops -- likely O(1) constant time."
    return (f"This {lang_str} snippet has {len(loops)} loop(s) with max nesting depth {nesting}.")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n  Algorithm Complexity Analyzer - Web UI")
    print("  Open your browser at: http://localhost:5000\n")
    app.run(debug=True, port=5000, use_reloader=False)
