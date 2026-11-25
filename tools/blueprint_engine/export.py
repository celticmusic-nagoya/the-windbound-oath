"""QA/Export: canonical JSON, SHA ledger, blueprint preview SVG, Studio read model.

Outputs are metadata and diagrams only; no native file, private source image or
publication approval is emitted. Studio publication stays with the Studio owner
(#468 studio_checkpoint_export requires a separate pinned approval).
"""
import json
import os
from pathlib import Path

from . import ENGINE_VERSION, SCHEMA
from .sources import file_sha256

STATE_COLOR = {"PASS": "#2e7d32", "HOLD": "#f9a825", "OUTSIDE": "#c62828"}


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, sort_keys=True, allow_nan=False,
                               ensure_ascii=False) + "\n")
    return path


def ledger(root, evidence_classes=None):
    root = Path(root)
    entries = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel in ("SHA256SUMS", "ledger.json"):
            continue
        entries[rel] = dict(sha256=file_sha256(path), bytes=path.stat().st_size,
                            evidence=(evidence_classes or {}).get(rel, "ENGINE_OUTPUT"))
    (root / "SHA256SUMS").write_text("".join(f"{e['sha256']}  {k}\n" for k, e in entries.items()))
    write_json(root / "ledger.json", dict(schema=SCHEMA, engine_version=ENGINE_VERSION,
                                          files=entries))
    return entries


def _svg(width, height, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" font-family="sans-serif" font-size="11">'
            f'<rect width="100%" height="100%" fill="#fafafa"/>'
            f'<text x="8" y="16" font-size="13" font-weight="bold">{title}</text>{body}</svg>\n')


def bbox_plan_svg(path, title, boxes, anchors=(), size=720, pad=40):
    """Top view (X right, Y up). boxes: [(label, target_xyxy, actual_xyxy|None, state)]."""
    xs = [v for _, t, a, _ in boxes for v in (t[0], t[2], *(a[0::2] if a else ()))]
    ys = [v for _, t, a, _ in boxes for v in (t[1], t[3], *(a[1::2] if a else ()))]
    xs += [a[1][0] for a in anchors]
    ys += [a[1][1] for a in anchors]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    scale = (size - 2 * pad) / max(x1 - x0, y1 - y0, 1e-9)

    def p(x, y):
        return pad + (x - x0) * scale, size - pad - (y - y0) * scale

    body = []
    for label, t, a, state in boxes:
        (ax, ay), (bx, by) = p(t[0], t[3]), p(t[2], t[1])
        body.append(f'<rect x="{ax:.1f}" y="{ay:.1f}" width="{bx-ax:.1f}" height="{by-ay:.1f}" '
                    f'fill="none" stroke="#555" stroke-dasharray="4 3"/>')
        if a:
            (cx, cy), (dx, dy) = p(a[0], a[3]), p(a[2], a[1])
            body.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{dx-cx:.1f}" height="{dy-cy:.1f}" '
                        f'fill="{STATE_COLOR[state]}" fill-opacity="0.12" '
                        f'stroke="{STATE_COLOR[state]}"><title>{label}: {state}</title></rect>')
        if state != "PASS":
            body.append(f'<text x="{ax+2:.1f}" y="{ay-3:.1f}" fill="{STATE_COLOR[state]}">'
                        f'{label} {state}</text>')
    for label, xy, state in anchors:
        cx, cy = p(*xy)
        body.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.5" fill="{STATE_COLOR[state]}">'
                    f'<title>{label}: {state}</title></circle>')
    body.append(f'<text x="8" y="{size-10}" fill="#555">dashed = blueprint target, filled = '
                f'native measured; green PASS / amber HOLD / red OUTSIDE</text>')
    Path(path).write_text(_svg(size, size, "".join(body), title))
    return path


def scanline_svg(path, title, size_px, rows, scale=0.6):
    """rows: [(y, target_lr, actual_lr, state)] in source pixels (no source image embedded)."""
    w, h = size_px[0] * scale + 80, size_px[1] * scale + 40
    body = [f'<rect x="40" y="24" width="{size_px[0]*scale:.1f}" height="{size_px[1]*scale:.1f}" '
            f'fill="none" stroke="#bbb"/>']
    for y, (tl, tr), (al, ar), state in rows:
        yy = 24 + y * scale
        body.append(f'<line x1="{40+tl*scale:.1f}" y1="{yy:.1f}" x2="{40+tr*scale:.1f}" '
                    f'y2="{yy:.1f}" stroke="#555" stroke-dasharray="3 2"/>')
        body.append(f'<line x1="{40+al*scale:.1f}" y1="{yy+2:.1f}" x2="{40+ar*scale:.1f}" '
                    f'y2="{yy+2:.1f}" stroke="{STATE_COLOR[state]}" stroke-width="2">'
                    f'<title>y={y}: {state}</title></line>')
    Path(path).write_text(_svg(int(w), int(h), "".join(body), title))
    return path


def studio_record(*, asset_id, case_id, blueprint_summary, groups, readiness, qa, files,
                  limitations):
    """Read-only Studio model. Provenance comes from the Actions environment when present."""
    run_id = os.environ.get("GITHUB_RUN_ID")
    return dict(
        schema=SCHEMA + "/studio", engine_version=ENGINE_VERSION, asset_id=asset_id,
        case_id=case_id, head=os.environ.get("GITHUB_SHA"), run_id=int(run_id) if run_id else None,
        artifact_id=None, adoption="UNDETERMINED", publication="NOT_APPROVED",
        blueprint=blueprint_summary, groups=groups, readiness=readiness, qa=qa, files=files,
        limitations=limitations)
