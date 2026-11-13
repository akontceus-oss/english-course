# One-off: adds the no-AI (offline) mode, install tips, backup and update handling to src/app.src.html
import sys,re
p="src/app.src.html";s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(a[:80],s.count(a));s=s.replace(a,b)

# --- state: static course content
rep('let store=local, cloud=false, sample=null;','let store=local, cloud=false, sample=null, COURSE=null;\nconst IN_CLAUDE=!!(window.claude&&window.claude.use);')

# --- AI layer: fall back to prepared content when no AI
rep('async function genMorning(d){','async function genMorning(d){\n  if(!sample)return offMorning(d);')
rep('async function checkDrill(items){','async function checkDrill(items){\n  if(!sample)return offCheck(items);')
rep('async function roleTurn(d,msgs,scenario){','async function roleTurn(d,msgs,scenario){\n  if(!sample)return offTurn(d,msgs);')
rep('async function genScenario(d){','async function genScenario(d){\n  if(!sample)return offScenario(d);')
rep('async function wrapUp(d,msgs){','async function wrapUp(d,msgs){\n  if(!sample)return offWrap(d,msgs);')

OFF=r'''
// ---------- Without AI: prepared lessons, self-check and scripted role-play ----------
function normEn(t){return String(t||"").toLowerCase().replace(/[’`]/g,"'")
  .replace(/\bi'm\b/g,"i am").replace(/n't\b/g," not").replace(/'re\b/g," are").replace(/'ve\b/g," have").replace(/'ll\b/g," will").replace(/'d\b/g," would")
  .replace(/\b(it|that|he|she|what|where|who|there|here)'s\b/g,"$1 is").replace(/\bcan not\b/g,"cannot").replace(/\bwo not\b/g,"will not")
  .replace(/colour/g,"color").replace(/favourite/g,"favorite").replace(/metre/g,"meter")
  .replace(/[^a-z0-9' ]+/g," ").replace(/'s\b/g,"s").replace(/'/g,"").split(/\s+/).filter(Boolean)}
function simEn(a,b){const x=normEn(a),y=normEn(b);if(!x.length||!y.length)return 0;
  const m=new Map();y.forEach(w=>m.set(w,(m.get(w)||0)+1));let hit=0;x.forEach(w=>{if(m.get(w)>0){hit++;m.set(w,m.get(w)-1)}});
  const pr=hit/x.length,rc=hit/y.length;return pr+rc?2*pr*rc/(pr+rc):0}
function noContent(){return Promise.reject({code:"no_content"})}
function offMorning(d){const a=COURSE&&COURSE.am&&COURSE.am[d];if(!a)return noContent();return Promise.resolve(a)}
function offScenario(d){const a=COURSE&&COURSE.pm&&COURSE.pm[d];if(!a)return noContent();return Promise.resolve(a)}
function offCheck(items){return Promise.resolve({results:items.map(x=>{const v=simEn(x.learner,x.model);const ok=v>=0.75;
  return {ok,natural:x.model,tip_ru:ok?(v<0.99?"Смысл верный. Сравни с образцом.":""):(x.learner==="(empty)"?"Скажи образец вслух 3 раза.":"Сравни с образцом и произнеси его вслух 3 раза.")}})})}
function offTurn(d,msgs){const sc=S.sess&&S.sess.data;const c=(sc&&sc.script)||[];const mine=msgs.filter(m=>m.who==="me");const i=mine.length;
  let fix=null;const last=mine[i-1];
  if(last&&c[i-1]){const v=simEn(last.en,c[i-1].me);last.score=v;if(v<0.9)fix={said:last.en,better:c[i-1].me,why_ru:v>=0.6?"Почти! Так звучит естественнее.":"Образец ответа: прочитай его вслух."}}
  if(i<c.length)return Promise.resolve({reply:c[i].a,reply_ru:c[i].a_ru,task_ru:c[i].q,hint_ru:"Например: "+c[i].me,fix});
  S.sess.over=true;return Promise.resolve({reply:sc.bye||"Thanks for the chat! Bye!",reply_ru:"",task_ru:"",hint_ru:"",fix})}
function offWrap(d,msgs){const sc=S.sess.data,c=sc.script||[];const mine=msgs.filter(m=>m.who==="me");
  const sc5=mine.length?mine.reduce((a,m,i)=>a+(m.score!=null?m.score:simEn(m.en,(c[i]||{}).me||m.en)),0)/mine.length:0;
  const score=Math.max(2,Math.min(5,Math.round(1+sc5*4.4)));
  const mistakes=mine.map((m,i)=>m.fix?{said:m.en,better:m.fix.better,why_ru:""}:null).filter(Boolean).slice(0,5);
  const praise_ru=score>=5?"Отлично! Ответы почти совпали с образцами.":score>=4?"Хороший разговор! Пара мест, где можно сказать естественнее.":"Разговор состоялся, это главное. Прочитай образцы ниже вслух и попробуй ещё раз.";
  return Promise.resolve({praise_ru,mistakes,phrases:(sc.useful||[]).concat(c.slice(0,2).map(x=>({en:x.me,ru:x.q}))),score})}
'''
rep('\n// ---------- Rendering ----------',OFF+'\n// ---------- Rendering ----------')

# --- prepared content is not cached into the store (so edits reach the phone)
rep('    let data=await store.get(key);\n    if(!data){data=kind==="am"?await genMorning(S.sess.day):await genScenario(S.sess.day);await store.set(key,data)}',
    '    let data=sample?await store.get(key):null;\n    if(!data){data=kind==="am"?await genMorning(S.sess.day):await genScenario(S.sess.day);if(sample)await store.set(key,data)}')

# --- errors
rep('s.err.code==="not_granted"?','s.err.code==="no_content"?"Урок для этого дня ещё в работе. Он появится сам, когда приложение обновится.":s.err.code==="not_granted"?')

# --- texts on the Today screen
a=re.search(r'\$\{!cloud\?`<div class="tip">.*?`:""\}\n',s).group(0);rep(a,'${IN_CLAUDE&&!cloud?`<div class="tip">История сейчас хранится только в этом браузере. Открой приложение через claude.ai, чтобы она сохранялась в аккаунте.</div>`:""}\n${installTip()}\n')
a=re.search(r'  \$\{!sample\?`<div class="tip">ИИ-партнёр.*?`:""\}\n',s).group(0);rep(a,'  ${IN_CLAUDE&&!sample?`<div class="tip">ИИ-партнёр недоступен в этом просмотре. Открой приложение в claude.ai и разреши ему обращаться к Claude.</div>`:""}\n')
rep('Повтор слов и живой диалог с ИИ','Повтор слов и ${sample?"живой диалог с ИИ":"диалог по ролям"}')

# --- role-play UI: always show the task, hide input when the script is over
rep('${s.msgs.length&&!s.busy?`${s.hint&&s.showHint?`<div class="tip">${esc(s.hint)}</div>`:""}',
    '${s.msgs.length&&!s.busy&&s.over?`<div class="tip">Разговор окончен. Нажми «Закончить разговор и разобрать».</div>`:""}\n    ${s.msgs.length&&!s.busy&&!s.over?`${s.task?`<div class="tip"><b>Твоя реплика:</b> ${esc(s.task)}</div>`:""}${s.hint&&s.showHint?`<div class="tip">${esc(s.hint)}</div>`:""}')
rep('s.msgs.push({who:"ai",en:r.reply,ru:r.reply_ru});s.hint=r.hint_ru;','s.msgs.push({who:"ai",en:r.reply,ru:r.reply_ru});s.hint=r.hint_ru;s.task=r.task_ru||"";')
rep('case "send":{const v=document.getElementById("say").value.trim();if(!v)return;',
    'case "send":{const v=document.getElementById("say").value.trim();if(!v||s.over)return;')

# --- backup on the History screen
m=re.search(r'(function renderHistory\(\)\{.*?)(\n\})',s,re.S)
body=m.group(1)
assert body.rstrip().endswith('`;'),body[-80:]
s=s.replace(m.group(0),body.rstrip()[:-2]+'''${backupCard()}`;
}
function installTip(){if(IN_CLAUDE)return "";const sa=window.navigator.standalone||matchMedia("(display-mode: standalone)").matches;if(sa)return "";
  const ios=/iphone|ipad|ipod/i.test(navigator.userAgent);if(!ios)return "";
  return `<div class="tip"><b>Сделай из сайта приложение:</b> нажми «Поделиться» внизу Safari и выбери «На экран „Домой“». Прогресс сохраняется на этом iPhone.</div>`}
function backupCard(){if(IN_CLAUDE)return "";return `<div class="card"><h3>Резервная копия</h3><p class="small muted">Прогресс хранится на этом телефоне. Время от времени сохраняй копию в «Файлы», чтобы ничего не потерять, если удалишь приложение с экрана.</p>
  <div class="row"><button class="btn soft sm" id="bk-save">Сохранить копию</button><button class="btn soft sm" id="bk-load">Восстановить из файла</button></div><input type="file" id="bk-file" accept=".json,application/json" hidden></div>`}
function backupSave(){const o={};for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k.startsWith(LS))o[k]=localStorage.getItem(k)}
  const f=new File([JSON.stringify({app:"speakup",date:today(),data:o})],`speakup-backup-${today()}.json`,{type:"application/json"});
  if(navigator.canShare&&navigator.canShare({files:[f]})){navigator.share({files:[f]}).catch(()=>{});return}
  const a=document.createElement("a");a.href=URL.createObjectURL(f);a.download=f.name;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},1000)}
async function backupLoad(file){try{const j=JSON.parse(await file.text());if(j.app!=="speakup"||!j.data)throw 0;
  Object.entries(j.data).forEach(([k,v])=>{if(k.startsWith(LS))localStorage.setItem(k,v)});location.reload()}catch(e){alert("Это не файл копии Speak Up.")}}''')
rep('    case "towrap":s.step=2;toWrap();break;','    case "towrap":s.step=2;toWrap();break;\n    case "bk-save":backupSave();break;\n    case "bk-load":document.getElementById("bk-file").click();break;')
rep('document.addEventListener("change",e=>{','document.addEventListener("change",e=>{if(e.target.id==="bk-file"&&e.target.files[0]){backupLoad(e.target.files[0]);return}')

# --- boot: load prepared course, service worker with safe auto-update
rep('  await Promise.all([initCaps(),loadAudioIndex()]);','  await Promise.all([initCaps(),loadAudioIndex(),loadCourse()]);')
rep('    if(plan&&Array.isArray(plan.days)&&plan.days.length){plan.days.forEach((x,i)=>{if(PLAN[i])Object.assign(PLAN[i],x)})}',
    '    const pl=plan&&Array.isArray(plan.days)&&plan.days.length?plan:(COURSE&&COURSE.days?COURSE:null);\n    if(pl){pl.days.forEach((x,i)=>{if(PLAN[i])Object.assign(PLAN[i],x)})}')
rep('// ---------- Boot ----------','''// ---------- Boot ----------
async function loadCourse(){try{const r=await fetch("course.json",{cache:"no-cache"});if(r.ok)COURSE=await r.json()}catch(e){}}
let reloadPending=false;
function setupSW(){if(IN_CLAUDE||!("serviceWorker" in navigator)||location.protocol!=="https:")return;
  const had=!!navigator.serviceWorker.controller;
  navigator.serviceWorker.register("sw.js").then(reg=>{
    document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")reg.update().catch(()=>{})});
    setInterval(()=>reg.update().catch(()=>{}),30*60*1000)}).catch(()=>{});
  navigator.serviceWorker.addEventListener("controllerchange",()=>{if(!had)return;if(S.view==="session"){reloadPending=true}else location.reload()})}
setupSW();''')
rep('function setView(v){S.view=v;','function setView(v){if(reloadPending&&v!=="session"){location.reload();return}S.view=v;')
open(p,"w").write(s);print("ok")
