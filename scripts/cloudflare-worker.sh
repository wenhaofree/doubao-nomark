#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/doubao-nomark-worker.XXXXXX")"

cleanup() {
  rm -rf "$WORK_DIR"
}

trap cleanup EXIT

cp "$ROOT_DIR/cloudflare_worker/pyproject.toml" "$WORK_DIR/pyproject.toml"
cp "$ROOT_DIR/wrangler.jsonc" "$WORK_DIR/wrangler.jsonc"
cp "$ROOT_DIR/worker.py" "$WORK_DIR/worker.py"
cp -R "$ROOT_DIR/doubao_parser" "$WORK_DIR/doubao_parser"

cd "$WORK_DIR"

if [[ "${1:-}" == "deploy" ]]; then
  has_name=false
  for arg in "$@"; do
    if [[ "$arg" == "--name" || "$arg" == --name=* ]]; then
      has_name=true
      break
    fi
  done

  if [[ "$has_name" == false ]]; then
    set -- "$@" --name doubao-nomark
  fi
fi

uvx --from workers-py pywrangler "$@"
