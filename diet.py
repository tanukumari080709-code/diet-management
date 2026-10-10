<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Diet Management System</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://pyscript.net/releases/2024.11.1/core.css">
<style>
:root{--ink:#17251f;--leaf:#2d6a4f;--mint:#dff0e6;--paper:#f5f7f4;--gold:#e3a72f;--line:#cfd9d2;--r:10px}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 "Bricolage Grotesque",system-ui,sans-serif}
header{background:var(--ink);color:#fff;padding:22px 5vw;display:flex;flex-wrap:wrap;gap:8px 24px;align-items:end;justify-content:space-between}
h1{margin:0;font-size:clamp(1.6rem,4vw,2.6rem);font-weight:800;letter-spacing:-.02em}
header p{margin:4px 0 0;color:#b9cbc1;max-width:52ch}
#status{font-size:.85rem;padding:4px 12px;border-radius:99px;background:#33433b;color:#f0d9a0}
#status.ok{background:var(--leaf);color:#fff}
.wrap{display:grid;grid-template-columns:minmax(280px,360px) 1fr;gap:24px;padding:24px 5vw;align-items:start}
@media(max-width:860px){.wrap{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--line);border-radius:var(--r);padding:20px}
h2{margin:0 0 12px;font-size:1.2rem}h3{margin:18px 0 6px;font-size:1.05rem}
label{display:block;font-size:.88rem;font-weight:600;margin:12px 0 4px}
input,select,button{font:inherit}
input[type=text],input[type=number],input[type=date],select{width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:8px;background:#fff}
input:focus-visible,select:focus-visible,button:focus-visible{outline:3px solid var(--gold);outline-offset:1px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.checks{display:flex;flex-wrap:wrap;gap:6px 14px}.checks label{display:flex;gap:6px;align-items:center;margin:4px 0;font-weight:400}
button{cursor:pointer;border:0;border-radius:8px;padding:10px 18px;background:var(--leaf);color:#fff;font-weight:600}
button.alt{background:var(--mint);color:var(--ink)}button:hover{filter:brightness(1.08)}
.full{width:100%;margin-top:18px}
#err{color:#a12a1a;font-size:.9rem;min-height:1.3em;margin:10px 0 0}
.photo{display:flex;gap:14px;align-items:center}
.avatar{width:84px;height:84px;border-radius:50%;background:var(--mint);object-fit:cover;display:grid;place-items:center;font-weight:800;font-size:1.6rem;color:var(--leaf);flex:none;overflow:hidden}
.note{font-size:.8rem;color:#5b6b63;margin:6px 0 0}
.hello{display:flex;gap:16px;align-items:center;margin-bottom:16px}.hello h2{margin:0;font-size:1.6rem}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:16px}
.stat{background:var(--mint);border-radius:var(--r);padding:12px}.stat b{display:block;font-size:1.5rem;font-weight:800}.stat span{font-size:.82rem;color:#385246}
.stat.gold{background:#f8e8bd}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}
.tabs button{background:#fff;color:var(--ink);border:1px solid var(--line)}.tabs button[aria-selected=true]{background:var(--ink);color:#fff;border-color:var(--ink)}
.panel{display:none}.panel.on{display:block}
table{width:100%;border-collapse:collapse;font-size:.92rem}th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line)}th{font-weight:600;background:#f0f4f1}
.scroll{overflow-x:auto}
tr.unsafe td{color:#9a5a50;text-decoration:line-through}
.chatlog{height:300px;overflow:auto;border:1px solid var(--line);border-radius:8px;padding:10px;background:var(--paper);display:flex;flex-direction:column;gap:8px}
.msg{max-width:85%;padding:8px 12px;border-radius:12px;background:#fff;border:1px solid var(--line)}.msg.me{align-self:flex-end;background:var(--leaf);color:#fff;border-color:var(--leaf)}
.inline{display:flex;gap:8px;margin-top:10px}
.empty{padding:40px 20px;text-align:center;color:#5b6b63}
footer{padding:0 5vw 30px;font-size:.82rem;color:#5b6b63;max-width:90ch}
@media print{.noprint{display:none!important}.wrap{display:block;padding:0}.card{border:0;padding:0}header{background:none;color:#000;padding:0 0 10px}.panel{display:none!important}.panel#p-report{display:block!important}}
</style>
</head>
<body>
<header class="noprint">
  <div><h1>Diet Management System</h1><p>Tell us about yourself and get a personalised daily meal plan, calculated by a Python engine running in your browser.</p></div>
  <span id="status">Loading Python engine…</span>
</header>

<main class="wrap">
  <aside class="card noprint">
    <h2>Your profile</h2>
    <form id="form" novalidate>
      <div class="photo">
        <div class="avatar" id="avatar">?</div>
        <div><button type="button" class="alt" id="pick">Select photo</button><input type="file" id="file" accept="image/*" hidden>
        <p class="note">Used as your profile picture only. It is never analysed and stays in this browser.</p></div>
      </div>
      <label for="name">Name</label><input type="text" id="name" name="name" autocomplete="name">
      <div class="row">
        <div><label for="age">Age</label><input type="number" id="age" name="age" min="12" max="90"></div>
        <div><label for="gender">Gender</label><select id="gender" name="gender"><option>Male</option><option>Female</option><option>Other</option></select></div>
        <div><label for="height">Height (cm)</label><input type="number" id="height" name="height" min="100" max="250"></div>
        <div><label for="weight">Weight (kg)</label><input type="number" id="weight" name="weight" min="25" max="250" step="0.1"></div>
      </div>
      <label for="activity">Activity level</label>
      <select id="activity" name="activity"><option>Sedentary</option><option selected>Lightly Active</option><option>Moderately Active</option><option>Very Active</option></select>
      <label for="diet">Diet type</label>
      <select id="diet" name="diet"><option>Vegetarian</option><option>Non-Vegetarian</option><option>Vegan</option></select>
      <label for="goal">Goal</label>
      <select id="goal" name="goal"><option>Maintain general fitness</option><option>Healthy weight management</option><option>Improve nutrition</option></select>
      <label>Food allergies</label>
      <div class="checks"><label><input type="checkbox" name="al" value="Peanuts">Peanuts</label><label><input type="checkbox" name="al" value="Milk">Milk</label><label><input type="checkbox" name="al" value="Eggs">Eggs</label><label><input type="checkbox" name="al" value="Soy">Soy</label></div>
      <label for="other">Other allergies (comma separated)</label><input type="text" id="other" name="other" placeholder="e.g. fish, tree nuts">
      <button class="full" type="submit">Create profile and generate plan</button>
      <p id="err" role="alert"></p>
    </form>
  </aside>

  <section>
    <div id="empty" class="card empty"><h2>Your dashboard will appear here</h2><p>Fill in your profile and choose “Create profile and generate plan”.</p></div>
    <div id="dash" hidden>
      <div class="card noprint">
        <div class="hello"><div class="avatar" id="avatar2">?</div><div><h2 id="welcome"></h2><span id="sub" class="note"></span></div></div>
        <div class="stats" id="stats"></div>
        <div class="tabs" role="tablist">
          <button role="tab" aria-selected="true" data-tab="plan">Diet plan</button>
          <button role="tab" aria-selected="false" data-tab="foods">Food database</button>
          <button role="tab" aria-selected="false" data-tab="progress">Progress</button>
          <button role="tab" aria-selected="false" data-tab="chat">AI assistant</button>
          <button role="tab" aria-selected="false" data-tab="report">Report</button>
        </div>
      </div>
      <div class="card" style="margin-top:16px">
        <div class="panel on" id="p-plan"></div>
        <div class="panel" id="p-foods">
          <h2>Food database</h2><input type="text" id="q" placeholder="Search food, category or diet (e.g. paneer, legume, vegan)" aria-label="Search food">
          <p class="note">Struck-through foods conflict with your diet or allergies.</p>
          <div class="scroll"><table><thead><tr><th>Food</th><th>Serving</th><th>kcal</th><th>Protein</th><th>Carbs</th><th>Fat</th><th>Fiber</th><th>Allergens</th></tr></thead><tbody id="foodrows"></tbody></table></div>
        </div>
        <div class="panel" id="p-progress">
          <h2>Progress tracker</h2>
          <form id="pform" class="row" novalidate>
            <div><label for="pd">Date</label><input type="date" id="pd"></div>
            <div><label for="pw">Weight (kg)</label><input type="number" id="pw" step="0.1"></div>
            <div><label for="pwa">Water (litres)</label><input type="number" id="pwa" step="0.1"></div>
            <div><label for="pc">Calories eaten</label><input type="number" id="pc"></div>
            <div><button class="full" type="submit">Save entry</button></div>
          </form>
          <p id="perr" role="alert" style="color:#a12a1a;font-size:.9rem"></p>
          <div class="scroll"><table><thead><tr><th>Date</th><th>Weight</th><th>Water</th><th>Calories</th><th></th></tr></thead><tbody id="prows"></tbody></table></div>
        </div>
        <div class="panel" id="p-chat">
          <h2>AI nutrition assistant</h2>
          <div class="chatlog" id="log" aria-live="polite"><div class="msg">Ask about foods, protein, fibre, or what to eat for a meal.</div></div>
          <form id="cform" class="inline"><input type="text" id="cq" placeholder="What foods are high in protein?" aria-label="Your question"><button type="submit">Ask</button></form>
        </div>
        <div class="panel" id="p-report"></div>
      </div>
    </div>
  </section>
</main>
<footer>General guidance only, not medical advice. BMI is a screening number, not a diagnosis. Talk to a doctor or registered dietitian before making major diet changes. Your data stays in this browser.</footer>

<script>
const $=s=>document.querySelector(s),esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const store={get:(k,d)=>{try{const v=JSON.parse(localStorage.getItem(k));return v??d}catch{return d}},set:(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch{}}};
let ready=false,profile=store.get('dms_profile',null),photo=store.get('dms_photo',''),result=null,variation=0,progress=store.get('dms_progress',[]);
const call=o=>JSON.parse(window.pyEngine(JSON.stringify(o)));
const err=t=>$('#err').textContent=t;

addEventListener('engine-ready',()=>{ready=true;$('#status').textContent='Python engine ready';$('#status').className='ok';if(profile)run()});

function setAvatar(){[['#avatar'],['#avatar2']].forEach(([s])=>{const a=$(s);a.innerHTML=photo?`<img src="${photo}" alt="Profile photo" style="width:100%;height:100%;object-fit:cover">`:esc((profile?.name||'?')[0].toUpperCase())})}
$('#pick').onclick=()=>$('#file').click();
$('#file').onchange=e=>{const f=e.target.files[0];if(!f)return;if(!f.type.startsWith('image/')){err('Please choose an image file.');return}
  const img=new Image();img.onload=()=>{const c=document.createElement('canvas'),s=200;c.width=c.height=s;const m=Math.min(img.width,img.height);
    c.getContext('2d').drawImage(img,(img.width-m)/2,(img.height-m)/2,m,m,0,0,s,s);photo=c.toDataURL('image/jpeg',.8);store.set('dms_photo',photo);setAvatar()};img.src=URL.createObjectURL(f)};

function fillForm(){if(!profile)return;for(const k of['name','age','gender','height','weight','activity','goal','diet','other'])$('#'+k).value=profile[k]??'';
  document.querySelectorAll('[name=al]').forEach(c=>c.checked=(profile.allergies||[]).includes(c.value))}

$('#form').addEventListener('submit',e=>{e.preventDefault();const f=new FormData(e.target);
  const p={name:f.get('name').trim(),age:+f.get('age'),gender:f.get('gender'),height:+f.get('height'),weight:+f.get('weight'),activity:f.get('activity'),goal:f.get('goal'),diet:f.get('diet'),allergies:f.getAll('al'),other:f.get('other').trim()};
  if(!p.name)return err('Enter your name.');
  if(!(p.age>=12&&p.age<=90))return err('Age must be between 12 and 90.');
  if(!(p.height>=100&&p.height<=250))return err('Height must be between 100 and 250 cm.');
  if(!(p.weight>=25&&p.weight<=250))return err('Weight must be between 25 and 250 kg.');
  err('');profile=p;store.set('dms_profile',p);variation=0;run()});

function run(){if(!ready){$('#empty').hidden=false;$('#dash').hidden=true;$('#empty').innerHTML=`<h2>Profile saved for ${esc(profile.name)}</h2><p>Waiting for the Python engine to load. Your plan will appear automatically.</p>`;err('Profile saved. Waiting for the Python engine…');return}err('');
  result=call({cmd:'plan',profile,variation});$('#empty').hidden=true;$('#dash').hidden=false;render()}

function render(){const t=result.targets;setAvatar();
  $('#welcome').textContent='Welcome, '+profile.name;$('#sub').textContent=`${profile.diet} · ${profile.goal}`;
  $('#stats').innerHTML=[['BMI',t.bmi,t.bmi_category],['Calories',t.calories+' kcal','BMR '+t.bmr+' · TDEE '+t.tdee],['Protein',t.protein+' g','daily target'],['Carbs / Fat',t.carbs+' / '+t.fat+' g','daily target'],['Fiber',t.fiber+' g','daily target'],['Water',t.water+' L','daily target']]
    .map(([a,b,c],i)=>`<div class="stat${i==1?' gold':''}"><span>${a}</span><b>${esc(b)}</b><span>${esc(c)}</span></div>`).join('');
  renderPlan();renderFoods();renderProgress();renderReport()}

function planHTML(){let h=result.warning?`<p role="alert" style="color:#a12a1a">${esc(result.warning)}</p>`:'';
  for(const m of result.meals)h+=`<h3>${m.meal} <span class="note">(target ${m.target} kcal)</span></h3><div class="scroll"><table><thead><tr><th>Food</th><th>Amount</th><th>kcal</th><th>Protein</th><th>Carbs</th><th>Fat</th></tr></thead><tbody>`+
    m.items.map(i=>`<tr><td>${esc(i.name)}</td><td>${i.servings} × ${esc(i.serving)}</td><td>${i.kcal}</td><td>${i.protein} g</td><td>${i.carbs} g</td><td>${i.fat} g</td></tr>`).join('')+
    `<tr><th colspan="2">Meal total</th><th>${m.kcal}</th><th>${m.protein} g</th><th colspan="2"></th></tr></tbody></table></div>`;
  const k=result.meals.reduce((a,m)=>a+m.kcal,0),p=result.meals.reduce((a,m)=>a+m.protein,0);
  return h+`<p><b>Day total: ${k} kcal, ${p} g protein.</b></p>`}
function renderPlan(){$('#p-plan').innerHTML=`<h2>Your diet plan</h2>`+planHTML()+`<div class="inline noprint"><button id="regen">Generate another plan</button><button class="alt" id="save">Save to history</button></div><div id="hist"></div>`;
  $('#regen').onclick=()=>{variation++;run()};
  $('#save').onclick=()=>{const h=store.get('dms_history',[]);h.unshift({date:new Date().toLocaleDateString(),kcal:result.meals.reduce((a,m)=>a+m.kcal,0),meals:result.meals.map(m=>m.meal+': '+m.items.map(i=>i.name).join(', '))});store.set('dms_history',h.slice(0,20));renderHist()};renderHist()}
function renderHist(){const h=store.get('dms_history',[]);$('#hist').innerHTML=h.length?`<h3>Diet history</h3><div class="scroll"><table><thead><tr><th>Date</th><th>kcal</th><th>Breakfast</th><th>Lunch</th><th>Snack</th><th>Dinner</th></tr></thead><tbody>`+
  h.map(x=>`<tr><td>${esc(x.date)}</td><td>${x.kcal}</td>`+x.meals.map(m=>`<td>${esc(m.split(': ')[1]||'')}</td>`).join('')+'</tr>').join('')+'</tbody></table></div>':''}

function renderFoods(){if(!ready)return;const rows=call({cmd:'search',q:$('#q').value,profile});
  $('#foodrows').innerHTML=rows.map(r=>`<tr class="${r.safe?'':'unsafe'}"><td>${esc(r.name)}</td><td>${esc(r.serving)}</td><td>${r.kcal}</td><td>${r.protein}</td><td>${r.carbs}</td><td>${r.fat}</td><td>${r.fiber}</td><td>${esc(r.allergens)}</td></tr>`).join('')||'<tr><td colspan="8">No foods match your search.</td></tr>'}
$('#q').oninput=renderFoods;

$('#pd').valueAsDate=new Date();
$('#pform').addEventListener('submit',e=>{e.preventDefault();const w=+$('#pw').value,wa=+$('#pwa').value,c=+$('#pc').value,d=$('#pd').value;
  if(!d||!(w>=25&&w<=250))return $('#perr').textContent='Enter a date and a weight between 25 and 250 kg.';
  if(wa<0||c<0)return $('#perr').textContent='Water and calories cannot be negative.';
  $('#perr').textContent='';progress.push({d,w,wa,c});progress.sort((a,b)=>a.d.localeCompare(b.d));store.set('dms_progress',progress);renderProgress();renderReport()});
function renderProgress(){$('#prows').innerHTML=progress.map((r,i)=>`<tr><td>${esc(r.d)}</td><td>${r.w} kg</td><td>${r.wa||'-'} L</td><td>${r.c||'-'}</td><td><button class="alt" data-del="${i}" aria-label="Delete entry">Delete</button></td></tr>`).join('')||'<tr><td colspan="5">No entries yet. Save your first one above.</td></tr>';
  document.querySelectorAll('[data-del]').forEach(b=>b.onclick=()=>{progress.splice(+b.dataset.del,1);store.set('dms_progress',progress);renderProgress();renderReport()})}

function say(t,me){const d=document.createElement('div');d.className='msg'+(me?' me':'');d.textContent=t;$('#log').append(d);$('#log').scrollTop=1e9}
$('#cform').addEventListener('submit',e=>{e.preventDefault();const q=$('#cq').value.trim();if(!q)return;say(q,1);$('#cq').value='';say(ready?call({cmd:'chat',q,profile}):'The Python engine is still loading.')});

function renderReport(){const t=result.targets,p=profile;let ps='No progress entries yet.';
  if(progress.length){const a=progress[0],b=progress.at(-1);ps=`${progress.length} entries from ${a.d} to ${b.d}. Weight: ${a.w} kg to ${b.w} kg (${(b.w-a.w>=0?'+':'')+(b.w-a.w).toFixed(1)} kg).`}
  $('#p-report').innerHTML=`<h2>Nutrition report</h2><div class="photo"><div class="avatar">${photo?`<img src="${photo}" alt="" style="width:100%;height:100%;object-fit:cover">`:esc(p.name[0].toUpperCase())}</div><div><b>${esc(p.name)}</b><br>${p.age} years, ${esc(p.gender)}, ${p.height} cm, ${p.weight} kg</div></div>
  <h3>Profile</h3><p>Diet: ${esc(p.diet)}. Goal: ${esc(p.goal)}. Activity: ${esc(p.activity)}. Allergies: ${esc([...p.allergies,p.other].filter(Boolean).join(', ')||'None')}.</p>
  <h3>Calculations</h3><p>BMI ${t.bmi} (${esc(t.bmi_category)}). BMR ${t.bmr} kcal. Estimated daily energy ${t.tdee} kcal. Calorie target ${t.calories} kcal.</p>
  <p>Targets: protein ${t.protein} g, carbs ${t.carbs} g, fat ${t.fat} g, fiber ${t.fiber} g, water ${t.water} L.</p>
  <h3>Recommended diet</h3>`+planHTML()+`<h3>Progress summary</h3><p>${ps}</p><button class="noprint" onclick="window.print()">Print or save as PDF</button>`}

document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tabs button').forEach(x=>x.setAttribute('aria-selected',x===b));
  document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('on',p.id==='p-'+b.dataset.tab));if(b.dataset.tab==='foods')renderFoods()});

if(location.protocol==='file:'){$('#status').textContent='Not loading: serve the folder with "python -m http.server" and open http://localhost:8000'}
setTimeout(()=>{if(!ready){$('#status').textContent='Python engine did not load. Check your internet connection, and open the site via http://localhost:8000 or GitHub Pages.';$('#status').style.background='#a12a1a'}},30000);
fillForm();setAvatar();if(window.pyEngine){ready=true;$('#status').textContent='Python engine ready';$('#status').className='ok'}
</script>
<script type="py" src="./diet_engine.py"></script>
<script type="module" src="https://pyscript.net/releases/2024.11.1/core.js"></script>
</body>
</html>
