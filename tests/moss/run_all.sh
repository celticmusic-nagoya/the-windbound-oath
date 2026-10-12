#!/usr/bin/env bash
# Sequential Moss regressions with exit codes, elapsed seconds and known-flake notes.
set -uo pipefail
cd "$(dirname "$0")/../.."
mapfile -t targets < <(if (($#)); then printf '%s\n' "$@"; else find tests/moss -maxdepth 1 -name '*.py' -type f | sort; fi)
for target in "${targets[@]}"; do
  if [[ "$target" != tests/moss/*.py || ! -f "$target" ]]; then
    echo "Invalid Moss test: $target" >&2; exit 2
  fi
done
out="${TEST_RESULTS_DIR:-$(mktemp -d /tmp/windbound-moss.XXXXXX)}"
mkdir -p "$out"
if ! python3 -c 'import socket; s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); s.bind(("127.0.0.1",8765)); s.close()' 2>"$out/port.log"; then
  echo 'Port 8765 is occupied. This runner starts its own server; stop your test server first.' >&2; exit 2
fi
python3 -m http.server 8765 --bind 127.0.0.1 >"$out/server.log" 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true' EXIT
ready=0
for ((i=0;i<50;i++)); do
  if ! kill -0 "$server_pid" 2>/dev/null; then cat "$out/server.log"; exit 2; fi
  if python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8765/index.html",timeout=.5)' 2>/dev/null; then ready=1; break; fi
  sleep .1
done
if (( !ready )); then echo 'Server did not become ready' >&2; exit 2; fi
printf 'test\texit_code\telapsed_seconds\tnote\n' >"$out/results.tsv"
failed=0; count=0
for target in "${targets[@]}"; do
  command=(python3 -u tests/run_python.py "$target")
  [[ "$target" == tests/moss/walk_map.py ]] && command+=(moss_forest_02_mossy_ravine.json)
  limit="${TEST_TIMEOUT_SECONDS:-900}"
  [[ "$target" == tests/moss/seal_a3.py ]] && limit="${TEST_TIMEOUT_SECONDS:-600}"
  # m19 writes screenshots unless OUT is supplied. Keep runner artifacts outside source.
  started=$SECONDS
  OUT="$out/height-screenshots" timeout --kill-after=5 "$limit" "${command[@]}" >"$out/${target//\//_}.log" 2>&1
  code=$?; elapsed=$((SECONDS-started)); count=$((count+1)); note=''
  [[ "$target" == tests/moss/m6_quest.py ]] && note='既知の不安定（申告あり、失敗でも続行）'
  [[ "$target" == tests/moss/m4_e2e.py ]] && note='既知の不安定/台詞期待値不一致（基準branch依存）'
  printf '%s\t%s\t%s\t%s\n' "$target" "$code" "$elapsed" "$note" >>"$out/results.tsv"
  printf '%s exit=%s elapsed=%ss %s\n' "$target" "$code" "$elapsed" "$note"
  if ((code)); then failed=$((failed+1)); tail -8 "$out/${target//\//_}.log"; fi
done
printf 'Executed=%s Failed=%s Results=%s\n' "$count" "$failed" "$out"
((count>0 && failed==0))
