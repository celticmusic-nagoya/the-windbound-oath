#!/usr/bin/env bash
set -euo pipefail
available() {
    command -v xvfb-run >/dev/null &&
        ldconfig -p | grep -F libEGL.so.1 >/dev/null &&
        compgen -G '/usr/lib/*/dri/swrast_dri.so' >/dev/null
}
if ! available; then
    apt_flags=(-o Acquire::Retries=0 -o Acquire::http::Timeout=10 -o Acquire::https::Timeout=10)
    packages=(libegl1 libgl1-mesa-dri libopengl0 libgl1 xvfb)
    if ! timeout 90s sudo env DEBIAN_FRONTEND=noninteractive apt-get "${apt_flags[@]}" install -y --no-install-recommends "${packages[@]}"; then
        timeout 90s sudo apt-get "${apt_flags[@]}" update -qq
        timeout 90s sudo env DEBIAN_FRONTEND=noninteractive apt-get "${apt_flags[@]}" install -y --no-install-recommends "${packages[@]}"
    fi
fi
available
