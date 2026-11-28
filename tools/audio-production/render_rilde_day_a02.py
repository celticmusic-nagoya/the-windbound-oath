"""Rilde Day A02: expressive synthesis of the unchanged A01 score; candidate only."""
import argparse, array, hashlib, json, math, platform, random, shutil, struct, wave
from pathlib import Path
import render_rilde_day as a01
from process_audio import RATE, sha, run, measure
from inspect_audio import inspect_pair, write_report
from export_delivery import export

BASE_SCORE_SHA="4f88803d7e9a93d87f7108b02b77859b5cd7d0db8f9d6626fa86f0eef90ec67a"
BASE_OPUS_SHA="00ffc1e7c44bb5b44549a1464f170965985a082229820cca3eefc483ef8f3136"
SEED=20261128
N=a01.N
TAU=2*math.pi

def render(path):
    if sha(Path(a01.__file__))!=BASE_SCORE_SHA:
        raise ValueError("A01 score source changed; reconcile before A02")
    assert N==1152000 and len(a01.BARS)==16 and all(sum(d for _,d in bar)==6 for bar in a01.BARS)
    left=array.array("d",[0])*N;right=array.array("d",[0])*N
    rng=random.Random(SEED)
    events=[]
    def note(start,duration,midi,amp,pan,voice,accent=1.0):
        f=440*2**((midi-69)/12)
        start=int(start);length=int(duration*RATE)
        lg=math.sqrt((1-pan)/2)*amp*accent;rg=math.sqrt((1+pan)/2)*amp*accent
        detune=rng.uniform(-2.5,2.5);vib_rate=rng.uniform(4.5,5.7)
        f*=2**(detune/1200)
        phase=0.0;noise=0.0;last_noise=0.0
        attack=rng.uniform(.019,.036) if voice=="whistle" else rng.uniform(.055,.09)
        attack=max(.001,attack)
        bend=rng.uniform(-15,-5)
        events.append({"voice":voice,"start_frame":start,"frames":length,"midi":midi,"accent":round(accent,5)})
        for i in range(length):
            t=i/RATE;remain=duration-t
            if voice=="whistle":
                # Breath-supported attack, short pitch approach, delayed vibrato and air noise.
                env=min(1,t/attack,max(0,remain/.055))
                pressure=(.88+.12*math.sin(math.pi*min(1,t/duration)))*(.97+.03*math.sin(TAU*2.0*t))
                cents=bend*math.exp(-t/.022)+min(1,max(0,(t-.12)/.18))*6.0*math.sin(TAU*vib_rate*t)
                phase+=TAU*f*2**(cents/1200)/RATE
                noise=.66*noise+.34*rng.uniform(-1,1)
                air=noise-last_noise;last_noise=noise
                v=env*pressure*(math.sin(phase)+(.11+.09*pressure)*math.sin(2*phase)+.043*math.sin(3*phase)+(.026+.035*math.exp(-t/.045))*air)*.78
            elif voice=="harp":
                # Plucked-string model: excitation-dependent partial decay and short body resonance.
                phase+=TAU*f/RATE
                env=min(1,t/.004)*min(1,max(0,remain/.06))
                v=env*(math.sin(phase)*math.exp(-2.8*t)+.42*math.sin(2*phase)*math.exp(-5.3*t)+.23*math.sin(3.003*phase)*math.exp(-8*t)+.11*math.sin(4.008*phase)*math.exp(-13*t)+.052*math.sin(5.016*phase)*math.exp(-19*t))*.60
            else:
                # Soft bowed harmonic tone: asymmetric swell, delayed narrow vibrato, bow variation.
                env=min(1,t/attack,max(0,remain/.18))
                cents=2.5*math.sin(TAU*1.1*t)+min(1,max(0,(t-.09)/.24))*8.5*math.sin(TAU*vib_rate*t)
                phase+=TAU*f*2**(cents/1200)/RATE
                noise=.86*noise+.14*rng.uniform(-1,1)
                v=env*(.88+.12*math.sin(math.pi*min(1,t/duration)))*(math.sin(phase)+.33*math.sin(2*phase)+.19*math.sin(3*phase)+.10*math.sin(4*phase)+.065*math.sin(5*phase)+.018*noise)*.59
            j=(start+i)%N
            left[j]+=v*lg;right[j]+=v*rg
    for i,(bar,chord) in enumerate(zip(a01.BARS,a01.CHORDS)):
        start=i*6*a01.UNIT;step=0
        phrase=(.92,1.02,1.05,.92,1.04,1.0,.96,.90,1.07,1.03,1.04,.90,1.03,1.01,.96,.86)[i]
        for k,(pitch,d) in enumerate(bar):
            lag=rng.randint(80,420) if k else rng.randint(0,120)
            gate=.93 if d==1 else .97
            duration=(d*a01.UNIT-lag)/RATE*gate
            accent=phrase*(1.08 if step in (0,3) else .94)*rng.uniform(.965,1.035)
            note(start+step*a01.UNIT+lag,duration,pitch,.133 if i>=8 else .119,.10,"whistle",accent)
            step+=d
        # Preserve chord progression; vary arpeggiation without replacing lead notes.
        order=(0,1,2,3,2,1) if i%4!=3 else (0,2,1,3,1,2)
        for j,k in enumerate(order):
            lag=rng.randint(0,300)
            accent=(1.14 if j==0 else 1.02 if j==3 else .81)*phrase*rng.uniform(.92,1.08)
            note(start+j*a01.UNIT+lag,.90 if j in (0,3) else .68,chord[k]+(12 if j in (2,3,4) else 0),.069,-.38,"harp",accent)
        note(start,1.64,chord[0]-12,.044,-.12,"bow",phrase)
        note(start+180,1.60,chord[1],.031,.35,"bow",phrase)
        if i>=8 and i%2==0:
            note(start+3*a01.UNIT+110,.70,chord[2]+12,.034,.40,"bow",phrase)
    # Circular room response, no external impulse response. Short smooth boundary taper.
    a=array.array("d",left);b=array.array("d",right)
    for i in range(N):
        left[i]+=.090*b[(i-3024)%N]+.064*a[(i-8112)%N]+.034*b[(i-14112)%N]
        right[i]+=.090*a[(i-3792)%N]+.064*b[(i-9552)%N]+.034*a[(i-17424)%N]
    peak=max(max(map(abs,left)),max(map(abs,right)))
    scale=10**(-6/20)/peak
    fade=768
    with wave.open(str(path),"wb") as f:
        f.setparams((2,2,RATE,0,"NONE","not compressed"))
        raw=bytearray()
        for i in range(N):
            edge=min(1,i/fade,(N-1-i)/fade)
            edge=.5-.5*math.cos(math.pi*edge)
            raw.extend(struct.pack("<hh",round(left[i]*scale*edge*32767),round(right[i]*scale*edge*32767)))
        f.writeframes(raw)
    lead=[e["midi"] for e in events if e["voice"]=="whistle"]
    assert lead==[pitch for bar in a01.BARS for pitch,_ in bar]
    return events

def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    source=out/"source.wav";events=render(source);source_hash=sha(source)
    raw=measure(source)
    assert raw["frames"]==N and raw["channels"]==2 and raw["full_scale_samples"]==0
    candidate=run(source,source_hash,out/"clean","clean")
    ffmpeg=shutil.which("ffmpeg")
    if not ffmpeg:raise RuntimeError("FFmpeg unavailable")
    inspection=inspect_pair(source,out/"clean/candidate.wav",out/"clean/receipt.json",ffmpeg)
    write_report(out/"loudness.json",inspection)
    report=export(out/"clean/candidate.wav",candidate["output_sha256"],out/"loop","loop",ffmpeg)
    assert sha(source)==source_hash
    opus=report["formats"]["opus"]
    if opus["sha256"]==BASE_OPUS_SHA:raise ValueError("unchanged encoded candidate")
    review=out/"review";review.mkdir()
    for name in ("delivery.ogg","delivery.json"):
        shutil.copyfile(out/"loop"/name,review/name)
    shutil.copyfile(out/"loudness.json",review/"loudness.json")
    shutil.copyfile(out/"clean/receipt.json",review/"processing.json")
    score=json.dumps({"bars":a01.BARS,"chords":a01.CHORDS,"unit":a01.UNIT},separators=(",",":"))
    p={"schema":"two.audio.original-music-candidate.v1","candidate_only":True,"variant":"A02",
        "purpose":"Rilde daytime BGM expression comparison, no game binding",
        "source":"Original A01 score, new synthetic voices; no third-party samples or recordings",
        "base":{"variant":"A01","run_id":46138675450,"artifact_id":15260444465,"score_source_sha256":BASE_SCORE_SHA,
                "opus_sha256":BASE_OPUS_SHA,"integrated_lufs":-17.02,"true_peak_dbtp":-8.57,"duration_seconds":24},
        "renderer_sha256":sha(Path(__file__)),"score_sha256":hashlib.sha256(score.encode()).hexdigest(),
        "source_wav_sha256":source_hash,"processed_wav_sha256":candidate["output_sha256"],
        "python":platform.python_version(),"seed":SEED,"duration_seconds":N/RATE,
        "bars":16,"meter":"6/8","dotted_quarter_bpm":80,"boundary_taper_ms":16,
        "event_counts":{v:sum(e["voice"]==v for e in events) for v in ("whistle","harp","bow")},
        "lead_pitch_sequence_preserved":True,"harmonic_progression_preserved":True,
        "expression_changes":["seeded microtiming and phrase accents","breathy whistle attack and delayed vibrato",
                              "frequency-dependent pluck partial decay","bow swell and delayed vibrato","circular early room taps"],
        "source_pcm":raw,"opus_sha256":opus["sha256"],"opus_status":opus["status"],
        "decoded_loudness":opus["decoded_loudness"],"bytes":opus["bytes"],
        "qa":{"technical_delivery":opus["status"],"listening":"NOT_RUN","game":"NOT_RUN","android":"NOT_RUN","adoption":"UNDETERMINED"},
        "limits":"Synthetic expression experiment, not measured acoustic realism or established improvement. No loudness matching in encoded files; use level-matched listening for comparison."}
    write_report(review/"provenance.json",p)
    print("Rilde A02 candidate:",json.dumps(p))
    if opus["status"]!="PASS":raise SystemExit("candidate technical HOLD")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("output",type=Path)
    main(p.parse_args().output)
