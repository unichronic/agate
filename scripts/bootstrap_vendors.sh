#!/usr/bin/env bash
set -euo pipefail

mkdir -p vendor

clone_or_update() {
  local repo_url="$1"
  local target_dir="$2"
  if [ -d "$target_dir/.git" ]; then
    echo "[update] $target_dir"
    git -C "$target_dir" pull --ff-only
  else
    echo "[clone] $repo_url -> $target_dir"
    git clone --depth 1 "$repo_url" "$target_dir"
  fi
}

# Open-source components you can vendor locally.
clone_or_update "https://github.com/maximhq/bifrost.git" "vendor/bifrost"
clone_or_update "https://github.com/open-policy-agent/opa.git" "vendor/opa"
clone_or_update "https://github.com/microsoft/presidio.git" "vendor/presidio"
clone_or_update "https://github.com/protectai/llm-guard.git" "vendor/llm-guard"

# Lakera/Cisco-A2A are typically integrated as API/service adapters.
echo "[info] Lakera is API-first in this setup; configure LAKERA_URL + LAKERA_API_KEY env vars."
echo "[info] Configure Cisco A2A connectors via gateway service endpoints/policies."
