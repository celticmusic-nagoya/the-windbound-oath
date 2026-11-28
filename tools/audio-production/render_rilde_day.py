"""Original Rilde daytime musical sketch; no borrowed melody, samples or game mutation."""
import argparse, array, hashlib, json, math, platform, shutil, struct, sys, wave
from pathlib import Path
from process_audio import RATE, sha, run, measure
from inspect_audio import inspect_pair, write_report
from export_delivery import export, seam

# 16 bars in 6/8, dotted-quarter = 80 BPM; exactly 24 seconds at 48 kHz.
# Original note/duration score, not a transcription or an existing tune.
UNIT=12000
BARS=(
 ((74,2),(76,1),(78,2),(81,1)),
 ((79,1),(78,1),(76,1),(74,2),(69,1)),
 ((71,2),(74,1),(76,1),(78,1),(76,1)),
 ((74,3),(69,2),(71,1)),
 ((74,1),(76,1),(78,1),(81,2),(83,1)),
 ((81,2),(78,1),(76,2),(74,1)),
 ((79,2),(76,1),(78,1),(76,1),(71,1)),
 ((74,4),(76,2)),
 ((81,2),(83,1),(86,2),(83,1)),
 ((81,1),(78,1),(76,1),(78,2),(81,1)),
 ((79,1),(81,1),(79,1),(76,2),(74,1)),
 ((71,3),(74,3)),
 ((78,2),(81,1),(83,2),(81,1)),
 ((79,1),(78,1),(76,1),(74,2),(71,1)),
 ((69,2),(71,1),(74,1),(76,1),(78,1)),
 ((74,6),)
)
CHORDS=((50,57,62,66),(50,57,62,66),(47,54,59,62),(45,52,57,61),
        (50,57,62,66),(47,54,59,62),(55,62,67,71),(50,57,62,66),
        (47,54,59,62),(50,57,62,66),(55,62,67,71),(45,52,57,61),
        (47,54,59,62),(55,62,67,71),(45,52,57,61),(50,57,62,66))
N=len(BARS)*6*UNIT
TAU=2*math.pi

def render(path):
    assert len(BARS)==len(CHORDS)==16 and all(sum(d for _,d in bar)==6 for bar in BARS)
    left=array.array("d",[0])*N;right=array.array("d",[0])*N
    def note(start,duration,midi,amp,pan,voice):
        f=440*2**((midi-69)/12)
        lg=math.sqrt((1-pan)/2)*amp;rg=math.sqrt((1+pan)/2)*amp
        length=int(duration*RATE)
        for i in range(length):
            t=i/RATE
            if voice=="whistle":
                env=min(1,t/.035,max(0,(duration-t)/.07))
                phase=TAU*f*t+.075*math.sin(TAU*5.1*t)
                v=env*(math.sin(phase)+.18*math.sin(2*phase)+.055*math.sin(3*phase))*.78
            elif voice=="harp":
                env=min(1,t/.005)*math.exp(-4.1*t)*min(1,max(0,(duration-t)/.07))
                phase=TAU*f*t
                v=env*(math.sin(phase)+.32*math.sin(2*phase)*math.exp(-2*t)+.13*math.sin(3*phase)*math.exp(-3*t))*.68
            else:
                env=min(1,t/.14,max(0,(duration-t)/.20))
                phase=TAU*f*t+.12*math.sin(TAU*4.3*t)
                v=env*(math.sin(phase)+.25*math.sin(2*phase)+.10*math.sin(3*phase))*.65
            j=(start+i)%N
            left[j]+=v*lg;right[j]+=v*rg
    for i,(bar,chord) in enumerate(zip(BARS,CHORDS)):
        start=i*6*UNIT;step=0
        for pitch,d in bar:
            note(start+step*UNIT,d*UNIT/RATE-.012,pitch,.12 if i<8 else .135,.12,"whistle")
            step+=d
        for j,k in enumerate((0,1,2,3,2,1)):
            note(start+j*UNIT,.78,chord[k]+(12 if j in (2,3,4) else 0),.080 if j in (0,3) else .052,-.44,"harp")
        note(start,1.64,chord[0]-12,.047,.12,"bow")
        note(start,1.64,chord[1],.035,.43,"bow")
        if i>=8 and i%2==0:
            note(start+3*UNIT,.70,chord[2]+12,.031,.42,"bow")
    # Circular short stereo room taps, then fixed headroom and documented 8 ms boundary taper.
    a=array.array("d",left);b=array.array("d",right)
    for i in range(N):
        left[i]+=.105*b[(i-8112)%N]+.045*a[(i-16224)%N]
        right[i]+=.105*a[(i-9552)%N]+.045*b[(i-19104)%N]
    peak=max(max(map(abs,left)),max(map(abs,right)))
    scale=(10**(-6/20))/peak
    fade=384
    with wave.open(str(path),"wb") as f:
        f.setparams((2,2,RATE,0,"NONE","not compressed"))
        raw=bytearray()
        for i in range(N):
            edge=min(1,i/fade,(N-1-i)/fade)
            raw.extend(struct.pack("<hh",round(left[i]*scale*edge*32767),round(right[i]*scale*edge*32767)))
        f.writeframes(raw)

def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    source=out/"source.wav";render(source);source_hash=sha(source)
    raw=measure(source)
    assert raw["frames"]==N and raw["channels"]==2 and raw["full_scale_samples"]==0
    # New musical input exercises existing qualified pipeline, not another test tone.
    candidate=run(source,source_hash,out/"clean","clean")
    ffmpeg=shutil.which("ffmpeg")
    inspection=inspect_pair(source,out/"clean/candidate.wav",out/"clean/receipt.json",ffmpeg)
    write_report(out/"loudness.json",inspection)
    report=export(out/"clean/candidate.wav",candidate["output_sha256"],out/"loop","loop",ffmpeg)
    assert sha(source)==source_hash
    # Publish only new, original compressed audition candidates and receipts, never source WAV.
    review=out/"review";review.mkdir()
    for name in ("delivery.ogg","delivery.json"):
        shutil.copyfile(out/"loop"/name,review/name)
    shutil.copyfile(out/"loudness.json",review/"loudness.json")
    shutil.copyfile(out/"clean/receipt.json",review/"processing.json")
    provenance={"schema":"two.audio.original-music-candidate.v1","candidate_only":True,
        "purpose":"Rilde daytime BGM candidate, no game binding",
        "source":"newly authored algorithmic score and synthesis; no third-party recordings, samples, melodies or licensed plug-ins imported",
        "score_sha256":sha(Path(__file__)),"python":platform.python_version(),
        "source_wav_sha256":source_hash,"processed_wav_sha256":candidate["output_sha256"],
        "bars":16,"meter":"6/8","dotted_quarter_bpm":80,"duration_seconds":N/RATE,
        "voices":["synthetic whistle-like lead","synthetic harp-like plucks","synthetic bowed/drone accompaniment"],
        "boundary_taper_ms":8,"source_pcm":raw,
        "opus_status":report["formats"]["opus"]["status"],"opus_sha256":report["formats"]["opus"]["sha256"],
        "qa":{"technical_delivery":report["formats"]["opus"]["status"],"listening":"NOT_RUN","game":"NOT_RUN","android":"NOT_RUN","adoption":"UNDETERMINED"},
        "limits":"Musical sketch, not an acoustic performance. Original source is reproducible from this script; WAV not published in review packet. Cross-runtime bit-exact rendering not claimed."}
    write_report(review/"provenance.json",provenance)
    print("Rilde music candidate:",json.dumps(provenance))
    if provenance["opus_status"]!="PASS":raise SystemExit("candidate technical HOLD")
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("output",type=Path)
    main(p.parse_args().output)
