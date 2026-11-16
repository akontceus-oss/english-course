# Generates the Emma voice (Kokoro bf_emma) for every English text the app can speak.
# Usage: python3 tools/gen_audio.py <kokoro.onnx> <voices.bin> [workdir]
# Output: packs/<name>.mp3 (concatenated clips) + packs/index.json {text: "pack:offset:length"}
import json,os,re,sys,subprocess,hashlib,time
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));os.chdir(R)
MODEL,VOICES=sys.argv[1],sys.argv[2];WORK=sys.argv[3] if len(sys.argv)>3 else "/tmp/emma-clips"
os.makedirs(WORK,exist_ok=True)
def split_speech(t):  # same as splitSpeech() in the app
    t=re.sub(r'([.!?…])\s+',r'\1\n',str(t))
    return [x.strip() for x in re.split(r'\n|\s+/\s+|\s+—\s+',t) if x.strip()]
c=json.load(open("course.json"))
groups=[]  # (pack, [texts])
UI=["Hi! Shall we have a coffee?","Hello! My name's Andrew. Nice to meet you. Shall we have a coffee?","Hello! Nice to meet you.","(No answer. Tap Send again.)"]
groups.append(("ui",UI))
for d in range(60):
    T=[];a=c["am"][d] or {};p=c["pm"][d] or {};n=c["days"][d].get("notes",{})
    T+=[x[0] for x in n.get("words",[])]+[x[0] for x in n.get("phrases",[])]+n.get("sentences",[])
    T+=[x["en"] for x in a.get("phrases",[])]+[x["en"] for x in a.get("dialogue",[])]+[x["en"] for x in a.get("drill",[])]
    T+=[x["en"] for x in p.get("useful",[])]+[x for s in p.get("script",[]) for x in (s["a"],s["me"])]+[p.get("bye","")]
    groups.append(("d%02d"%d,T))
groups.append(("pb",[x[0] for sec in c.get("phrasebook",[]) for x in sec["p"]]))
seen={};plan=[]
for pk,T in groups:
    for t in T:
        for part in split_speech(t):
            if part not in seen: seen[part]=pk;plan.append((pk,part))
print(len(plan),"clips",flush=True)
from kokoro_onnx import Kokoro
import soundfile as sf
k=Kokoro(MODEL,VOICES)
def fn(t):return os.path.join(WORK,hashlib.sha1(t.encode()).hexdigest()[:16]+".mp3")
t0=time.time()
for i,(pk,t) in enumerate(plan):
    f=fn(t)
    if os.path.exists(f):continue
    say=t
    if not re.search(r'[.!?…]$',say):say=say+"."   # a full stop gives a natural falling end
    s,sr=k.create(say,voice="bf_emma",speed=1.0,lang="en-gb")
    w=f[:-4]+".wav";sf.write(w,s,sr)
    subprocess.run(["ffmpeg","-v","error","-y","-i",w,"-af","silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse,apad=pad_dur=0.12","-ac","1","-ar","24000","-b:a","40k","-map_metadata","-1","-id3v2_version","0","-write_xing","0",f],check=True)
    os.remove(w)
    if i%100==0:print(i,round(time.time()-t0),"s",flush=True)
packs={};idx={}
for pk,t in plan:
    b=open(fn(t),"rb").read();buf=packs.setdefault(pk,bytearray());idx[t]=f"{pk}:{len(buf)}:{len(b)}";buf+=b
os.makedirs("packs",exist_ok=True)
for f in os.listdir("packs"):
    if f.endswith(".mp3"):os.remove(os.path.join("packs",f))
for pk,b in packs.items():open(f"packs/{pk}.mp3","wb").write(b)
json.dump(idx,open("packs/index.json","w"),ensure_ascii=False,separators=(",",":"))
print("done",len(idx),"clips",sum(len(b) for b in packs.values())//1024,"KB")
