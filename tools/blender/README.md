# BLENDER-SETUP-01

Draft-only headless Blender smoke test. No AI API or secrets, no sprite generation, no game asset edits, no merge or publication.

- Run `Blender Setup Smoke QA` from Actions or via a PR change to the workflow/script.
- Ubuntu package `blender` is installed at runtime (version recorded, not assumed).
- Produces empty `smoke.blend` and `qa.json` in `/tmp/blender-setup-01/`.
- Artifacts retained 7 days.
- The workflow intentionally does **not** render or create Morwen images. First prove Blender starts.
- If Ubuntu package install fails, inspect logs and replace installation strategy; do not silently claim success.
- Later tasks must validate original reference hashes, asymmetry, alpha, dimensions, and approval status before producing candidate art.
