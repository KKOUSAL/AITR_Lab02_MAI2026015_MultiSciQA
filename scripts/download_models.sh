#!/bin/zsh
# Resumable model downloads (protocol v2). Xet disabled: the 2026-11-13 Qwen-3B download failed in Xet token refresh.
# A download counts as complete ONLY if the snapshot contains a weight file (*.safetensors) and the
# cache has no *.incomplete blobs. `hf download` can exit 0 after a network drop without fetching
# anything (seen 2026-11-16 22:49), so its exit code alone is not trusted.
# Usage: zsh scripts/download_models.sh <repo> [<repo> ...]
export HF_HUB_DISABLE_XET=1
CACHE="${HF_HOME:-$HOME/.cache/huggingface}/hub"

complete() {
  local d="$CACHE/models--${1//\//--}"
  [[ -n $(ls "$d"/snapshots/*/*.safetensors 2>/dev/null) ]] || return 1
  [[ -z $(ls "$d"/blobs/*.incomplete 2>/dev/null) ]] || return 1
  # every safetensors symlink must resolve to a non-empty file
  for f in "$d"/snapshots/*/*.safetensors; do [[ -s "$f" ]] || return 1; done
  return 0
}

rc=0
for repo in "$@"; do
  ok=0
  for attempt in {1..60}; do
    echo "[$(date '+%F %T')] $repo attempt $attempt"
    hf download "$repo" --exclude "*.bin" "original/*" "*.gguf" "*.pth" > /dev/null 2>>"${0:A:h}/../results/env/download_errors.log"
    if complete "$repo"; then
      echo "[$(date '+%F %T')] $repo VERIFIED COMPLETE ($(du -sh "$CACHE/models--${repo//\//--}" | cut -f1))"
      ok=1; break
    fi
    echo "[$(date '+%F %T')] $repo not complete yet; retrying in 20 s"
    sleep 20
  done
  (( ok )) || { echo "[$(date '+%F %T')] $repo FAILED after 60 attempts"; rc=1; }
done
exit $rc
