const $ = id => document.getElementById(id);
let labels = {}, catalogueData = null, historyData = null, busy = false;
const text = key => labels[key] || key;
function cell(value, className='') { const td=document.createElement('td');td.textContent=value;td.className=className;return td; }
function numberTime(value) {
  if (typeof value!=='number'||!Number.isFinite(value)||value<0)return text('Temps inconnu');
  const n=Math.floor(value);return String(Math.floor(n/3600)).padStart(2,'0')+':'+String(Math.floor(n%3600/60)).padStart(2,'0')+':'+String(n%60).padStart(2,'0');
}
function metric(target,key,value) { const box=document.createElement('div');box.className='stat';const label=document.createElement('span');label.textContent=text(key);const count=document.createElement('strong');count.textContent=String(value);box.append(label,count);target.appendChild(box); }
function render() {
  document.querySelectorAll('[data-i18n]').forEach(el=>el.textContent=text(el.dataset.i18n));
  $('search').placeholder=text('Rechercher un boss');$('search').setAttribute('aria-label',text('Rechercher un boss'));
  $('scope-note').textContent=text('Le suivi actif dépend des associations configurées.');
  if(catalogueData){
    const s=catalogueData.summary;$('coverage').replaceChildren();metric($('coverage'),'Rencontres du catalogue',s.catalogue_total);metric($('coverage'),'Rencontres actives',s.active_total);metric($('coverage'),'Suivis actifs disponibles',s.live_supported_active);
    const query=$('search').value.trim().toLocaleLowerCase();const fragment=document.createDocumentFragment();
    for(const boss of catalogueData.rows){
      if(query&&!String(boss.name+' '+boss.boss_id).toLocaleLowerCase().includes(query))continue;
      const row=document.createElement('tr');if(!boss.active)row.className='inactive';
      row.append(cell(boss.name),cell(boss.content_label),cell(boss.active_flag===null||boss.active_flag===undefined?'N/A':String(boss.active_flag),'mono'),cell(boss.validation_label,boss.validation==='user_tested'?'good':'pending'),cell(boss.support_label,boss.live_supported?'good':'pending'));fragment.appendChild(row);
    }
    $('boss-rows').replaceChildren(fragment);
  }
  if(historyData){
    $('challenge').textContent=historyData.challenge||text('Aucun challenge sélectionné');$('history-summary').replaceChildren();
    metric($('history-summary'),'Tentative observée',historyData.summary.attempts);metric($('history-summary'),'Mort',historyData.summary.deaths);metric($('history-summary'),'Victoire',historyData.summary.victories);
    const fragment=document.createDocumentFragment();for(const entry of historyData.rows){const row=document.createElement('tr');row.append(cell(entry.name),cell(String(entry.number)),cell(entry.result_label),cell(numberTime(entry.start_seconds),'mono'),cell(numberTime(entry.end_seconds),'mono'),cell(numberTime(entry.duration_seconds),'mono'));fragment.appendChild(row)}
    $('history-rows').replaceChildren(fragment);$('history-empty').textContent=historyData.rows.length?'':text('Aucune tentative enregistrée');
  }
}
async function refresh(){
  if(busy)return;busy=true;
  try{
    const responses=await Promise.all([fetch('/api/combat-catalogue',{cache:'no-store'}),fetch('/api/combat-history',{cache:'no-store'})]);
    if(responses.some(r=>!r.ok))throw Error('HTTP');
    const [catalogue,history]=await Promise.all(responses.map(r=>r.json()));
    if(!Array.isArray(catalogue.rows)||!Array.isArray(history.rows))throw Error('Invalid response');
    catalogueData=catalogue;historyData=history;labels=catalogue.ui||{};document.documentElement.lang=catalogue.language==='en'?'en':'fr';
    $('message').textContent=catalogue.configuration_error||'';render();
  }catch(error){$('message').textContent=text('Connexion au tracker interrompue')}finally{busy=false}
}
$('search').addEventListener('input',render);$('refresh').addEventListener('click',refresh);
for(const target of ['catalogue','history'])$('tab-'+target).addEventListener('click',()=>{$('catalogue').hidden=target!=='catalogue';$('history').hidden=target!=='history';$('tab-catalogue').classList.toggle('selected',target==='catalogue');$('tab-history').classList.toggle('selected',target==='history')});
refresh();setInterval(refresh,2000);
