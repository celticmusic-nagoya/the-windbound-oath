#!/usr/bin/env python3
"""Unit/integration tests for the v0.5 AI collaboration pipeline.
Run:  python3 -m unittest discover -s tools/character-asset-studio/pipeline/tests -v
"""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PIPE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPE))
from caslib import core, schemas, imageqa, manifest, report, brief, align, prbody, bodyspec  # noqa: E402
from PIL import Image  # noqa: E402

STUDIO = PIPE.parent
REPO = core.REPO_ROOT
CANVAS = {"width": 120, "height": 160}
ANCHOR = [60, 154]


def figure(path, dx=0, dy=0, size=(120, 160), mode="RGBA", height=120, bg=(0, 0, 0, 0), touch_border=False, shade=0):
    """Simple 'character': torso + two feet whose lowest row sits on the anchor (60,154) when dx=dy=0."""
    im = Image.new("RGBA", size, bg)
    px = im.load()
    top = 154 - height + 1
    for y in range(top + dy, 155 + dy):
        for x in range(50 + dx, 71 + dx):
            if 0 <= x < size[0] and 0 <= y < size[1]:
                px[x, y] = (120 + shade, 60, 160, 255)
    if touch_border:
        px[0, 80] = (255, 0, 0, 255)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    (im.convert(mode) if mode != "RGBA" else im).save(p)
    return p


def asset_set(root, frames, kind="walk_frames", view="right", **extra):
    doc = {"schema": "cas/asset-set/0.5", "status": "UNAPPROVED_CANDIDATE", "characterId": "testchar", "kind": kind,
           "canvas": dict(CANVAS), "anchor": {"px": list(ANCHOR), "n": core.to_norm(ANCHOR, CANVAS)}, "frameCount": len(frames),
           "views": {view: [{"frame": i, "file": {"path": core.rel(p, root), "sha256": core.sha256_file(p)}} for i, p in frames]}}
    doc.update(extra)
    return doc


def results(rep, cid):
    return [c["result"] for c in rep["checks"] if c["id"] == cid]


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cas_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---------- coordinates: parity with studio-core.js ----------
    def test_coordinate_parity_with_studio_core(self):
        cases = {"px": [[0, 0], [600, 1540], [1199, 1599], [333.5, 777.25], [-5, 2000]],
                 "n": [[0.5, 0.9625], [0.44583, 0.725], [0.123455, 0.987655], [1, 1]],
                 "canvases": [{"width": 1200, "height": 1600}, {"width": 96, "height": 128}, {"width": 1024, "height": 1280}],
                 "imgs": [[1152, 1536], [1200, 1600], [640, 360], [96, 128]]}
        js = """const C=require(process.argv[1]);const k=JSON.parse(process.argv[2]);const o={toNorm:[],toPixel:[],placement:[]};
for(const c of k.canvases){for(const p of k.px)o.toNorm.push(C.toNorm(p,c));for(const n of k.n)o.toPixel.push(C.toPixel(n,c));for(const i of k.imgs)o.placement.push(C.placement(i[0],i[1],c));}
o.template=C.templateLandmarks().front;o.stable=C.stableStringify({b:1.0,a:[2.5,{z:null,y:'é'}]});console.log(JSON.stringify(o));"""
        out = json.loads(subprocess.run(["node", "-e", js, str(STUDIO / "studio-core.js"), json.dumps(cases)], capture_output=True, text=True, check=True).stdout)
        py = {"toNorm": [], "toPixel": [], "placement": []}
        for c in cases["canvases"]:
            py["toNorm"] += [core.to_norm(p, c) for p in cases["px"]]
            py["toPixel"] += [core.to_pixel(n, c) for n in cases["n"]]
            py["placement"] += [core._norm(core.placement(i[0], i[1], c)) for i in cases["imgs"]]
        self.assertEqual(py["toNorm"], out["toNorm"])
        self.assertEqual(py["toPixel"], out["toPixel"])
        self.assertEqual(py["placement"], out["placement"])
        self.assertEqual({k: v["n"] for k, v in out["template"].items()}, brief.TEMPLATE)
        self.assertEqual(core.stable_dumps({"b": 1.0, "a": [2.5, {"z": None, "y": "é"}]}), out["stable"])

    def test_map_point_and_alignment_offset(self):
        self.assertEqual(core.map_point([600, 1540], {"width": 1200, "height": 1600}, {"width": 96, "height": 128}), [48, 123])
        self.assertEqual(core.alignment_offset([591.5, 1530], [600, 1540]), [9, 10])

    # ---------- schemas ----------
    def test_schema_validation_classification(self):
        ok = asset_set(self.tmp, [(0, figure(self.tmp / "a.png"))])
        self.assertEqual(schemas.validate(ok)["result"], "PASS")
        bad = copy.deepcopy(ok); bad["anchor"]["n"] = [2, 0]; bad["status"] = "MAYBE"
        r = schemas.validate(bad)
        self.assertEqual(r["result"], "FAIL"); self.assertGreaterEqual(len(r["errors"]), 2)
        self.assertEqual(schemas.validate({"hello": 1})["result"], "BLOCKED")
        for f in [STUDIO / "motion" / "grid_overlay_walk.reference.json", PIPE / "examples" / "demo_candidates.asset-set.json",
                  PIPE / "examples" / "morwen_walk_brief" / "production_brief.json"]:
            self.assertEqual(schemas.validate_file(f)["result"], "PASS", f)

    def test_body_spec_v2_from_studio_validates(self):
        js = """const C=require(process.argv[1]);const p={id:'MORWEN_REAL_1200x1600',canvas:[1200,1600],ground:[0.5,0.9625],frames:12};
console.log(C.stableStringify(C.buildSpec({characterId:'morwen',preset:p,landmarks:C.templateLandmarks(),assets:[],referenceBody:null})));"""
        spec = json.loads(subprocess.run(["node", "-e", js, str(STUDIO / "studio-core.js")], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(schemas.validate(spec)["schema"], "BASE_BODY_SPEC/2.0")
        self.assertEqual(schemas.validate(spec)["result"], "PASS", schemas.validate(spec)["errors"])

    # ---------- image QA ----------
    def test_good_walk_set_passes_automated_and_leaves_human_not_run(self):
        frames = [(i, figure(self.tmp / f"w{i}.png", shade=i * 10, height=118 + i)) for i in range(6)]
        rep = imageqa.run(asset_set(self.tmp, frames), repo_root=self.tmp)
        auto = [c for c in rep["checks"] if c["kind"] == "automated"]
        self.assertTrue(all(c["result"] == "PASS" for c in auto), [c for c in auto if c["result"] != "PASS"])
        human = [c for c in rep["checks"] if c["kind"] == "human"]
        self.assertTrue(human and all(c["result"] == "NOT_RUN" for c in human))
        self.assertEqual(rep["overall"], "NOT_RUN")
        self.assertEqual(schemas.validate(rep)["result"], "PASS")

    def test_human_review_records_are_used_never_invented(self):
        frames = [(i, figure(self.tmp / f"h{i}.png", shade=i * 10)) for i in range(2)]
        reviews = {cid: {"result": "PASS", "by": "director", "date": "2026-11-11"} for cid, _ in imageqa.HUMAN_CHECKS}
        rep = imageqa.run(asset_set(self.tmp, frames, humanReviews=reviews), repo_root=self.tmp)
        self.assertEqual(rep["overall"], "PASS")
        self.assertTrue(all(c["detail"]["by"] == "director" for c in rep["checks"] if c["kind"] == "human"))

    def test_failures_are_detected(self):
        f = {
            "size": figure(self.tmp / "size.png", size=(100, 160)),
            "rgb": figure(self.tmp / "rgb.png", mode="RGB"),
            "opaque": figure(self.tmp / "opaque.png", bg=(200, 200, 200, 255)),
            "border": figure(self.tmp / "border.png", touch_border=True),
            "float": figure(self.tmp / "float.png", dy=-12),
            "shiftx": figure(self.tmp / "shiftx.png", dx=30),
        }
        expect = {"size": "dimensions", "rgb": "alpha_channel", "opaque": "real_transparency", "border": "transparent_border", "float": "ground_contact"}
        for name, cid in expect.items():
            rep = imageqa.run(asset_set(self.tmp, [(0, f[name])], kind="reference"), repo_root=self.tmp)
            self.assertIn("FAIL", results(rep, cid), name)
            self.assertEqual(rep["overall"], "FAIL")
        rep = imageqa.run(asset_set(self.tmp, [(0, f["shiftx"])], kind="reference"), repo_root=self.tmp)
        self.assertEqual(results(rep, "anchor_x_at_contact"), ["FAIL"])

    def test_frame_integrity(self):
        a, b = figure(self.tmp / "a.png"), figure(self.tmp / "b.png", shade=40)
        doc = asset_set(self.tmp, [(0, a), (1, b), (3, a)]); doc["frameCount"] = 4
        rep = imageqa.run(doc, repo_root=self.tmp)
        fs = [c for c in rep["checks"] if c["id"] == "frame_set_complete"][0]
        self.assertEqual((fs["result"], fs["detail"]["missing"]), ("FAIL", [2]))
        rep = imageqa.run(asset_set(self.tmp, [(0, a), (1, a), (2, b)]), repo_root=self.tmp)
        self.assertEqual(results(rep, "no_identical_consecutive_frames"), ["FAIL"])
        tall, short = figure(self.tmp / "t.png", height=140), figure(self.tmp / "s.png", height=90)
        rep = imageqa.run(asset_set(self.tmp, [(0, tall), (1, short)]), repo_root=self.tmp)
        self.assertEqual(results(rep, "bbox_height_consistency"), ["FAIL"])
        lo, hi = figure(self.tmp / "lo.png"), figure(self.tmp / "hi.png", dy=-5, shade=20)
        rep = imageqa.run(asset_set(self.tmp, [(0, lo), (1, hi)]), repo_root=self.tmp)
        self.assertEqual(results(rep, "ground_consistency"), ["FAIL"])
        doc = asset_set(self.tmp, [(0, a)]); doc["views"]["right"][0]["file"]["sha256"] = "0" * 64
        self.assertEqual(results(imageqa.run(doc, repo_root=self.tmp), "file_sha256"), ["FAIL"])
        doc = asset_set(self.tmp, [(0, a)]); doc["views"]["right"].append({"frame": 0, "file": {"path": "missing.png"}}); doc["frameCount"] = 1
        rep = imageqa.run(doc, repo_root=self.tmp)
        self.assertIn("FAIL", results(rep, "file_present"))

    def test_status_and_blocked_reference(self):
        a = figure(self.tmp / "a.png")
        rep = imageqa.run(asset_set(self.tmp, [(0, a)], status="DIRECTOR_APPROVED"), repo_root=self.tmp)
        self.assertEqual(results(rep, "approval_record"), ["FAIL"])
        r21 = "assets/candidates/morwen/real-canon-final-04/fix03/BASE_BODY_SPEC.json"
        rep = imageqa.run(asset_set(self.tmp, [(0, a)], references=[{"path": r21, "sha256": "0" * 64, "role": "body"}]), repo_root=self.tmp)
        self.assertEqual(results(rep, "reference_usable"), ["BLOCKED"])
        self.assertEqual(rep["overall"], "BLOCKED")
        bad = asset_set(self.tmp, [(0, a)]); bad["kind"] = "hero"
        rep = imageqa.run(bad, repo_root=self.tmp)
        self.assertEqual((results(rep, "schema_valid"), rep["overall"]), (["FAIL"], "FAIL"))

    def test_costume_layer_without_feet_skips_ground_checks(self):
        hat = Image.new("RGBA", (120, 160), (0, 0, 0, 0))
        for x in range(40, 80):
            for y in range(5, 30):
                hat.putpixel((x, y), (90, 40, 130, 255))
        p = self.tmp / "hat.png"; hat.save(p)
        doc = asset_set(self.tmp, [(0, p)], kind="costume_layer", layer={"slot": "headgear_upper", "zOrder": 50, "parentAnchor": "shared"})
        rep = imageqa.run(doc, repo_root=self.tmp)
        self.assertEqual(results(rep, "ground_contact"), [])
        self.assertTrue(all(c["result"] == "PASS" for c in rep["checks"] if c["kind"] == "automated"))

    def test_demo_candidates_example(self):
        rep = imageqa.run(core.load_json(PIPE / "examples" / "demo_candidates.asset-set.json"))
        self.assertEqual(rep["counts"]["FAIL"] + rep["counts"]["BLOCKED"], 0)
        self.assertEqual(rep["overall"], "NOT_RUN")

    # ---------- manifest / protection ----------
    def test_manifest_build_verify_and_tamper(self):
        d = self.tmp / "set"; figure(d / "a.png"); (d / "n.json").write_text("{}")
        m = manifest.build(d, repo_root=self.tmp)
        self.assertEqual(schemas.validate(m)["result"], "PASS")
        self.assertEqual(manifest.verify(m, repo_root=self.tmp)["overall"], "PASS")
        (d / "n.json").write_text('{"x":1}'); (d / "extra.txt").write_text("x")
        rep = manifest.verify(m, repo_root=self.tmp)
        self.assertEqual(rep["overall"], "FAIL")
        self.assertEqual(results(rep, "no_unlisted_files"), ["FAIL"])
        with self.assertRaises(core.PolicyError):
            manifest.build(d, status="DIRECTOR_APPROVED", repo_root=self.tmp)

    def test_protected_assets_unchanged_and_guarded(self):
        rep = manifest.verify_protected()
        self.assertEqual((rep["overall"], rep["counts"]["PASS"]), ("PASS", 17))
        canon = "assets/candidates/morwen/final-visual-canon-20261111/front.png"
        self.assertTrue(core.is_protected(canon))
        self.assertTrue(core.is_protected("assets/official/characters/morwen/new.png"))
        self.assertFalse(core.is_protected("assets/candidates/morwen/walk-ai/x.png"))
        with self.assertRaises(core.PolicyError):
            core.guard_write(REPO / canon, overwrite=True)
        p = figure(self.tmp / "exists.png")
        with self.assertRaises(core.PolicyError):
            core.guard_write(p)
        self.assertEqual(manifest.changed_protected(["README.md", canon]), [canon])
        m = manifest.build(REPO / "assets/candidates/morwen/final-visual-canon-20261111")
        self.assertTrue(all(e["status"] == "CANONICAL_PROTECTED" for e in m["files"] if e["path"].endswith(".png")))

    # ---------- alignment ----------
    def test_align_writes_new_file_onto_anchor(self):
        src = figure(self.tmp / "off.png", dx=-7, dy=-9)
        r = align.align(src, self.tmp / "out" / "aligned.png", CANVAS, ANCHOR, repo_root=self.tmp)
        self.assertEqual((r["result"], r["offset"]), ("PASS", [7, 9]))
        m = imageqa.measure(self.tmp / "out" / "aligned.png")
        self.assertEqual((m["contact"]["bottomRow"], m["contact"]["x"]), (154, 60))
        with self.assertRaises(core.PolicyError):
            align.align(src, self.tmp / "out" / "aligned.png", CANVAS, ANCHOR, repo_root=self.tmp)
        neg = figure(self.tmp / "neg.png", dx=8, dy=0)
        r = align.align(neg, self.tmp / "out" / "neg.png", CANVAS, ANCHOR, repo_root=self.tmp)
        m = imageqa.measure(self.tmp / "out" / "neg.png")
        self.assertEqual((r["offset"], m["contact"]["x"], m["contact"]["bottomRow"]), ([-8, 0], 60, 154))
        big = figure(self.tmp / "big.png", size=(240, 320), height=240)  # different size -> uniform placement
        big2 = Image.new("RGBA", (240, 320), (0, 0, 0, 0)); big2.alpha_composite(Image.open(big).crop((0, 0, 240, 160)).resize((240, 320)))
        r = align.align(big, self.tmp / "out" / "placed.png", CANVAS, ANCHOR, repo_root=self.tmp)
        self.assertEqual(r["placement"]["exact"], False)
        edge = figure(self.tmp / "edge.png", dx=-50)
        r = align.align(edge, self.tmp / "out" / "edge.png", CANVAS, [119, 154], repo_root=self.tmp)
        self.assertEqual(r["result"], "FAIL")
        self.assertFalse((self.tmp / "out" / "edge.png").exists())

    # ---------- brief ----------
    def test_brief_is_valid_unapproved_and_guarded(self):
        b = brief.build_brief("T-1", "costume_layer", "morwen", "HD_FIELD_1024x1280", self.tmp / "g", "assets/candidates/morwen/test",
                              frame_count=6, layer_slot="headgear_upper", repo_root=self.tmp, with_preview=False)
        self.assertEqual(schemas.validate(b)["result"], "PASS", schemas.validate(b)["errors"])
        self.assertEqual((b["status"], b["adoption"]["autoAdopt"]), ("UNAPPROVED_INSTRUCTION", False))
        self.assertEqual(b["anchor"]["px"], [512, 1230])
        g = Image.open(self.tmp / "g" / "guide_front.png")
        self.assertEqual((g.size, g.mode), ((1024, 1280), "RGBA"))
        self.assertEqual(g.getpixel((5, 5))[3] if g.getpixel((5, 5))[3] == 0 else 0, 0)
        self.assertGreater(g.getpixel((512, 1230))[3], 0)  # anchor drawn
        with self.assertRaises(core.PolicyError):
            brief.build_brief("T", "walk_frames", "morwen", "MORWEN_REAL_1200x1600", self.tmp / "x", "assets/official/morwen")
        with self.assertRaises(core.PolicyError):
            brief.build_brief("T", "base_body", "morwen", "MORWEN_REAL_1200x1600", self.tmp / "y", "assets/candidates/morwen/x",
                              body_spec_path=REPO / "assets/candidates/morwen/real-canon-final-04/fix03/BASE_BODY_SPEC.json")

    # ---------- report ----------
    def test_overall_precedence_and_markdown(self):
        c = report.Checks()
        c.add("a", "s", "PASS"); self.assertEqual(report.overall(c.rows), "PASS")
        c.add("b", "s", "NOT_RUN", "human"); self.assertEqual(report.overall(c.rows), "NOT_RUN")
        c.add("c", "s", "BLOCKED"); self.assertEqual(report.overall(c.rows), "BLOCKED")
        c.add("d", "s", "FAIL"); self.assertEqual(report.overall(c.rows), "FAIL")
        self.assertEqual(report.overall([]), "NOT_RUN")
        md = report.to_markdown([("x.json", report.make_report({"kind": "t"}, c.rows))])
        self.assertIn("**FAIL**", md); self.assertIn("NOT_RUN", md)

    def test_cli_exit_codes(self):
        cas = [sys.executable, str(PIPE / "cas.py")]
        self.assertEqual(subprocess.run(cas + ["protect-verify"], capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run(cas + ["validate", str(PIPE / "examples" / "demo_candidates.asset-set.json")], capture_output=True).returncode, 0)
        r = subprocess.run(cas + ["brief", "--task-id", "X", "--kind", "walk_frames", "--character", "morwen", "--preset", "MORWEN_REAL_1200x1600",
                                  "--out-dir", str(self.tmp / "b"), "--deliver-to", "assets/candidates/morwen/final-visual-canon-20261111/x"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 64); self.assertIn("BLOCKED", r.stdout)


class V051(unittest.TestCase):
    """CHARACTER-ASSET-STUDIO-07 reliability fixes."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cas051_"))
        self.cas = [sys.executable, str(PIPE / "cas.py")]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # 1. idempotent PR sections
    def test_pr_body_merge_is_idempotent(self):
        body = "Intro\n\n## Notes\ntext"
        b1, a1 = prbody.merge(body, "pipeline-qa", "### QA\n| x |\n")
        b2, a2 = prbody.merge(b1, "pipeline-qa", "### QA\n| x |\n")
        self.assertEqual((a1, a2, b1 == b2), ("appended", "unchanged", True))
        self.assertEqual(b2.count(prbody.begin("pipeline-qa")), 1)
        b3, a3 = prbody.merge(b2, "pipeline-qa", "### QA\n| y |")
        self.assertEqual((a3, b3.count("| x |"), b3.count("| y |")), ("replaced", 0, 1))
        self.assertTrue(b3.startswith("Intro\n\n## Notes\ntext"))
        b4, _ = prbody.merge(b3, "other", "B")
        self.assertEqual(prbody.sections(b4), ["pipeline-qa", "other"])
        b5, a5 = prbody.merge(b4, "pipeline-qa", "### QA\n| y |")
        self.assertEqual((a5, b5), ("unchanged", b4))

    def test_pr_body_legacy_marker_converted_without_text_loss(self):
        legacy_tail = "\n---\n## v0.5 section\n| a |\n\nfooter\n"
        body = "Top text\n\n" + prbody.LEGACY + legacy_tail
        new, action = prbody.merge(body, "pipeline-qa", "S")
        self.assertEqual(action, "appended+legacy-converted")
        self.assertEqual(prbody.sections(new), [prbody.LEGACY_KEY, "pipeline-qa"])
        self.assertIn(legacy_tail.strip(), new)
        self.assertNotIn(prbody.LEGACY, new)
        again, a2 = prbody.merge(new, "pipeline-qa", "S")
        self.assertEqual((a2, again), ("unchanged", new))

    def test_pr_body_refuses_ambiguous_markers(self):
        bad = prbody.begin("k") + "\nA\n" + prbody.end("k") + "\n" + prbody.begin("k") + "\nB\n" + prbody.end("k")
        with self.assertRaises(ValueError):
            prbody.merge(bad, "k", "C")
        with self.assertRaises(ValueError):
            prbody.merge(prbody.begin("k") + "\nA\n", "k", "C")
        with self.assertRaises(ValueError):
            prbody.merge("", "bad key", "C")

    # 2. QA verdict vs exit code, adoptionReady
    def _qa_fixture(self, **extra):
        frames = [(i, figure(self.tmp / f"q{i}.png", shade=i * 20)) for i in range(2)]
        doc = asset_set(self.tmp, frames, **extra)
        p = self.tmp / "set.json"; p.write_text(json.dumps(doc))
        return doc, p

    def test_adoption_ready_requires_human_checks(self):
        doc, _ = self._qa_fixture()
        rep = imageqa.run(doc, repo_root=self.tmp)
        self.assertTrue(all(c["result"] == "PASS" for c in rep["checks"] if c["kind"] == "automated"))
        self.assertEqual((rep["overall"], rep["adoptionReady"]), ("NOT_RUN", False))
        self.assertTrue(any("human checks NOT_RUN" in b for b in rep["adoptionBlockers"]))
        self.assertEqual(schemas.validate(rep)["result"], "PASS")
        forged = dict(rep, adoptionReady=True)
        self.assertEqual(schemas.validate(forged)["result"], "FAIL", "schema rejects adoptionReady with a non-PASS overall")
        ids = [c["id"] for c in rep["checks"] if c["kind"] == "human"]
        reviews = {i: {"result": "PASS", "by": "director", "date": "2026-11-11"} for i in ids}
        rep2 = imageqa.run(dict(doc, humanReviews=reviews), repo_root=self.tmp)
        self.assertEqual((rep2["overall"], rep2["adoptionReady"], rep2["adoptionBlockers"]), ("PASS", True, []))
        auto_only = report.make_report({"kind": "t"}, [{"id": "a", "scope": "s", "result": "PASS", "kind": "automated"}])
        self.assertEqual((auto_only["overall"], auto_only["adoptionReady"]), ("PASS", False))

    def test_cli_gate_codes_in_repo(self):
        work = REPO / "tools/character-asset-studio/pipeline/tests/_tmp_v051"
        shutil.rmtree(work, ignore_errors=True); work.mkdir()
        try:
            good = [(i, figure(work / f"g{i}.png", shade=i * 20)) for i in range(2)]
            doc = asset_set(REPO, good); gp = work / "good.json"; gp.write_text(json.dumps(doc))
            bad = asset_set(REPO, [(0, figure(work / "bad.png", dy=-12))]); bp = work / "bad.json"; bp.write_text(json.dumps(bad))
            r = lambda *a: subprocess.run(self.cas + list(a), capture_output=True, text=True)
            g0 = r("qa", str(gp)); out = json.loads(g0.stdout)
            self.assertEqual((g0.returncode, out["overall"], out["adoptionReady"]), (0, "NOT_RUN", False))
            self.assertEqual(r("qa", str(gp), "--gate", "no-fail").returncode, 0)
            self.assertEqual(r("qa", str(gp), "--gate", "adoption").returncode, 3)
            b0 = r("qa", str(bp))
            self.assertEqual((b0.returncode, json.loads(b0.stdout)["overall"]), (0, "FAIL"))
            self.assertEqual(r("qa", str(bp), "--gate", "no-fail").returncode, 1)
            self.assertEqual(r("qa", str(bp), "--gate", "adoption").returncode, 1)
            # 3. overwrite rules through the CLI
            rp = work / "rep.json"
            self.assertEqual(r("qa", str(gp), "--report", str(rp)).returncode, 0)
            self.assertEqual(r("qa", str(gp), "--report", str(rp)).returncode, 64, "no silent overwrite")
            self.assertEqual(r("qa", str(gp), "--report", str(rp), "--overwrite").returncode, 0, "own qa-report can be regenerated")
            self.assertEqual(r("qa", str(gp), "--report", str(gp), "--overwrite").returncode, 64, "asset-set is not pipeline output")
            self.assertEqual(r("qa", str(gp), "--report", str(work / "g0.png"), "--overwrite").returncode, 64)
            canon = REPO / "assets/candidates/morwen/final-visual-canon-20261111/MANIFEST.json"
            before = core.sha256_file(canon)
            self.assertEqual(r("protect-verify", "--report", str(canon), "--overwrite").returncode, 64)
            self.assertEqual(core.sha256_file(canon), before)
        finally:
            shutil.rmtree(work, ignore_errors=True)

    # 3. overwrite policy (library level)
    def test_overwrite_policy(self):
        rep = report.make_report({"kind": "t"}, [])
        own = self.tmp / "r.json"; own.write_text(core.stable_dumps(rep))
        self.assertEqual(core.guard_write(own, self.tmp, overwrite=True), own.resolve())
        with self.assertRaises(core.PolicyError):
            core.guard_write(own, self.tmp)
        foreign = self.tmp / "f.json"; foreign.write_text('{"schema": "cas/asset-set/0.5"}')
        with self.assertRaises(core.PolicyError):
            core.guard_write(foreign, self.tmp, overwrite=True)
        md = self.tmp / "m.md"; md.write_text("hand written")
        with self.assertRaises(core.PolicyError):
            core.guard_write(md, self.tmp, overwrite=True)
        md.write_text(report.to_markdown([("x", rep)]))
        core.guard_write(md, self.tmp, overwrite=True)
        cand = self.tmp / "assets" / "candidates" / "x" / "r.json"; cand.parent.mkdir(parents=True); cand.write_text(core.stable_dumps(rep))
        with self.assertRaises(core.PolicyError):
            core.guard_write(cand, self.tmp, overwrite=True)
        new = self.tmp / "brand-new.json"
        self.assertEqual(core.guard_write(new, self.tmp), new.resolve())

    def test_brief_overwrite_only_regenerates_its_own_guides(self):
        out = self.tmp / "brief"
        b = brief.build_brief("T", "walk_frames", "morwen", "PIXEL_96x128", out, "assets/candidates/morwen/t", repo_root=self.tmp, with_preview=False)
        (out / "production_brief.json").write_text(core.stable_dumps(b))
        with self.assertRaises(core.PolicyError):
            brief.build_brief("T", "walk_frames", "morwen", "PIXEL_96x128", out, "assets/candidates/morwen/t", repo_root=self.tmp, with_preview=False)
        brief.build_brief("T", "walk_frames", "morwen", "PIXEL_96x128", out, "assets/candidates/morwen/t", repo_root=self.tmp, with_preview=False, overwrite=True)
        stranger = out / "guide_front_preview.png"; figure(stranger)
        before = core.sha256_file(out / "guide_front.png")
        with self.assertRaises(core.PolicyError):   # preview not listed by the brief -> refused before anything is written
            brief.build_brief("T2", "walk_frames", "morwen", "PIXEL_96x128", out, "assets/candidates/morwen/t", repo_root=self.tmp, with_preview=True, overwrite=True)
        self.assertEqual(core.sha256_file(out / "guide_front.png"), before)

    # 4. legacy BASE_BODY_SPEC
    def test_legacy_body_spec_kept_and_upgrade_matches_studio(self):
        legacy = STUDIO / "docs" / "BASE_BODY_SPEC.example.json"
        sha = core.sha256_file(legacy)
        v = schemas.validate_file(legacy)
        self.assertEqual((v["schema"], v["result"]), ("BASE_BODY_SPEC/1.0-legacy", "PASS"))
        up = bodyspec.upgrade_v1(core.load_json(legacy))
        self.assertEqual(schemas.validate(up)["result"], "PASS", schemas.validate(up)["errors"])
        js = """const C=require(process.argv[1]);const fs=require('fs');const j=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const P=JSON.parse(fs.readFileSync(process.argv[3],'utf8')).presets.find(p=>p.id===j.presetId);
const r=C.parseSpec(j,P);process.stdout.write(C.stableStringify(C.buildSpec({characterId:j.characterId,preset:P,landmarks:r.landmarks,assets:[],referenceBody:null})));"""
        node = subprocess.run(["node", "-e", js, str(STUDIO / "studio-core.js"), str(legacy), str(STUDIO / "profiles" / "presets.json")], capture_output=True, text=True)
        self.assertEqual(node.returncode, 0, node.stderr)
        self.assertEqual(core.stable_dumps(up), node.stdout)
        committed = STUDIO / "docs" / "BASE_BODY_SPEC.example.v2.json"
        self.assertEqual(committed.read_text(encoding="utf-8"), node.stdout, "committed v2 example equals the studio's own conversion")
        self.assertEqual(core.sha256_file(legacy), sha, "legacy original unchanged")
        r = subprocess.run(self.cas + ["body-spec-upgrade", str(legacy), "--out", str(committed)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 64, "existing output is never overwritten")
        bad = dict(core.load_json(legacy)); bad["landmarks"] = {"front": {}}
        with self.assertRaises(ValueError):
            bodyspec.upgrade_v1(bad)


if __name__ == "__main__":
    unittest.main()
