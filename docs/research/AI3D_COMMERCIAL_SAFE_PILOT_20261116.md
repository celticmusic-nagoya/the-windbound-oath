# THE WINDBOUND OATH | Image-to-3D / Procedural 3D adoption decision (2026-11-16)

Status: RESEARCH + CANDIDATE-ONLY PILOT APPROVED; **not** approval of generated meshes for official use. This document does not grant IP rights.

## Decision
- **Primary**: Existing pinned Blender 5.3.0, Python mesh/curve tooling, QA-first production on GitHub Actions. No inference model is required for MORWEN EYELID-09; residual collision is localized to lash faces 0 and 1 / cage triangles 938 and 940 (run 43784789534, real-model collision G3 FAIL).
- **Optional pilot #1: TripoSR**. Official MIT code and Hugging Face weights tagged MIT. Single-image reconstructions; official README reports ~6GB GPU VRAM for default image inference. Use only independently owned *noncanonical synthetic object image* as input, never protected official character or unreleased design, until hosting privacy and all dependency/model terms are checked. A resulting mesh is **candidate geometry** requiring retopology, UVs, normals, measured topology and visual QA.
- **Optional pilot #2: InstantMesh**. Official repository and Hugging Face model card tagged Apache-2.0. Official installation specifies Python >=3.10 / PyTorch >=2.1 / CUDA >=12.1; exports OBJ vertex colors by default, optional texture. No GPU runner provisioned in this branch. The model card tag does not audit every checkpoint component and third-party package license: block production until independently checked.
- **Do not pilot TRELLIS** until submodule terms (diffoctreerast, modified Flexicubes, etc.), CUDA requirements, checkpoint license and redistribution status are independently audited; core MIT claim alone is insufficient.
- **Use procedural JS / Three.js only where fitting** (placement tools, gizmos, runtime lightweight effects). Avoid primitive-only models masquerading as finished character/house art. Three.js MIT obligations apply when bundling its code; procedural code does not erase third-party reference/image rights.
- **External web generator**: Meshy Free outputs currently CC BY 4.0 (commercial allowed with attribution, quota and model-download restrictions); do not treat as private/exclusive official assets. Tripo Studio web service has *different* terms from TripoSR OSS: as of 2026-11-16 terms 5.2.1 says Free Outputs are public by default with public commercial reuse/waiver if applicable; some help pages still say commercial rights unavailable. Regardless of this inconsistency, **do not upload canonical/private input or adopt Free Outputs as exclusive project IP**.
- **Google Colab free**: opportunistic GPU availability, not assured, so cannot be a deterministic CI requirement. Do not claim automated model execution until a GPU inference run and its exported file SHA are recorded.

## Copyright and license caution
Blender's GPL covers the application, not independently created art, per Blender Foundation. Using Blender does **not** alone guarantee copyright originality or that external assets are cleared. Human artistic editing may strengthen a creativity analysis but does not automatically create ownership of arbitrary AI outputs. Record exact source image origin, ownership, rights, model repository revision, weight revision/hash, dependency license inventory, output SHA256, and generated asset's distribution/credit obligations. Treat legal questions as unresolved until reviewed.

## Pilot admission policy
- Candidate directory only, no original/official asset overwrite. Dedicated branch and Draft PR.
- Input: self-created synthetic image (or separate cleared user-owned image with documented permission); no scraping, Pinterest copying, licensed stock with uncertain model-input permissions, or copyrighted game imagery.
- Execution: choose trusted local/controlled runtime; model weights downloaded only from verified official source; no unapproved service upload or GPU purchase.
- Freeze model SHA, weight SHA, CUDA/runtime and seed when applicable. Keep generated raw output and postprocessed result distinct.
- Gates: G1 original source SHA and legal/provenance; G2 silhouette/readability/art comparison; G3 topology, UV, mesh watertightness as needed, performance, geometry/surface clearance; G4 actual engine and Android behavior.
- Exit after **one** synthetic object candidate: measure setup time, total work, source fidelity, polycount, texture size, editing overhead, privacy and license burden. If low-quality or manual modeling is faster, abandon this AI route rather than create dozens of throwaway meshes.
- No automatic production asset ingestion. No main merge, canonical changes, publication, paid accounts or external uploads.

## Source ledger (checked 2026-11-16)
- TripoSR code MIT: https://github.com/VAST-AI-Research/TripoSR/blob/main/LICENSE
- TripoSR weights MIT tag: https://huggingface.co/stabilityai/TripoSR ; VRAM: https://github.com/VAST-AI-Research/TripoSR/blob/main/README.md
- InstantMesh Apache-2.0 code: https://github.com/TencentARC/InstantMesh/blob/main/LICENSE
- InstantMesh model tag: https://huggingface.co/TencentARC/InstantMesh ; setup: https://github.com/TencentARC/InstantMesh/blob/main/README.md
- TRELLIS submodule exceptions: https://github.com/microsoft/TRELLIS#%EF%B8%8F-license
- Meshy Free CC BY 4.0: https://help.meshy.ai/en/articles/15696428-what-is-included-on-the-free-plan
- Tripo Studio official free policy: https://www.tripo3d.ai/terms ; inconsistent help: https://www.tripo3d.ai/help/privacy-policy/how-to-use-tripo-models-commercially
- Colab fluctuating GPU limits: https://research.google.com/colaboratory/faq.html
- Blender art licensing: https://www.blender.org/about/license/
