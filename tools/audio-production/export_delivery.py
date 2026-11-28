"""Candidate delivery encode/decode QA. No game integration or source overwrite."""
import argparse, json, math, re, shutil, struct, subprocess, tempfile, wave
from pathlib import Path
from process_audio import RATE, sha
from inspect_audio import checked_wav, loudness, write_report

# Provisional technical thresholds, not musical quality or a universal loop specification.
JUMP_LIMIT=0.025
SLOPE_LIMIT=0.025
CODECS={"opus":("delivery.ogg","libopus"),"mp3":("delivery.mp3","libmp3lame")}

def seam(path):
    with wave.open(str(path),"rb") as f:
        n=f.getnframes();c=f.getnchannels()
        if n<4:raise ValueError("loop too short")
        first=struct.unpack("<"+"h"*(2*c),f.readframes(2))
        f.setpos(n-2)
        last=struct.unpack("<"+"h"*(2*c),f.readframes(2))
    jump=max(abs(first[i]-last[c+i])/32768 for i in range(c))
    slope=max(abs((first[c+i]-first[i])-(last[c+i]-last[i]))/32768 for i in range(c))
    return {"sample_jump_fs":jump,"slope_difference_fs":slope,
            "status":"PASS" if jump<=JUMP_LIMIT and slope<=SLOPE_LIMIT else "HOLD"}

def execute(args):
    subprocess.run(args,check=True,timeout=180)

def export(source,expected,out,role,ffmpeg):
    source,out=Path(source),Path(out)
    before=checked_wav(source)
    if not re.fullmatch("[0-9a-f]{64}",expected) or sha(source)!=expected:
        raise ValueError("source SHA mismatch")
    if role not in ("loop","oneshot") or out.exists() or out.is_symlink():
        raise ValueError("invalid role or output exists")
    if before["sample_peak_dbfs"] is None or before["sample_peak_dbfs"]>-1 or before["full_scale_samples"]:
        raise ValueError("source sample headroom/silence")
    src_seam=seam(source) if role=="loop" else None
    if src_seam and src_seam["status"]!="PASS":
        raise ValueError("source loop seam HOLD; edit a separate source candidate first")
    base_loud=loudness(source,ffmpeg)
    version=subprocess.check_output([ffmpeg,"-version"],text=True,timeout=10).splitlines()[0]
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent,prefix=".audio-delivery-") as td:
        temp=Path(td);reports={}
        for key,(filename,encoder) in CODECS.items():
            dest=temp/filename;decoded=temp/(key+".wav")
            bitrate=("96k" if before["channels"]==2 else "64k") if key=="opus" else ("128k" if before["channels"]==2 else "96k")
            common=[ffmpeg,"-nostdin","-hide_banner","-loglevel","error","-n"]
            execute(common+["-i",str(source.resolve()),"-map","0:a:0","-vn","-map_metadata","-1","-c:a",encoder,"-b:a",bitrate,"-ar",str(RATE),"-threads","1",str(dest)])
            execute(common+["-i",str(dest),"-map","0:a:0","-vn","-c:a","pcm_s16le","-ar",str(RATE),str(decoded)])
            after=checked_wav(decoded);stats=loudness(decoded,ffmpeg)
            delta=after["frames"]-before["frames"]
            decoded_seam=seam(decoded) if role=="loop" else None
            frame_ok=delta==0 if role=="loop" else abs(delta)<=960
            small=0<dest.stat().st_size<source.stat().st_size
            technical=frame_ok and small and after["channels"]==before["channels"] and after["full_scale_samples"]==0 and stats["true_peak_dbtp"]<=-1 and abs(stats["integrated_lufs"]-base_loud["integrated_lufs"])<=1
            # MP3 is a one-shot compatibility candidate, never certified for loops here.
            loop_ok=role!="loop" or (key=="opus" and decoded_seam["status"]=="PASS")
            reports[key]={"file":filename,"sha256":sha(dest),"bytes":dest.stat().st_size,
                "size_ratio":round(dest.stat().st_size/source.stat().st_size,6),"encoder":encoder,"bitrate":bitrate,
                "decoded_pcm":after,"decoded_loudness":stats,"decoded_frame_delta":delta,
                "decoded_seam":decoded_seam,"status":"PASS" if technical and loop_ok else "HOLD",
                "scope":"loop candidate" if role=="loop" and key=="opus" else "one-shot candidate / no loop certification"}
        if sha(source)!=expected:raise ValueError("source changed")
        report={"schema":"two.audio.delivery.v1","candidate_only":True,"role":role,
            "source_sha256":expected,"source_bytes":source.stat().st_size,"source_pcm":before,
            "source_loudness":base_loud,"source_seam":src_seam,
            "thresholds":{"sample_jump_fs":JUMP_LIMIT,"slope_difference_fs":SLOPE_LIMIT,"decoded_lufs_delta":1,"true_peak_dbtp":-1},
            "backend":version,"backend_sha256":sha(ffmpeg),"formats":reports,
            "qa":{"listening":"NOT_RUN","game":"NOT_RUN","android":"NOT_RUN","adoption":"UNDETERMINED"}}
        out.mkdir(exist_ok=False)
        for key,(filename,_) in CODECS.items():
            shutil.copyfile(temp/filename,out/filename)
            if sha(out/filename)!=reports[key]["sha256"]:raise ValueError("delivery readback mismatch")
        write_report(out/"delivery.json",report)
        print(json.dumps(report,indent=2,allow_nan=False))
        return report

def periodic(path,bad=False):
    with wave.open(str(path),"wb") as f:
        f.setparams((2,2,RATE,0,"NONE","not compressed"))
        data=bytearray()
        for i in range(RATE*2):
            v=round(8000*math.sin(2*math.pi*110*i/RATE)+2000*math.sin(2*math.pi*330*i/RATE))
            if bad and i>=RATE:data_value=v+10000
            else:data_value=v
            data.extend(struct.pack("<hh",data_value,round(data_value*.8)))
        f.writeframes(data)

def selftest(packet,out,ffmpeg):
    out.mkdir(parents=True,exist_ok=False)
    loop=out/"synthetic-loop.wav";periodic(loop)
    bad=out/"synthetic-bad-loop.wav";periodic(bad,True)
    shot=packet/"warm/candidate.wav";expected=json.loads((packet/"warm/receipt.json").read_text())["output_sha256"]
    a=export(loop,sha(loop),out/"loop","loop",ffmpeg)
    b=export(shot,expected,out/"oneshot","oneshot",ffmpeg)
    checks={"loop_source":a["source_seam"]["status"]=="PASS",
            "opus_loop":a["formats"]["opus"]["status"]=="PASS",
            "mp3_loop_not_certified":a["formats"]["mp3"]["status"]=="HOLD",
            "opus_oneshot":b["formats"]["opus"]["status"]=="PASS",
            "mp3_oneshot":b["formats"]["mp3"]["status"]=="PASS",
            "source_preserved":sha(shot)==expected and sha(loop)==a["source_sha256"]}
    def reject(key,fn):
        try:fn()
        except ValueError:checks[key]=True
        else:checks[key]=False
    reject("bad_seam",lambda:export(bad,sha(bad),out/"bad","loop",ffmpeg))
    reject("bad_sha",lambda:export(loop,"0"*64,out/"bad-sha","loop",ffmpeg))
    reject("overwrite",lambda:export(loop,sha(loop),out/"loop","loop",ffmpeg))
    write_report(out/"qualification.json",{"checks":checks,"all_pass":all(checks.values())})
    print("Delivery qualification:",json.dumps(checks))
    if not all(checks.values()):raise SystemExit("delivery qualification failed")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="mode",required=True)
    a=sub.add_parser("export");a.add_argument("source",type=Path);a.add_argument("sha256");a.add_argument("output",type=Path);a.add_argument("--role",choices=("loop","oneshot"),required=True)
    a=sub.add_parser("selftest");a.add_argument("packet",type=Path);a.add_argument("output",type=Path)
    args=p.parse_args();ffmpeg=shutil.which("ffmpeg")
    if not ffmpeg:raise RuntimeError("FFmpeg unavailable")
    if args.mode=="selftest":selftest(args.packet,args.output,ffmpeg)
    else:export(args.source,args.sha256,args.output,args.role,ffmpeg)
