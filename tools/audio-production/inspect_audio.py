"""Read-only SHA-bound loudness inspection; does not normalize or adopt audio."""
import argparse, json, math, re, shutil, stat, subprocess, zipfile
from pathlib import Path
from process_audio import measure, sha

PINNED_ARCHIVE = "ec8257eb7f5e66599c606a55e0e00eaab8f668216b0f161f06c2d3ceec97a5f6"
PAIRS = (("clean","synthetic-stereo.wav"),("warm","synthetic-stereo.wav"),
         ("warm-repeat","synthetic-stereo.wav"),("mono","synthetic-mono.wav"))
FILES = {"qualification.json","synthetic-stereo.wav","synthetic-mono.wav","synthetic-silent.wav"} | {
    f"{name}/{file}" for name,_ in PAIRS for file in ("candidate.wav","receipt.json")}
DIRS = {name+"/" for name,_ in PAIRS}
HEX = re.compile(r"[a-f0-9]{64}")

def extract_pinned(archive, dest):
    """Only this exact reviewed synthetic fixture, not arbitrary ZIP extraction."""
    if archive.is_symlink() or not archive.is_file() or archive.stat().st_size != 679647 or sha(archive) != PINNED_ARCHIVE:
        raise ValueError("pinned qualification archive mismatch")
    with zipfile.ZipFile(archive) as z:
        seen=set()
        for i in z.infolist():
            name=i.filename
            mode=i.external_attr >> 16
            kind=stat.S_IFMT(mode)
            if name in seen or i.flag_bits & 1:
                raise ValueError("duplicate/encrypted member")
            seen.add(name)
            if i.is_dir():
                if name not in DIRS or i.file_size or kind not in (0,stat.S_IFDIR):
                    raise ValueError("unexpected directory")
            elif name not in FILES or kind not in (0,stat.S_IFREG) or not 0<i.file_size<=24*1024**2:
                raise ValueError("unexpected member")
        if seen-DIRS!=FILES or sum(i.file_size for i in z.infolist())>4*1024**2 or z.testzip() is not None:
            raise ValueError("archive member set, size or CRC mismatch")
        dest.mkdir(parents=True,exist_ok=False)
        for name in sorted(FILES):
            p=dest/name
            p.parent.mkdir(parents=True,exist_ok=True)
            with p.open("xb") as f:
                f.write(z.read(name))

def checked_wav(path):
    if path.is_symlink() or not path.is_file() or path.suffix.lower()!=".wav" or not 44<=path.stat().st_size<=24*1024**2:
        raise ValueError("invalid WAV path or size")
    return measure(path)

def match_pcm(actual, recorded):
    for k in ("channels","sample_rate","frames","full_scale_samples"):
        if type(recorded.get(k)) is not int or recorded[k]!=actual[k]:
            raise ValueError("PCM receipt mismatch: "+k)
    for k in ("sample_peak_dbfs","rms_dbfs"):
        a,b=actual[k],recorded.get(k)
        if a is None or type(b) not in (float,int) or not math.isfinite(b) or abs(a-b)>0.005:
            raise ValueError("PCM receipt mismatch: "+k)

def loudness(path, ffmpeg):
    # Use INPUT statistics only. The filter's processed output is discarded.
    proc=subprocess.run([ffmpeg,"-nostdin","-hide_banner","-loglevel","info",
        "-i",str(path.resolve()),"-map","0:a:0","-vn",
        "-af","loudnorm=I=-24:LRA=7:TP=-2:print_format=json","-f","null","-"],
        stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,timeout=180,check=True)
    blocks=re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}",proc.stderr,re.S)
    if len(blocks)!=1:
        raise ValueError("missing or ambiguous loudnorm report")
    raw=json.loads(blocks[0])
    result={key:float(raw[field]) for key,field in (
        ("integrated_lufs","input_i"),("true_peak_dbtp","input_tp"),
        ("loudness_range_lu","input_lra"),("gating_threshold_lufs","input_thresh"))}
    if not all(math.isfinite(v) for v in result.values()):
        raise ValueError("undefined loudness measurement")
    return result

def inspect_pair(source, candidate, receipt_path, ffmpeg):
    if receipt_path.is_symlink() or not receipt_path.is_file() or not 0<receipt_path.stat().st_size<=65536:
        raise ValueError("invalid receipt")
    receipt=json.loads(receipt_path.read_text())
    if receipt.get("schema")!="two.audio.candidate.v1" or receipt.get("candidate_only") is not True:
        raise ValueError("not a candidate v1 receipt")
    metrics=[]
    for file,key,phase in ((source,"source_sha256","before"),(candidate,"output_sha256","after")):
        expected=receipt[key]
        if not isinstance(expected,str) or not HEX.fullmatch(expected) or sha(file)!=expected:
            raise ValueError("audio SHA mismatch")
        pcm=checked_wav(file)
        match_pcm(pcm,receipt[phase])
        stats=loudness(file,ffmpeg)
        if sha(file)!=expected:
            raise ValueError("audio changed during inspection")
        metrics.append(dict(sha256=expected,pcm=pcm,**stats))
    a,b=metrics
    if a["pcm"]["channels"]!=b["pcm"]["channels"] or a["pcm"]["frames"]!=b["pcm"]["frames"] or b["pcm"]["full_scale_samples"] or b["pcm"]["sample_peak_dbfs"]>-1:
        raise ValueError("candidate PCM integrity/headroom failed")
    return dict(schema="two.audio.loudness-inspection.v1",candidate_only=True,
        source_receipt_sha256=sha(receipt_path),backend=subprocess.check_output([ffmpeg,"-version"],text=True,timeout=10).splitlines()[0],
        backend_sha256=sha(ffmpeg),method="FFmpeg loudnorm input statistics; null sink; no normalization written",
        before=a,after=b,delta_lufs=round(b["integrated_lufs"]-a["integrated_lufs"],2),
        qa={"sha_pcm":"PASS","lufs":"MEASURED","true_peak":"MEASURED",
            "provisional_minus_1_dbtp_headroom":"PASS" if b["true_peak_dbtp"]<=-1 else "HOLD",
            "listening":"NOT_RUN","loop_seam":"NOT_RUN","game":"NOT_RUN","adoption":"UNDETERMINED"})

def write_report(path, report):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        json.dump(report,f,indent=2,allow_nan=False)
        f.write("\n")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="mode",required=True)
    a=sub.add_parser("pair")
    for name in ("source","candidate","receipt","report"):
        a.add_argument(name,type=Path)
    a=sub.add_parser("packet")
    a.add_argument("directory",type=Path);a.add_argument("report",type=Path)
    a.add_argument("--pinned-archive",type=Path)
    args=p.parse_args()
    ffmpeg=shutil.which("ffmpeg")
    if not ffmpeg:raise RuntimeError("FFmpeg unavailable")
    if args.mode=="pair":
        report=inspect_pair(args.source,args.candidate,args.receipt,ffmpeg)
    else:
        if args.pinned_archive:
            extract_pinned(args.pinned_archive,args.directory)
        q=json.loads((args.directory/"qualification.json").read_text())
        if q.get("all_pass") is not True:
            raise ValueError("producer qualification not PASS")
        results={}
        for name,source in PAIRS:
            results[name]=inspect_pair(args.directory/source,args.directory/name/"candidate.wav",args.directory/name/"receipt.json",ffmpeg)
        assert results["warm"]["after"]==results["warm-repeat"]["after"],"repeat measurement mismatch"
        report={"schema":"two.audio.packet-inspection.v1","candidate_only":True,
            "source_archive_sha256":PINNED_ARCHIVE if args.pinned_archive else None,
            "pairs":results,"note":"LRA on two-second fixtures is not meaningful for full musical dynamics; no gain matching or listening approval."}
    write_report(args.report,report)
    print(json.dumps(report,indent=2,allow_nan=False))
if __name__=="__main__":
    main()
