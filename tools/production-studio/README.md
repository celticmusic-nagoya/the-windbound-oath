# TWO Production Studio — candidate
Read-only, mobile-first, isolated from the game. No deployment or main merge authorized by this file.

## Run locally
Node.js 22, Python 3. From this directory:
```sh
npm install --ignore-scripts --no-audit --no-fund
python3 -m http.server 8765 --bind 127.0.0.1
```
Open http://127.0.0.1:8765/. Three.js 0.180.0 (MIT) is served locally; no CDN. Public GitHub API only, unauthenticated and subject to rate limits. Latest 20 runs and three tracked PRs are not exhaustive. Unknown QA stays unknown.
## Artifact workflow
Download via authenticated GitHub UI; no token entry in Studio. Select ZIP, copy source digest, verify SHA-256 (128 MiB limit). Preview PNG/JPEG from ZIP locally (12 images, 32 MiB total, 8 MiB each); CRC and provenance not verified by preview. Manual gallery: 24 images, 25 MiB each. No upload. GLB/VRM local inspection and basic glTF drawing, 100 MiB limit; external resource references blocked. VRM-specific material, physics, animation QA not supported.
## Evidence
Chromium smoke run 44959038430, HEAD 121fb84441cf233299cc0e5a16a856bc4501c945, artifact 14729020829. Diagnostic fixtures only: mocked GitHub API, mobile viewport, SHA match/mismatch, ZIP preview/rejection, GLB load. Actual asset, actual API, Android hardware, visual QA, security review and deployment remain unverified. Existing Production OS and owning PRs are authoritative. Do not publish restricted assets. No automatic authenticated retrieval or production adoption.
