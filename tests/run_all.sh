#!/usr/bin/env bash
# Run every standalone Python/browser and Node regression, preserving exit codes.
set -uo pipefail
cd "$(dirname "$0")/.."
out="${TEST_RESULTS_DIR:-$(mktemp -d /tmp/windbound-regression.XXXXXX)}"
mkdir -p "$out"
# Never attach to or stop somebody else's server on the test port.
if ! python3 -c 'import socket; s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); s.bind(("127.0.0.1",8765)); s.close()' 2>"$out/port.log"; then
  echo 'Port 8765 is already in use; stop your test server before running this suite.'
  exit 2
fi
python3 -m http.server 8765 --bind 127.0.0.1 >"$out/server.log" 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true' EXIT
ready=0
for ((i=0;i<50;i++)); do
  if ! kill -0 "$server_pid" 2>/dev/null; then cat "$out/server.log"; exit 2; fi
  if python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8765/index.html", timeout=.5)' 2>/dev/null; then ready=1; break; fi
  sleep .1
done
if (( !ready )); then echo 'Server did not become ready'; exit 2; fi
printf 'test\texit_code\n' >"$out/results.tsv"
failed=0; count=0
while IFS= read -r test; do
  [[ "$test" == tests/run_python.py ]] && continue
  [[ "$test" == *.test.js ]] && command=(node "$test") || command=(python3 -u tests/run_python.py "$test")
  # This generic route utility requires a map argument. A1 and A3 already have
  # dedicated walk/seal regressions; exercise A2 here.
  [[ "$test" == tests/moss/walk_map.py ]] && command+=(moss_forest_02_mossy_ravine.json)
  log="${test//\//_}.log"
  timeout "${TEST_TIMEOUT_SECONDS:-900}" "${command[@]}" >"$out/$log" 2>&1
  code=$?; count=$((count+1))
  printf '%s\t%s\n' "$test" "$code" >>"$out/results.tsv"
  printf '%s exit=%s\n' "$test" "$code"
  if ((code)); then failed=$((failed+1)); tail -8 "$out/$log"; fi
done < <(if (($#)); then printf '%s\n' "$@"; else find tests -type f \( -name '*.py' -o -name '*.test.js' \) ! -path '*/__pycache__/*' | sort; fi)
printf 'Executed=%s Failed=%s Results=%s\n' "$count" "$failed" "$out"
((count>0 && failed==0))
