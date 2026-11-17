"""Prompt 08 environment test. Prints versions, device, HF auth status and gated-model access.

Usage: python scripts/env_check.py [--out results/env/env_<host>.json]
Expected output: a JSON object; every 'access' entry should be "ok" before Phase III runs.
"""
import argparse
import json
import platform
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GATED = [
    "ai4bharat/indictrans2-en-indic-dist-200M",
    "ai4bharat/indictrans2-indic-en-dist-200M",
    "meta-llama/Llama-3.2-3B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rep = {"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "python": sys.version.split()[0], "platform": platform.platform()}
    for m in ["torch", "transformers", "accelerate", "sentencepiece", "sacrebleu", "numpy",
              "scipy", "pandas", "yaml", "huggingface_hub", "IndicTransToolkit"]:
        try:
            mod = __import__(m)
            rep[f"v_{m}"] = getattr(mod, "__version__", "installed")
        except Exception as e:  # noqa: BLE001
            rep[f"v_{m}"] = f"MISSING ({type(e).__name__})"

    import torch
    rep["cuda"] = torch.cuda.is_available()
    rep["gpu"] = torch.cuda.get_device_name(0) if rep["cuda"] else None
    rep["gpu_mem_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1) if rep["cuda"] else None
    rep["mps"] = torch.backends.mps.is_available()
    torch.manual_seed(2026)
    rep["seed_check"] = round(float(torch.rand(1)), 6)       # same value on every run of the same torch build

    from huggingface_hub import HfApi
    from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError
    api = HfApi()
    try:
        rep["hf_user"] = api.whoami()["name"]
    except Exception as e:  # noqa: BLE001
        rep["hf_user"] = f"NOT LOGGED IN ({type(e).__name__})"
    access = {}
    for repo in GATED:
        try:
            api.hf_hub_download(repo, "config.json")
            access[repo] = "ok"
        except GatedRepoError:
            access[repo] = "GATED: accept terms / log in"
        except RepositoryNotFoundError:
            access[repo] = "NOT FOUND"
        except Exception as e:  # noqa: BLE001
            access[repo] = f"ERROR {type(e).__name__}"
    rep["access"] = access

    from src.data import load_protocol
    load_protocol()   # raises if the frozen protocol was modified
    rep["protocol_v1_hash_ok"] = True

    txt = json.dumps(rep, indent=2)
    print(txt)
    out = Path(args.out) if args.out else ROOT / "results" / "env" / f"env_{socket.gethostname().split('.')[0]}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(txt)


if __name__ == "__main__":
    main()
