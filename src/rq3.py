"""RQ3 measurements: number preservation through translation and token fertility."""
from __future__ import annotations

import re
from collections import Counter

# Native digit blocks -> ASCII (Devanagari, Bengali, Gurmukhi, Odia)
_DIGIT_BASES = {"devanagari": 0x0966, "bengali": 0x09E6, "gurmukhi": 0x0A66, "odia": 0x0B66}
_DIGIT_MAP = {chr(base + i): str(i) for base in _DIGIT_BASES.values() for i in range(10)}
_DIGIT_TABLE = str.maketrans(_DIGIT_MAP)

# A number: digits with optional thousands/decimal separators, e.g. 12, 0.05, 1,234.5
_NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")


def normalize_digits(text: str) -> str:
    return text.translate(_DIGIT_TABLE)


def extract_numbers(text: str) -> Counter:
    """Multiset of numeric strings after digit normalisation; trailing separators dropped."""
    return Counter(_NUM_RE.findall(normalize_digits(text)))


def number_preservation(source: str, target: str) -> dict:
    """Share of the source's numbers (multiset) that also occur in the target.

    Returns n_source, n_preserved, rate (None if the source has no numbers).
    """
    src, tgt = extract_numbers(source), extract_numbers(target)
    n_src = sum(src.values())
    kept = sum(min(c, tgt[k]) for k, c in src.items())
    return {"n_source": n_src, "n_preserved": kept, "rate": (kept / n_src) if n_src else None}


def fertility(n_tokens_x: int, n_tokens_en: int) -> float:
    """Token fertility of an X-language input relative to its English original."""
    if n_tokens_en <= 0:
        raise ValueError("English token count must be positive")
    return n_tokens_x / n_tokens_en
