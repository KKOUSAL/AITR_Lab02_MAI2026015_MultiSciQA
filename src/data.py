"""Data loading, protocol access, input construction and leakage control.

Only QUESTION and CONTEXTS may reach a prompt (protocol_v1: data.input_fields).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_VERSION = 4            # v3 -> v4 on 2026-11-16 (D15: hi+or only, P0 only, Colab)
PROTOCOL = ROOT / "configs" / f"protocol_v{PROTOCOL_VERSION}.yaml"
PROTOCOL_HASH = ROOT / "configs" / f"protocol_v{PROTOCOL_VERSION}.sha256"

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def load_protocol(path: Path = PROTOCOL, check_hash: bool = True) -> dict:
    """Load the frozen protocol; refuse to run if it changed since freezing."""
    raw = path.read_bytes()
    if check_hash:
        expected = PROTOCOL_HASH.read_text().split()[0]
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise RuntimeError(
                f"{path.name} hash {actual[:12]} != frozen {expected[:12]}. "
                "Protocol changes must go to a new version (P07 §10)."
            )
    return yaml.safe_load(raw)


def load_items(cfg: dict, split: str, limit: int | None = None) -> list[dict]:
    """Return items for 'test' or 'dev' in sorted PMID order.

    Each item: {pmid, question, contexts (list[str]), gold}. Gold is kept for evaluation
    only; it is never passed to build_prompt.
    """
    if split not in ("test", "dev"):
        raise ValueError(split)
    data = json.loads((ROOT / cfg["data"]["items"]).read_text())
    ids = (ROOT / cfg["data"][f"{split}_ids"]).read_text().split()
    if limit:
        ids = ids[:limit]
    items = []
    for pmid in ids:
        rec = data[pmid]
        items.append({
            "pmid": pmid,
            "question": rec["QUESTION"],
            "contexts": list(rec["CONTEXTS"]),
            "gold": rec["final_decision"],
        })
    return items


def split_sentences(text: str) -> list[str]:
    """Protocol segmentation rule for MT (verified on test: 4,787 segments, D12)."""
    return [s for s in SENT_SPLIT.split(text.strip()) if s]


def join_context(contexts: list[str], cfg: dict) -> str:
    return cfg["data"]["context_join"].join(c.strip() for c in contexts)


def build_prompt(question: str, context: str, cfg: dict, template_id: str = "P0") -> str:
    """Render the user prompt. Takes only question + context, so no other field can leak."""
    if template_id == "P0":
        tpl = cfg["prompt"]["text"]
    else:
        tpl = cfg["prompt"]["sensitivity_templates"][template_id]
    return tpl.format(context=context, question=question).rstrip() + "\n"


def assert_no_leak(prompt: str, raw_record: dict) -> None:
    """Fail if the long answer (the abstract's conclusion) appears in a prompt."""
    la = raw_record.get("LONG_ANSWER", "").strip()
    if la and la in prompt:
        raise AssertionError("LONG_ANSWER leaked into prompt")
