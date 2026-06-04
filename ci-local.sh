#!/usr/bin/env bash
# Local mirror of .github/workflows/ci.yml — run BEFORE every push.
#   ./ci-local.sh
# Hard gates (exit non-zero on failure):
#   backend: pytest, ruff      frontend: eslint, vitest, build, prod audit
# Informational (never block): radon complexity.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> [1/6] backend pytest (stripped env — mirror CI's bare environment)"
# Strip ambient secrets so a test that only passes because the dev shell has
# SECRET_KEY/LLM_API_KEY set fails HERE, not in CI. Tests must be hermetic.
( cd backend && env -u SECRET_KEY -u LLM_API_KEY .venv/bin/python -m pytest -q )

echo "==> [2/6] backend ruff"
( cd backend && uvx ruff check app )

echo "==> [3/6] frontend eslint"
( cd frontend && npm run lint )

echo "==> [4/6] frontend vitest"
( cd frontend && npm run test:run )

echo "==> [5/6] frontend build"
( cd frontend && npm run build >/dev/null && echo "build OK" )

echo "==> [6/6] frontend audit (prod deps, high+)"
( cd frontend && npm audit --omit=dev --audit-level=high )

echo
echo "--- informational (non-blocking) ---"
( cd backend && uvx radon cc -s -n C app ) || true

echo
echo "✅ HARD GATES PASS — safe to push."
