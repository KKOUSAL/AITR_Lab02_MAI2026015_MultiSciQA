"""Measure IndicTrans2 EN->hi speed under different settings on the same dev sentences.

Not part of the experiment: timing only, no cache is written. Output: results/translation/bench.json
Usage: python scripts/bench_translate.py --n 16
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import torch  # noqa: E402
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer  # noqa: E402

try:
    from IndicTransToolkit.processor import IndicProcessor
except ImportError:
    from IndicTransToolkit import IndicProcessor

from src.data import load_items, load_protocol, split_sentences  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=16)
    args = ap.parse_args()
    cfg = load_protocol()
    mid = cfg["translation"]["en_to_x"]
    sents = [s for it in load_items(cfg, "dev", 40)[20:] for c in it["contexts"] for s in split_sentences(c)][:args.n]
    ip = IndicProcessor(inference=True)
    tok = AutoTokenizer.from_pretrained(mid, trust_remote_code=True)
    batch = ip.preprocess_batch(sents, src_lang="eng_Latn", tgt_lang="hin_Deva")
    results = []
    configs = [("mps", torch.float32, 5), ("mps", torch.float16, 5), ("mps", torch.float16, 1),
               ("cpu", torch.float32, 5), ("cpu", torch.float32, 1)]
    outs = {}
    for dev, dt, beams in configs:
        if dev == "mps" and not torch.backends.mps.is_available():
            continue
        model = AutoModelForSeq2SeqLM.from_pretrained(mid, trust_remote_code=True, torch_dtype=dt).to(dev).eval()
        enc = tok(batch, truncation=True, padding="longest", return_tensors="pt").to(dev)
        with torch.inference_mode():
            model.generate(**enc, num_beams=beams, max_new_tokens=16)          # warm-up
            t = time.time()
            out = model.generate(**enc, num_beams=beams, max_new_tokens=512, use_cache=True)
            secs = time.time() - t
        dec = ip.postprocess_batch(tok.batch_decode(out, skip_special_tokens=True), lang="hin_Deva")
        key = f"{dev}-{str(dt).split('.')[-1]}-beam{beams}"
        outs[key] = dec
        results.append({"config": key, "n": len(sents), "seconds": round(secs, 2),
                        "sec_per_sentence": round(secs / len(sents), 3)})
        print(results[-1], flush=True)
        del model
        if dev == "mps":
            torch.mps.empty_cache()
    ref = outs.get("mps-float32-beam5") or outs.get("cpu-float32-beam5")
    for r in results:
        r["identical_to_fp32_beam5"] = sum(a == b for a, b in zip(outs[r["config"]], ref))
    p = ROOT / "results" / "translation" / "bench.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"sentences": sents, "results": results}, indent=2, ensure_ascii=False))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
