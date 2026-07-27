#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> API tests"
cd "$ROOT/apps/api"
if [[ -x .venv/bin/pytest ]]; then
  .venv/bin/pytest -q
else
  pytest -q
fi

echo "==> Web tests"
cd "$ROOT/apps/web"
npm test
