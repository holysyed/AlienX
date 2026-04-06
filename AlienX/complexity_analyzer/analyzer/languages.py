"""
analyzer/languages.py
─────────────────────
Enum for supported languages + auto-detection logic.
"""

from __future__ import annotations
import re
from enum import Enum


class Language(Enum):
    PYTHON     = "python"
    C          = "c"
    CPP        = "cpp"
    JAVA       = "java"
    JAVASCRIPT = "javascript"
    PSEUDOCODE = "pseudocode"


def detect_language(code: str) -> Language:
    """Heuristically auto-detect the language of a code snippet."""
    # Java
    if re.search(r"\bSystem\.out\b", code) or \
       re.search(r"public\s+(static\s+)?(?:void|int|String|boolean|double|float)\s+\w+\s*\(", code):
        return Language.JAVA

    # C++
    if re.search(r"#include\s*<(?:iostream|vector|map|set|algorithm|string)>", code) or \
       re.search(r"\bstd::", code) or re.search(r"\bcout\s*<<", code):
        return Language.CPP

    # C
    if re.search(r"#include\s*<(?:stdio|stdlib|string)\.h>", code) or \
       re.search(r"\bprintf\s*\(", code) or re.search(r"\bscanf\s*\(", code):
        return Language.C

    # JavaScript
    if re.search(r"\bconsole\.log\b", code) or \
       re.search(r"\b(?:const|let|var)\s+\w+", code) or \
       re.search(r"=>\s*{|function\s+\w+\s*\(", code):
        return Language.JAVASCRIPT

    # Python
    if re.search(r"\bdef\s+\w+\s*\(", code) or \
       re.search(r"\bimport\s+\w+", code) or \
       re.search(r"\bprint\s*\(", code) or \
       re.search(r"^\s*#.*$", code, re.MULTILINE):
        return Language.PYTHON

    # Pseudocode
    if re.search(r"\bfor\s+\w+\s*←|:=|←|begin\b|end\b", code, re.IGNORECASE):
        return Language.PSEUDOCODE

    # Fallback
    return Language.PYTHON
