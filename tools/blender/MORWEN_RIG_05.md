# MORWEN-RIG-05 — Four-view alignment candidate

Run locally or in a private environment with the four original images:

`blender -b --python tools/blender/align_morwen_views.py -- --input-dir ./references --output-dir ./out`

The script verifies original SHA-256, embeds four images in a .blend scene, and creates four ground markers. It **does not** measure body joints or assign official status. JPEG bytes with .png extension are supported by Blender's image decoder. The .blend packs the images: **do not upload generated .blend to a public GitHub artifact without consent**. Keep it local/private. GitHub stores only the script.

Before motion work: visually confirm side asymmetry (especially left shoulder crest, hat ornaments and satchel), measure joint anchors, and reconcile approved official turnarounds. A generated alignment scene is a candidate, not a final character asset.
