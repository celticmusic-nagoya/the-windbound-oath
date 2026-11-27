"""Offline, candidate-only audio processing. No Waves binary or game mutation."""
import argparse, hashlib, json, math, os, re, shutil, struct, subprocess, tempfile, wave
from pathlib import Path

RATE = 48000
MAX_FRAMES = RATE * 120
CHAINS = {
    "clean": "highpass=f=40,volume=-3dB",
    "warm": "highpass=f=40,equalizer=f=240:t=q:w=0.9:g=1.5,acompressor=threshold=0.25:ratio=2:attack=15:release=120:makeup=1,asoftclip=type=tanh:threshold=0.9:output=0.85,volume=-3dB",
}
def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def measure(path):
    with wave.open(str(path), "rb") as f:
        channels, width, rate, frames = f.getnchannels(), f.getsampwidth(), f.getframerate(), f.getnframes()
        if channels not in (1,2) or width != 2 or rate != RATE or not 0 < frames <= MAX_FRAMES or f.getcomptype() != "NONE":
            raise ValueError("require PCM16 WAV, 48 kHz, mono/stereo, <=120 seconds")
        peak = count = energy = clips = 0
        while count < frames * channels:
            raw = f.readframes(8192)
            if not raw:
                break
            for (v,) in struct.iter_unpack("<h", raw):
                peak = max(peak, abs(v))
                energy += v*v
                clips += int(v in (-32768,32767))
                count += 1
        if count != frames*channels:
            raise ValueError("truncated PCM")
        db = lambda x: 20*math.log10(x/32768) if x else None
        return dict(channels=channels, sample_rate=rate, frames=frames,
                    sample_peak_dbfs=db(peak), rms_dbfs=db(math.sqrt(energy/count)),
                    full_scale_samples=clips)

def run(source, expected, output, preset):
    source, output = Path(source), Path(output)
    if source.is_symlink() or not source.is_file() or source.suffix.lower() != ".wav":
        raise ValueError("local WAV file required")
    if not re.fullmatch("[0-9a-f]{64}", expected) or sha(source) != expected:
        raise ValueError("source SHA mismatch")
    if preset not in CHAINS or output.exists() or output.is_symlink():
        raise ValueError("invalid preset or output already exists")
    if source.stat().st_size > 24*1024**2:
        raise ValueError("source exceeds byte budget")
    before = measure(source)
    if before["sample_peak_dbfs"] is None:
        raise ValueError("silent input")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg unavailable")
    version = subprocess.check_output([ffmpeg,"-version"],text=True,timeout=10).splitlines()[0]
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent,prefix=".audio-") as temp:
        dest = Path(temp)/"candidate.wav"
        subprocess.run([ffmpeg,"-nostdin","-hide_banner","-loglevel","error","-n",
                        "-i",str(source.resolve()),"-map","0:a:0","-vn","-map_metadata","-1",
                        "-af",CHAINS[preset],"-c:a","pcm_s16le","-ar",str(RATE),
                        "-threads","1",str(dest)],check=True,timeout=180)
        after = measure(dest)
        if (after["channels"] != before["channels"] or after["frames"] != before["frames"]
            or after["sample_peak_dbfs"] is None or after["sample_peak_dbfs"] > -1
            or after["full_scale_samples"] or sha(source) != expected):
            raise ValueError("audio QA failed: duration/channels/headroom/source integrity")
        receipt = dict(schema="two.audio.candidate.v1",candidate_only=True,
                       backend=version,backend_sha256=sha(ffmpeg),preset=preset,filter=CHAINS[preset],
                       source_sha256=expected,output_sha256=sha(dest),before=before,after=after,
                       qa={"pcm_format":"PASS","source_integrity":"PASS","sample_peak":"PASS",
                           "duration_channels":"PASS","listening":"NOT_RUN","true_peak":"NOT_RUN",
                           "lufs":"NOT_RUN","loop_seam":"NOT_RUN","game":"NOT_RUN"})
        output.mkdir(exist_ok=False)
        shutil.copyfile(dest,output/"candidate.wav")
        (output/"receipt.json").write_text(json.dumps(receipt,indent=2,allow_nan=False)+"\n")
        if sha(output/"candidate.wav") != receipt["output_sha256"]:
            raise ValueError("output readback mismatch")
        return receipt

def fixture(path, channels=2, silent=False):
    with wave.open(str(path),"wb") as f:
        f.setparams((channels,2,RATE,0,"NONE","not compressed"))
        raw = bytearray()
        for i in range(RATE*2):
            t=i/RATE
            envelope=min(1,t*100,(2-t)*100)
            a=0 if silent else round(30000*envelope*(0.72*math.sin(2*math.pi*220*t)+0.20*math.sin(2*math.pi*660*t)))
            raw.extend(struct.pack("<"+"h"*channels,*([a] if channels==1 else [a,round(a*.7)])))
        f.writeframes(raw)

def selftest(root):
    root=Path(root)
    root.mkdir(exist_ok=False,parents=True)
    source=root/"synthetic-stereo.wav"
    fixture(source)
    original=sha(source)
    clean=run(source,original,root/"clean","clean")
    warm=run(source,original,root/"warm","warm")
    again=run(source,original,root/"warm-repeat","warm")
    mono=root/"synthetic-mono.wav"
    fixture(mono,1)
    m=run(mono,sha(mono),root/"mono","warm")
    checks={"source_unchanged":sha(source)==original,"warm_distinct":warm["output_sha256"]!=clean["output_sha256"],
            "same_runtime_repeat":warm["output_sha256"]==again["output_sha256"],"stereo":warm["after"]["channels"]==2,
            "mono":m["after"]["channels"]==1}
    def rejected(name, fn):
        try:
            fn()
        except ValueError:
            checks[name]=True
        else:
            checks[name]=False
    rejected("wrong_sha",lambda:run(source,"0"*64,root/"bad","warm"))
    rejected("no_overwrite",lambda:run(source,original,root/"warm","clean"))
    silent=root/"synthetic-silent.wav"
    fixture(silent,1,True)
    rejected("silence",lambda:run(silent,sha(silent),root/"silent","warm"))
    rejected("unknown_preset",lambda:run(source,original,root/"bad-preset","arbitrary"))
    (root/"qualification.json").write_text(json.dumps({"checks":checks,"all_pass":all(checks.values()),
        "limits":"Synthetic PCM only; no listening, true peak, LUFS, loops, browser/game, Waves, or cross-run bit-exact certification."},indent=2)+"\n")
    print(json.dumps({"checks":checks,"clean":clean["after"],"warm":warm["after"],"backend":warm["backend"]},indent=2))
    if not all(checks.values()):
        raise SystemExit("qualification failed")

if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="mode",required=True)
    q=sub.add_parser("process");q.add_argument("source",type=Path);q.add_argument("sha256");q.add_argument("output",type=Path);q.add_argument("--preset",choices=CHAINS,required=True)
    q=sub.add_parser("selftest");q.add_argument("output",type=Path)
    a=p.parse_args()
    if a.mode=="selftest":
        selftest(a.output)
    else:
        print(json.dumps(run(a.source,a.sha256,a.output,a.preset),indent=2))
