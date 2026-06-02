#!/usr/bin/env bash
# Local mirror of .github/workflows/ci.yml — run BEFORE every push.
#   ./ci-local.sh
# Hard gates (exit non-zero on failure): backend pytest, frontend vitest, frontend build.
# Informational (never block): ruff, radon, npm audit.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> [1/3] backend pytest"
( cd backend && .venv/bin/python -m pytest -q )

echo "==> [2/3] frontend vitest"
( cd frontend && npm run test:run )

echo "==> [3/3] frontend build"
( cd frontend && npm run build >/dev/null && echo "build OK" )

echo
echo "--- informational (non-blocking) ---"
( cd backend && uvx ruff check app )            || echo "  ruff: findings (non-blocking)"
( cd backend && uvx radon cc -s -n C app )      || true
( cd frontend && npm audit --audit-level=high ) || echo "  npm audit: findings (non-blocking)"

echo
echo "✅ HARD GATES PASS — safe to push."
