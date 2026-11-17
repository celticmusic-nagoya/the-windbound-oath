# MORWEN canonical reference intake — 2026-11-16

**Status:** Director-designated new reference set / ORIGINAL BYTES PENDING GITHUB UPLOAD / G1 BLOCKED until uploaded SHA verification. **Do not overwrite** prior approved source or mark 3D production reference PASS.

Director supplied five images in chat and expressly instructed their registration as the official design and original sources. A byte-preserving ZIP package `MORWEN_CANONICAL_20261116_ORIGINALS.zip` and JSON manifest have been prepared for GitHub upload. Original images have **not yet been committed**; this document is metadata only.

## File intake manifest (SHA-256, original bytes)
| Proposed GitHub filename | Format | Dimensions | SHA-256 |
|---|---|---|---|
| `MORWEN_DESIGN_SHEET_APPROVED_SOURCE.jpg` | JPEG/JFIF (upload named .png) | 1536×1024 | `d9730dad8b1791204bb39f52697a176d4556e82a33442fdc0c101059bcc7113b` |
| `LAYER0_FRONT.png` | RGBA PNG | 384×1024 | `b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed` |
| `LAYER0_BACK.png` | RGBA PNG | 384×1024 | `b9d6d6667be8d9bbed1538a42cbaea0e51bab68371366962e43463fbe394976f` |
| `LAYER0_PROFILE_FACING_RIGHT.png` | RGBA PNG | 384×1024 | `9f4873cf331f55b72510159412bd0bfc4c606499f792626e03cffcdace7bf737` |
| `LAYER0_PROFILE_FACING_LEFT.png` | RGBA PNG | 384×1024 | `69f23ce23cf9c56228e1e4d9a23fbab6b6607456a35239c853718a84da2298fa` |

Target directory after upload: `assets/canonical/morwen/2026-11-16/`. ZIP stores exact uploaded bytes without image processing. Alpha exists in Layer0 PNGs but is not certified strict binary 0/255.

## Canonical precedence / historical protection
- Director's 2026-11-16 message explicitly designates these **five new uploads** as the formal reference set. This is a later explicit decision than `docs/design/MORWEN_V561_CANONICAL_20261108.md` identifying the earlier `7374.png` SHA `47d58c...`. Preserve that earlier file and record as historical, **do not silently overwrite** it or pretend its SHA matches this new source.
- Design sheet governs costume/face/hair/accessories and color; Layer0 four views govern anatomical/inner construction only. If the design sheet and Layer0 differ, do not overwrite costume canon with underwear/inner-layer geometry.
- Director separately specified **7.5–8-head new 3D geometry target** and anatomical RIGHT leg garter, continuous and visible from rear. This supersedes prior conflicting 3D proportion/garter interpretations but does not imply generated four-view art is approved.
- Do not infer the final 3D turnaround from the supplied images without checking view consistency and director's visual approval.

## Next actions
1. Upload ZIP's five files and MANIFEST.json to the target directory on this Draft PR branch, preserving bytes.
2. Verify each GitHub raw file SHA256 against this manifest, inspect image content and provenance.
3. Update canonical registry in a non-destructive versioned entry; explicitly mark old references as historical without deletion.
4. Create 7.5–8-head *candidate* four-view 3D modeling sheet using this new reference set; independent art QA and director approval required.
5. Keep G1 BLOCKED until bytes, hierarchy and visual QA confirmed. No main merge or publication.

## QA
- Five upload files inspected in local container; format, dimensions, SHA256 recorded.
- GitHub image binary upload: NOT_RUN (GitHub connector only accepts text content or blobs passed as strings; no container-to-connector binary transfer used).
- G1 BLOCKED / G2 NOT_RUN for new model / G3 NOT_RUN for new model / G4 NOT_RUN.

## 2026-11-17 status reconciliation (append-only)

The opening **ORIGINAL BYTES PENDING GITHUB UPLOAD** status above describes the historical intake stage, **not the current state**. The five source files and `MANIFEST.json` are now committed at `assets/canonical/morwen/2026-11-16/`; registration and GitHub re-fetch verification are recorded in `docs/design/MORWEN_CANONICAL_20261116_REGISTRATION.md` and `REGISTRATION_VERIFY.json`. Preserve this intake record for provenance; use the newer registration document for current source status and precedence. `docs/production/MORWEN_3D_TURNAROUND_01_BRIEF.md` already reflects the new precedence. A new 7.5–8-head four-view illustration and production-ready Morwen 3D model are **NOT_RUN / NOT_APPROVED**. Blender CC0 basemesh geometry inventory PASS does not imply art or canonical-model G1 PASS. Do not replace canonical assets, merge main, or publish without explicit authorization.
