# Builds the site for GitHub Pages: index.html, course.json, sw.js, manifest and icons.
# Run from the repo root: python3 tools/build.py
import json,glob,hashlib,os
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));os.chdir(R)

# ---- course content
plan=json.load(open("content/plan.json"))
am=[None]*60;pm=[None]*60
for f in sorted(glob.glob("content/ai/*.json")):          # lessons the AI made earlier, already in app format
    d,k=os.path.basename(f)[:-5].split("-");j=json.load(open(f))
    if k=="am":am[int(d)]=j
for f in sorted(glob.glob("content/b*.json")):            # prepared lessons, compact format
    for d,v in json.load(open(f)).items():
        d=int(d)
        if "am" in v:
            a=v["am"];am[d]={"goal_ru":a["g"],"phrases":[{"en":x[0],"ru":x[1],"note_ru":x[2] if len(x)>2 else ""} for x in a["p"]],
              "dialogue":[{"who":x[0],"en":x[1],"ru":x[2]} for x in a["d"]],"drill":[{"ru":x[0],"en":x[1]} for x in a["x"]]}
        if "pm" in v:
            a=v["pm"];assert len(a["c"])>=4,d
            pm[d]={"setup_ru":a["s"],"useful":[{"en":x[0],"ru":x[1]} for x in a["u"]],
              "script":[{"a":x[0],"a_ru":x[1],"q":x[2],"me":x[3]} for x in a["c"]],"bye":a.get("b","")}
course={"book":plan.get("book"),"days":plan["days"],"am":am,"pm":pm}
cj=json.dumps(course,ensure_ascii=False,separators=(",",":"))
open("course.json","w").write(cj)

# ---- page
src=open("src/app.src.html").read()
assert src.startswith("<title>")
head='''<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#f3f5f7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0f1720" media="(prefers-color-scheme: dark)">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Speak Up">
<style>html{padding-top:env(safe-area-inset-top,0px)}body{margin:0;-webkit-text-size-adjust:100%}</style>
'''
html=head+src.replace('<meta name="claude:viewport-fit-sides" content="cover">\n','')+"\n</html>\n"
open("index.html","w").write(html)

# ---- manifest
json.dump({"name":"Speak Up English","short_name":"Speak Up","lang":"ru","start_url":"./","scope":"./","display":"standalone",
  "background_color":"#f3f5f7","theme_color":"#1f5fbf",
  "icons":[{"src":"icon-192.png","sizes":"192x192","type":"image/png"},{"src":"icon-512.png","sizes":"512x512","type":"image/png"},
           {"src":"icon-512.png","sizes":"512x512","type":"image/png","purpose":"maskable"}]},open("manifest.webmanifest","w"),ensure_ascii=False,indent=1)

# ---- service worker: version = hash of everything it caches
h=hashlib.sha256()
for f in ["index.html","course.json","manifest.webmanifest","packs/index.json"]:h.update(open(f,"rb").read())
ver=h.hexdigest()[:10];pv=hashlib.sha256(open("packs/index.json","rb").read()).hexdigest()[:8]
open("sw.js","w").write(open("src/sw.template.js").read().replace("__VER__",ver).replace("__PACKS__",pv))
print("built",ver,"am:",sum(x is not None for x in am),"pm:",sum(x is not None for x in pm),"course.json",len(cj)//1024,"KB")
