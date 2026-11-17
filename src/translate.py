"""IndicTrans2 sentence-level translation with a persistent cache (protocol_v1: translation).

Each segment is translated once per (model, src, tgt); every LLM condition then reads the
same cache, so all models see identical translated text.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import torch

try:                                   # package layout differs across IndicTransToolkit versions
    from IndicTransToolkit.processor import IndicProcessor
except ImportError:                    # pragma: no cover
    from IndicTransToolkit import IndicProcessor

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from .data import ROOT
from .device import pick_device


def seg_key(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


class TranslationCache:
    """Append-only JSONL: {"key", "src", "tgt", "truncated"} per line."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, dict] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                rec = json.loads(line)
                self.data[rec["key"]] = rec

    def get(self, text: str):
        rec = self.data.get(seg_key(text))
        return None if rec is None else rec["tgt"]

    def add_many(self, recs: list[dict]) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            for r in recs:
                self.data[r["key"]] = r
                f.write(json.dumps(r, ensure_ascii=False) + "\n")


class Translator:
    def __init__(self, model_id: str, src_lang: str, tgt_lang: str, cfg: dict, device: str | None = None):
        tcfg = cfg["translation"]
        self.model_id, self.src, self.tgt = model_id, src_lang, tgt_lang
        self.device = device or pick_device()
        self.num_beams = tcfg["num_beams"]
        self.max_new_tokens = tcfg["max_new_tokens"]
        self.batch_size = tcfg["batch_size"]
        dtype = torch.float16 if (self.device == "cuda" and tcfg["dtype"] == "float16") else torch.float32
        self.tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            model_id, trust_remote_code=True, torch_dtype=dtype).to(self.device).eval()
        self.ip = IndicProcessor(inference=True)
        name = model_id.split("/")[-1]
        # Decoding settings are part of the cache key, so a settings change can never reuse old outputs.
        # Beam-5 is the v1-v3 default, so its file name is kept unchanged.
        tag = "" if self.num_beams == 5 else f"__beam{self.num_beams}"
        self.cache = TranslationCache(ROOT / tcfg["cache_dir"] / f"{name}__{src_lang}__{tgt_lang}{tag}.jsonl")

    @torch.inference_mode()
    def _translate_batch(self, sents: list[str]) -> list[tuple[str, bool]]:
        batch = self.ip.preprocess_batch(sents, src_lang=self.src, tgt_lang=self.tgt)
        enc = self.tok(batch, truncation=True, padding="longest", return_tensors="pt",
                       return_attention_mask=True).to(self.device)
        out = self.model.generate(**enc, use_cache=True, min_length=0, num_beams=self.num_beams,
                                  num_return_sequences=1, max_new_tokens=self.max_new_tokens)
        # A row is "truncated" if it never produced EOS, i.e. it stopped at max_new_tokens.
        eos = self.model.generation_config.eos_token_id
        eos = set(eos if isinstance(eos, list) else [eos])
        truncated = [not any(int(t) in eos for t in row[1:]) for row in out]
        # Input-side truncation by the tokenizer is checked separately in scripts/01_translate.py.
        dec = self.tok.batch_decode(out, skip_special_tokens=True, clean_up_tokenization_spaces=True)
        dec = self.ip.postprocess_batch(dec, lang=self.tgt)
        return list(zip(dec, truncated))

    def translate(self, sents: list[str]) -> list[str]:
        """Translate segments, using and filling the cache. Order is preserved."""
        todo = list(dict.fromkeys(s for s in sents if self.cache.get(s) is None))
        # Sort by length so batches pad less; the results are keyed, so order doesn't matter.
        todo.sort(key=len)
        for i in range(0, len(todo), self.batch_size):
            chunk = todo[i:i + self.batch_size]
            res = self._translate_batch(chunk)
            self.cache.add_many([{"key": seg_key(s), "src": s, "tgt": t, "truncated": tr,
                                  "model": self.model_id} for s, (t, tr) in zip(chunk, res)])
        return [self.cache.get(s) for s in sents]
