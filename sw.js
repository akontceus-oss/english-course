// Speak Up service worker. Pages and lessons: network first (so edits arrive at once), cache when offline.
// Audio packs: cache first, kept across versions until packs/index.json changes.
const VER="d27b2fdf4d",CORE="core-"+VER,AUDIO="audio-d913cd97",FONTS="fonts";
const PRE=["./","index.html","course.json","manifest.webmanifest","apple-touch-icon.png","icon-192.png","icon-512.png","packs/index.json"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(CORE).then(c=>c.addAll(PRE.map(u=>new Request(u,{cache:"reload"})))).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CORE&&k!==AUDIO&&k!==FONTS).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
function timeout(ms){return new Promise((_,j)=>setTimeout(()=>j(new Error("timeout")),ms))}
async function networkFirst(req){const c=await caches.open(CORE);
  try{const r=await Promise.race([fetch(req,{cache:"no-cache"}),timeout(4000)]);if(r&&r.ok)c.put(req,r.clone());return r}
  catch(e){const m=await c.match(req,{ignoreSearch:true})||(req.mode==="navigate"?await c.match("index.html"):null);if(m)return m;throw e}}
async function cacheFirst(req,name){const c=await caches.open(name);const m=await c.match(req);if(m)return m;
  const r=await fetch(req);if(r&&(r.ok||r.type==="opaque"))c.put(req,r.clone());return r}
self.addEventListener("fetch",e=>{const req=e.request;if(req.method!=="GET")return;const u=new URL(req.url);
  if(u.origin===location.origin){
    if(/\/packs\/p[0-9a-f]\.mp3$/.test(u.pathname)){e.respondWith(cacheFirst(req,AUDIO));return}
    e.respondWith(networkFirst(req));return}
  if(/fonts\.(googleapis|gstatic)\.com$/.test(u.hostname))e.respondWith(cacheFirst(req,FONTS));});
