"""Zero-shot label scoring by log-likelihood (protocol_v1: scoring).

For each item we compute log P(label | prompt + answer prefix) for " yes", " no", " maybe"
(summed over the label's tokens) and predict the argmax. There is no sampling.
"""
from __future__ import annotations

import copy

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

from .device import pick_device

LABELS = ("yes", "no", "maybe")


class LabelScorer:
    def __init__(self, model_id: str, chat_template: bool, answer_prefix: str = "Answer:",
                 device: str | None = None, dtype: str = "float16"):
        self.model_id = model_id
        self.device = device or pick_device()
        self.chat = chat_template
        self.answer_prefix = answer_prefix
        torch_dtype = torch.float16 if (dtype == "float16" and self.device != "cpu") else torch.float32
        self.tok = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch_dtype).to(self.device).eval()
        self.label_ids = {l: self._label_tokens(l) for l in LABELS}

    def render(self, user_prompt: str) -> str:
        """Full text up to and including the answer prefix; the label follows directly."""
        if self.chat:
            msgs = [{"role": "user", "content": user_prompt}]
            head = self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            return head + self.answer_prefix
        return user_prompt + "\n" + self.answer_prefix

    def _label_tokens(self, label: str) -> list[int]:
        """Tokens of ' label' as they appear after the prefix (checked by tokenizing jointly)."""
        probe = self.render("x")
        a = self.tok(probe, add_special_tokens=False)["input_ids"]
        b = self.tok(probe + " " + label, add_special_tokens=False)["input_ids"]
        if b[:len(a)] != a:
            raise RuntimeError(f"{self.model_id}: prefix tokens change when ' {label}' is appended")
        return b[len(a):]

    def label_token_report(self) -> dict:
        return {l: {"ids": ids, "pieces": self.tok.convert_ids_to_tokens(ids)} for l, ids in self.label_ids.items()}

    @torch.inference_mode()
    def score(self, user_prompt: str) -> dict:
        text = self.render(user_prompt)
        ids = self.tok(text, add_special_tokens=not self.chat, return_tensors="pt")["input_ids"].to(self.device)
        out = self.model(ids, use_cache=True)
        first_lp = F.log_softmax(out.logits[0, -1].float(), dim=-1)
        ll = {}
        for label, toks in self.label_ids.items():
            total = first_lp[toks[0]].item()
            if len(toks) > 1:                      # continue from the cached prefix
                past = copy.deepcopy(out.past_key_values)
                cont = torch.tensor([toks[:-1]], device=self.device)
                o2 = self.model(cont, past_key_values=past, use_cache=True)
                lps = F.log_softmax(o2.logits[0].float(), dim=-1)
                total += sum(lps[i, t].item() for i, t in enumerate(toks[1:]))
            ll[label] = total
        pred = max(ll, key=ll.get)
        return {"pred": pred, **{f"ll_{k}": v for k, v in ll.items()}, "n_input_tokens": int(ids.shape[1])}
