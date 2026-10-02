/* CINEMATIC_CANVAS_V1 — CONSOLIDATED_OVERLAY_V1 */
const $ = id => document.getElementById(id);
const ANIMATION_WIDTH = 860;
const ANIMATION_HEIGHT = 250;
const POLL_MS = 250;
const MAX_QUEUE = 5;
let busy = false;
let profileId = null;
let known = new Set();
let queue = [];
let playing = false;
let epoch = 0;


/* OVERLAY_I18N_V1 */
let interfaceLanguage = 'fr';
let interfaceLabels = {};
function uiText(key) {
  const value = interfaceLabels[key];
  return typeof value === 'string' && value ? value : key;
}
function applyInterface(state) {
  interfaceLanguage = state.language === 'en' ? 'en' : 'fr';
  interfaceLabels = state.ui && typeof state.ui === 'object' && !Array.isArray(state.ui) ? state.ui : {};
  document.documentElement.lang = interfaceLanguage;
  const keys = ['CHALLENGE', 'TEMPS DE JEU', 'MORTS', 'BOSS VAINCUS'];
  const elements = document.querySelectorAll('.challenge-panel .eyebrow');
  if (elements.length === keys.length) {
    elements.forEach((element, index) => {
      element.dataset.i18n = keys[index];
      element.textContent = uiText(keys[index]);
    });
  }
  const localized = new Map((Array.isArray(state.boss_history) ? state.boss_history : []).filter(event => event && typeof event.id === 'string').map(event => [event.id, event]));
  queue = queue.map(event => event.preview ? event : (localized.get(event.id) || event));
}

function put(id, value) {
  $(id).textContent = value === null || value === undefined || value === '' ? 'N/A' : String(value);
}
function validEvents(history) {
  if (!Array.isArray(history)) return [];
  const identifiers = new Set();
  return history.filter(event => {
    if (!event || event.type !== 'boss_victory' ||
        event.timing_mode !== 'confirmed_flag_observation' ||
        typeof event.id !== 'string' || !event.id ||
        typeof event.observed_at !== 'string' || !Number.isFinite(Date.parse(event.observed_at)) ||
        typeof event.run_seconds !== 'number' || !Number.isFinite(event.run_seconds) ||
        event.run_seconds < 0 || identifiers.has(event.id)) return false;
    identifiers.add(event.id);
    return true;
  }).sort((a, b) => Date.parse(a.observed_at) - Date.parse(b.observed_at));
}
function format(seconds) {
  seconds = Math.floor(seconds);
  return String(Math.floor(seconds / 3600)).padStart(2, '0') + ':' +
    String(Math.floor(seconds % 3600 / 60)).padStart(2, '0') + ':' +
    String(seconds % 60).padStart(2, '0');
}
function bossName(event) {
  return typeof event.name === 'string' && event.name.trim() ? event.name.trim() :
    (typeof event.boss_id === 'string' ? event.boss_id : uiText('Boss vaincu'));
}
function prepareInscription(event, w, h, dpr) {
  const layer = document.createElement('canvas');
  layer.width = Math.round(w * dpr);
  layer.height = Math.round(h * dpr);
  const c = layer.getContext('2d');
  c.setTransform(dpr, 0, 0, dpr, 0, 0);
  c.textBaseline = 'middle';
  function inscription(text, y, size, spacing, color) {
    c.font = size + 'px Georgia, "Times New Roman", serif';
    const chars = Array.from(text);
    const widths = chars.map(ch => c.measureText(ch).width);
    const total = widths.reduce((a, b) => a + b, 0) + Math.max(0, chars.length - 1) * spacing;
    let x = (w - total) / 2;
    c.fillStyle = color;
    for (let i = 0; i < chars.length; i++) {
      c.fillText(chars[i], x, y);
      x += widths[i] + spacing;
    }
  }
  const name = event.preview ? uiText('Aperçu de la victoire') : bossName(event);
  const time = event.preview ? uiText('PRÉVISUALISATION — AUCUNE VICTOIRE ENREGISTRÉE') : format(event.run_seconds);
  let size = 42;
  c.font = size + 'px Georgia, "Times New Roman", serif';
  while (size > 18 && c.measureText(name).width + (Array.from(name).length - 1) * .7 > w - 100) {
    size--;
    c.font = size + 'px Georgia, "Times New Roman", serif';
  }
  inscription(event.preview ? uiText('APERÇU') : uiText('VICTOIRE'), 71, 12, 5, '#b6a173');
  inscription(name, 120, size, .7, '#e1d2ac');
  inscription(time, 166, event.preview ? 11 : 17, event.preview ? 1 : 2, '#b4a17b');
  for (const y of [43, 195]) {
    const g = c.createLinearGradient(110, y, w - 110, y);
    g.addColorStop(0, 'rgba(163,141,89,0)');
    g.addColorStop(.3, 'rgba(163,141,89,.6)');
    g.addColorStop(.7, 'rgba(163,141,89,.6)');
    g.addColorStop(1, 'rgba(163,141,89,0)');
    c.fillStyle = g;
    c.fillRect(110, y, w - 220, 1);
  }
  return layer;
}
async function show(event) {
  playing = true;
  const token = epoch;
  const v = $('victory');
  const canvas = $('ash');
  const w = ANIMATION_WIDTH, h = ANIMATION_HEIGHT;
  const dpr = Math.min(devicePixelRatio || 1, 2);
  try {
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    const c = canvas.getContext('2d');
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    const layer = prepareInscription(event, w, h, dpr);
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    $('victory-label').textContent = event.preview ? uiText('APERÇU') : uiText('VICTOIRE');
    $('victory-name').textContent = event.preview ? uiText('Aperçu de la victoire') : bossName(event);
    $('victory-time').textContent = event.preview ? uiText('Prévisualisation') : format(event.run_seconds);
    v.className = 'victory active';
    const start = performance.now();
    const ease = value => {
      value = Math.max(0, Math.min(1, value));
      return value * value * (3 - 2 * value);
    };
    await new Promise((resolve, reject) => {
      function frame(now) {
        try {
          if (token !== epoch) { resolve(); return; }
          const t = (now - start) / 1000;
          if (t >= 8.5) { c.clearRect(0, 0, w, h); resolve(); return; }
          c.clearRect(0, 0, w, h);
          const exit = 1 - ease((t - 6.7) / 1.8);
          const backgroundAlpha = ease(t / .8) * exit * .48;
          const bandWidth = reduced ? w : w * (.45 + .55 * ease(t / 1.15));
          const x = (w - bandWidth) / 2;
          const horizontal = c.createLinearGradient(x, 0, x + bandWidth, 0);
          horizontal.addColorStop(0, 'rgba(5,7,6,0)');
          horizontal.addColorStop(.18, 'rgba(5,7,6,' + backgroundAlpha + ')');
          horizontal.addColorStop(.82, 'rgba(5,7,6,' + backgroundAlpha + ')');
          horizontal.addColorStop(1, 'rgba(5,7,6,0)');
          c.fillStyle = horizontal;
          c.fillRect(x, 24, bandWidth, 192);
          c.globalAlpha = ease((t - (reduced ? .15 : .55)) / (reduced ? .6 : 1.25)) * exit;
          c.drawImage(layer, 0, 0, w, h);
          c.globalAlpha = 1;
          requestAnimationFrame(frame);
        } catch (error) { reject(error); }
      }
      requestAnimationFrame(frame);
    });
    if (token !== epoch) return;
    v.className = 'victory';
    playing = false;
    next();
  } catch (error) {
    if (token === epoch) {
      v.className = 'victory';
      playing = false;
      console.error('Victory animation:', error);
      next();
    }
  }
}
function next() {
  if (!playing && queue.length) show(queue.shift());
}
function resetProfile(id, events) {
  profileId = id;
  known = new Set(events.map(event => event.id));
  queue = [];
  epoch++;
  playing = false;
  $('victory').className = 'victory';
  const canvas = $('ash');
  canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
}
function eventsChanged(state) {
  const events = validEvents(state.boss_history);
  const id = typeof state.profile_id === 'string' && state.profile_id ? state.profile_id : null;
  if (id !== profileId) { resetProfile(id, events); return; }
  if (!id || state.stale) return;
  for (const event of events) {
    if (known.has(event.id)) continue;
    known.add(event.id);
    const age = Date.now() - Date.parse(event.observed_at);
    if (age >= -5000 && age < 30000 && queue.length < MAX_QUEUE) queue.push(event);
  }
  next();
}
async function refresh() {
  if (busy) return;
  busy = true;
  try {
    const response = await fetch('/api/state', { cache: 'no-store' });
    if (!response.ok) throw Error('HTTP ' + response.status);
    const state = await response.json();
    if (!state || typeof state !== 'object' || Array.isArray(state)) throw Error('Invalid state');
    applyInterface(state);
    applyCombat(state);
    for (const id of ['challenge', 'character', 'timer', 'deaths', 'defeated']) put(id, state[id]);
    put('status', state.status);
    document.body.classList.toggle('stale', !!state.stale);
    eventsChanged(state);
  } catch (error) {
    put('status', uiText('Connexion au tracker interrompue'));
    document.body.classList.add('stale');
  } finally { busy = false; }
}
refresh();
setInterval(refresh, POLL_MS);
if (new URLSearchParams(location.search).get('preview') === '1') {
  setTimeout(() => { queue.push({ preview: true }); next(); }, 800);
}

/* GODEFROY_COMBAT_PROTOTYPE_V1 */
/* COMBAT_CONTEXTUAL_UI_V1 */
const combatPreviewRequested = new URLSearchParams(location.search).get('preview_combat') === '1';
const combatPreviewStart = performance.now();
const combatDrawer = { visible: false, key: null, animation: null, serial: 0 };

function combatVisible(combat, state) {
  return !!combat && combat.mode === 'confirmed_active_flag_v1' && combat.active === true &&
    ['active', 'active_untracked'].includes(combat.phase) && (combat.preview === true || state.stale !== true);
}

function animateCombatDrawer(block, show) {
  const wasHidden = block.hidden;
  const height = wasHidden ? 0 : block.getBoundingClientRect().height;
  const opacity = wasHidden ? 0 : Number(getComputedStyle(block).opacity);
  const serial = ++combatDrawer.serial;
  if (combatDrawer.animation) {
    combatDrawer.animation.cancel();
    combatDrawer.animation = null;
  }
  block.hidden = false;
  block.style.height = '';
  block.style.opacity = '';
  const fullHeight = block.scrollHeight;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (typeof block.animate !== 'function' || reduced) {
    block.hidden = !show;
    return;
  }
  const animation = block.animate([
    { height: height + 'px', opacity: Number.isFinite(opacity) ? opacity : 0 },
    { height: (show ? fullHeight : 0) + 'px', opacity: show ? 1 : 0 }
  ], { duration: show ? 380 : 250, easing: 'cubic-bezier(.25,.1,.25,1)', fill: 'both' });
  combatDrawer.animation = animation;
  animation.finished.then(() => {
    if (serial !== combatDrawer.serial) return;
    block.hidden = !show;
    animation.cancel();
    combatDrawer.animation = null;
    block.style.height = '';
    block.style.opacity = '';
  }, () => {});
}

function applyCombat(state) {
  let combat = state.combat;
  if (combatPreviewRequested) {
    const t = (performance.now() - combatPreviewStart) / 1000;
    combat = t >= 1 && t < 8 ? {
      mode: 'confirmed_active_flag_v1', boss_id: '__preview__', preview: true,
      phase: 'active', active: true, boss_name: uiText('Aperçu de combat'),
      observed_attempts: 3, observed_boss_deaths: 2, status: uiText('Données fictives - aperçu')
    } : null;
  }
  let block = document.getElementById('experimental-combat');
  const show = combatVisible(combat, state);
  if (!show) {
    if (block && combatDrawer.visible) {
      combatDrawer.visible = false;
      combatDrawer.key = null;
      animateCombatDrawer(block, false);
    }
    return;
  }
  if (!block) {
    const panel = document.querySelector('.challenge-panel');
    if (!panel) return;
    block = document.createElement('section');
    block.id = 'experimental-combat';
    block.hidden = true;
    block.style.overflow = 'hidden';
    const rule = document.createElement('div'); rule.className = 'rule'; block.appendChild(rule);
    function caption(id) {
      const element = document.createElement('span'); element.id = id;
      element.className = 'combat-caption';
      element.style.cssText = 'display:block;color:#aea07c;font-size:10px;letter-spacing:2px;margin-top:8px';
      return element;
    }
    block.appendChild(caption('combat-title'));
    const name = document.createElement('strong'); name.id = 'combat-name';
    name.style.cssText = 'display:block;font-weight:normal;color:#e8d9af;font-size:19px;margin-top:8px';
    block.appendChild(name);
    const metrics = document.createElement('div'); metrics.className = 'metrics'; metrics.style.marginTop = '10px';
    for (const [labelId, valueId] of [['combat-attempt-label','combat-attempts'],['combat-death-label','combat-deaths']]) {
      const cell = document.createElement('div'); cell.appendChild(caption(labelId));
      const value = document.createElement('strong'); value.id = valueId; cell.appendChild(value);
      metrics.appendChild(cell);
    }
    block.appendChild(metrics);
    const status = document.createElement('div'); status.id = 'combat-status';
    status.style.cssText = 'color:#aaa18a;font-size:10px;line-height:1.4;margin-top:9px';
    block.appendChild(status);
    const scope = document.createElement('div'); scope.id = 'combat-scope';
    scope.style.cssText = 'color:#9e967e;font-size:9px;line-height:1.4;margin-top:5px';
    block.appendChild(scope);
    panel.insertBefore(block, panel.querySelector('footer'));
  }
  document.getElementById('combat-title').textContent = uiText(combat.preview ? 'APERÇU' : 'COMBAT EN COURS');
  document.getElementById('combat-name').textContent = combat.boss_name;
  document.getElementById('combat-attempt-label').textContent = uiText('TENTATIVES OBSERVÉES');
  document.getElementById('combat-death-label').textContent = uiText('MORTS OBSERVÉES');
  document.getElementById('combat-attempts').textContent = Number.isInteger(combat.observed_attempts) && combat.observed_attempts >= 0 ? String(combat.observed_attempts) : 'N/A';
  document.getElementById('combat-deaths').textContent = Number.isInteger(combat.observed_boss_deaths) && combat.observed_boss_deaths >= 0 ? String(combat.observed_boss_deaths) : 'N/A';
  document.getElementById('combat-status').textContent = combat.status || '';
  document.getElementById('combat-scope').textContent = combat.preview ? uiText('Données fictives - aperçu') : (combat.validation_label || uiText('Suivi expérimental'));
  const newEntry = !combatDrawer.visible || combatDrawer.key !== combat.boss_id;
  combatDrawer.visible = true;
  combatDrawer.key = combat.boss_id;
  if (newEntry) animateCombatDrawer(block, true);
}


// GENERIC_COMBAT_ENGINE_V1
