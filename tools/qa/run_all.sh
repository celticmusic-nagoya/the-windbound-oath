#!/usr/bin/env bash
# Sequential tests; isolated tracked snapshot; one owned server per test.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec "${PYTHON:-python3}" -u tools/qa/run_regressions.py "$@"
