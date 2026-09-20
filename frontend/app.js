// ============================================================
// Utilidades generales
// ============================================================
const RANKS = ['2','3','4','5','6','7','8','9','T','J','Q','K','A'];
const SUITS = [['s','♠'],['h','♥'],['d','♦'],['c','♣']];

async function api(method, path, body) {
  const res = await fetch(path, {
    method,
    headers: body ? {'Content-Type': 'application/json'} : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.detail || res.statusText;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data;
}

function suitLetterOf(card) { return card[1]; }
function isRed(card) { return suitLetterOf(card) === 'h' || suitLetterOf(card) === 'd'; }

// ============================================================
// Selector de cartas — grilla de las 52, UN toque por carta
// ============================================================
function makeCardPicker(containerId, initialMax) {
  const container = document.getElementById(containerId);
  let max = initialMax;
  let cards = [];
  let openSlot = null;

  function render() {
    container.innerHTML = '';
    const slotsRow = document.createElement('div');
    slotsRow.className = 'card-slots';
    for (let i = 0; i < max; i++) {
      const slot = document.createElement('div');
      const c = cards[i];
      if (c) {
        slot.className = 'card-slot filled ' + (isRed(c) ? 'red' : 'black');
        slot.textContent = c[0] + SUITS.find(s => s[0] === c[1])[1];
      } else {
        slot.className = 'card-slot empty';
        slot.textContent = '+';
      }
      slot.onclick = () => { openSlot = (openSlot === i) ? null : i; render(); };
      slotsRow.appendChild(slot);
    }
    container.appendChild(slotsRow);

    if (openSlot !== null) {
      const grid = document.createElement('div');
      grid.className = 'card-grid-picker';
      RANKS.slice().reverse().forEach(r => {
        const row = document.createElement('div');
        row.className = 'card-grid-row';
        SUITS.forEach(([letter, symbol]) => {
          const code = r + letter;
          const usedElsewhere = cards.includes(code) && cards[openSlot] !== code;
          const cell = document.createElement('div');
          cell.className = 'card-grid-cell' + ((letter === 'h' || letter === 'd') ? ' red' : '') + (usedElsewhere ? ' used' : '');
          cell.textContent = r + symbol;
          if (!usedElsewhere) {
            cell.onclick = () => {
              cards[openSlot] = code;
              openSlot = null;
              render();
              if (containerId === 'board-slots') onBoardChanged();
            };
          }
          row.appendChild(cell);
        });
        grid.appendChild(row);
      });
      container.appendChild(grid);
    }
  }

  render();
  return {
    getCards: () => cards.filter(Boolean),
    setMax: (n) => { max = n; cards = cards.slice(0, n); openSlot = null; render(); },
    clear: () => { cards = []; openSlot = null; render(); },
  };
}

// ============================================================
// Grupos de selección única (chips)
// ============================================================
function makeToggleGroup(containerId, defaultValue, onChange) {
  const container = document.getElementById(containerId);
  let value = defaultValue;
  function apply() {
    [...container.children].forEach(chip => {
      chip.classList.toggle('selected', chip.dataset.v === value);
    });
  }
  container.querySelectorAll('.toggle-chip').forEach(chip => {
    chip.onclick = () => { value = chip.dataset.v; apply(); if (onChange) onChange(value); };
  });
  apply();
  return { get: () => value, set: (v) => { value = v; apply(); } };
}

// ============================================================
// Navegación por pestañas
// ============================================================
document.querySelectorAll('nav.tabs button').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('nav.tabs button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('view-' + btn.dataset.view).classList.add('active');
    if (btn.dataset.view === 'players') loadPlayers();
    if (btn.dataset.view === 'session') loadSession();
  };
});

// ============================================================
// VISTA: DECISIÓN — "mano en curso"
// ============================================================
const heroPicker = makeCardPicker('hero-slots', 2);
const boardPicker = makeCardPicker('board-slots', 0);
const deadPicker = makeCardPicker('dead-slots', 4);

const STREET_BOARD_SIZE = {preflop: 0, flop: 3, turn: 4, river: 5};
const STREET_ORDER = ['preflop', 'flop', 'turn', 'river'];
const POSITION_OPTIONS = [
  ['', '— sin especificar —'], ['early', 'Temprana'], ['middle', 'Media'], ['late', 'Tardía'],
  ['button', 'Botón'], ['sb', 'Ciega chica'], ['bb', 'Ciega grande'],
];

function onBoardChanged() { /* enganche disponible si hace falta reaccionar al completar el board */ }

// ---------- configuración de mesa (se recuerda entre manos de la misma sesión) ----------
// tableSeatActive NO se resetea en "Nueva mano" a propósito — así, si jugás
// varias manos seguidas con la misma gente, no hay que volver a tocar nada.
let tableSeatActive = {};

function renderSeatConfig() {
  const size = parseInt(document.getElementById('table-size-input').value) || 6;
  const row = document.getElementById('seat-config-row');
  row.innerHTML = '';
  for (let i = 1; i <= size; i++) {
    const name = `Asiento ${i}`;
    if (!(name in tableSeatActive)) tableSeatActive[name] = true;
    const btn = document.createElement('div');
    btn.className = 'seat-btn' + (tableSeatActive[name] ? '' : ' off');
    btn.textContent = name;
    btn.onclick = () => { tableSeatActive[name] = !tableSeatActive[name]; renderSeatConfig(); };
    row.appendChild(btn);
  }
  Object.keys(tableSeatActive).forEach(k => {
    const num = parseInt(k.replace('Asiento ', ''));
    if (num > size) delete tableSeatActive[k];
  });
}
document.getElementById('table-size-input').addEventListener('input', renderSeatConfig);

document.getElementById('btn-apply-table-size').onclick = () => {
  if (!hand) { alert('Primero tocá "Nueva mano"'); return; }
  localStorage.setItem('pokerapp_table_size', document.getElementById('table-size-input').value);
  Object.keys(tableSeatActive).forEach(name => {
    if (tableSeatActive[name]) {
      if (!hand.players[name]) hand.players[name] = { position: '', active: true, rangeNotation: '', suggestedWeights: null };
    } else if (hand.players[name]) {
      delete hand.players[name];
    }
  });
  refreshHandUI();
};

// ---------- estado de la mano en curso ----------
// actionHistory guarda TODA la mano (todas las calles) — así los
// jugadores y sus rangos quedan disponibles aunque cambiés de calle,
// y "Sugerir rango" puede mirar la última acción real de cada uno.
function newHandState() {
  return {
    handId: 'mano-' + Date.now(),
    street: 'preflop',
    potBeforeStreet: 0,
    actionHistory: [], // {street, player, type, amount}
    players: {},         // {nombre: {position, active, rangeNotation, suggestedWeights}}
    pendingDecisionId: null,
  };
}
let hand = null;
let openActionSeat = null; // nombre del asiento (o 'hero') con el selector de acción abierto

function currentStreetActions() {
  if (!hand) return [];
  return hand.actionHistory.filter(a => a.street === hand.street);
}
function potNow() {
  if (!hand) return 0;
  return hand.potBeforeStreet + currentStreetActions()
    .filter(a => a.type !== 'fold' && a.type !== 'check')
    .reduce((s, a) => s + (a.amount || 0), 0);
}
// La apuesta "vigente" de la calle es la ÚLTIMA acción de apostar/subir,
// salteando los retiros y chequeos que hayan pasado después (esos no
// cambian cuánto hay que pagar). Antes esto miraba solo la ÚLTIMA fila
// de la lista, así que un retiro después de una apuesta hacía que
// pareciera que ya no había nada que pagar — bug real, encontrado
// probando con 3 rivales.
function currentBetLevelAction() {
  const acts = currentStreetActions();
  for (let i = acts.length - 1; i >= 0; i--) {
    if (acts[i].type === 'bet' || acts[i].type === 'raise') return acts[i];
  }
  return null;
}
function potBeforeAction(action) {
  if (!hand) return 0;
  if (!action) return hand.potBeforeStreet;
  const acts = currentStreetActions();
  const idx = acts.indexOf(action);
  return hand.potBeforeStreet + acts.slice(0, idx)
    .filter(a => a.type !== 'fold' && a.type !== 'check')
    .reduce((s, a) => s + (a.amount || 0), 0);
}
function facingBetFor(playerName) {
  const a = currentBetLevelAction();
  return !!a && a.player !== playerName; // nadie "enfrenta" su propia apuesta
}
function betAmountFor(playerName) {
  return facingBetFor(playerName) ? currentBetLevelAction().amount : null;
}
function facingBetNow() { return facingBetFor('hero'); }
function betAmountFacing() { return betAmountFor('hero'); }
function potBeforeLastAction() { return potBeforeAction(currentBetLevelAction()); }
function activeNonHeroPlayers() {
  if (!hand) return [];
  return Object.keys(hand.players).filter(p => hand.players[p].active);
}
function primaryVillainName() {
  if (facingBetNow()) return currentBetLevelAction().player;
  const active = activeNonHeroPlayers();
  return active.length ? active[0] : null; // simplificación: si nadie te está apostando, se enfoca el primer rival activo
}

document.getElementById('btn-new-hand').onclick = () => {
  hand = newHandState();
  openActionSeat = null;
  heroPicker.clear();
  boardPicker.setMax(0);
  boardPicker.clear();
  deadPicker.clear();
  document.getElementById('initial-pot').value = localStorage.getItem('pokerapp_default_blinds') || '';
  document.getElementById('contemplated-bet').value = '';
  document.getElementById('table-size-input').value = localStorage.getItem('pokerapp_table_size') || '6';
  document.getElementById('initial-pot-field').style.display = 'block';
  document.getElementById('hand-active-ui').style.display = 'block';
  document.getElementById('hand-status-text').textContent = `Mano en curso (${hand.handId}) — calle: preflop.`;
  document.getElementById('decision-results').innerHTML = '';
  renderSeatConfig();
  hand.potBeforeStreet = parseFloat(document.getElementById('initial-pot').value) || 0;
  // los asientos que ya estaban marcados activos de una mano anterior arrancan cargados solos
  Object.keys(tableSeatActive).forEach(name => {
    if (tableSeatActive[name]) hand.players[name] = { position: '', active: true, rangeNotation: '', suggestedWeights: null };
  });
  refreshHandUI();
};

document.getElementById('initial-pot').addEventListener('input', () => {
  if (!hand) return;
  hand.potBeforeStreet = parseFloat(document.getElementById('initial-pot').value) || 0;
  localStorage.setItem('pokerapp_default_blinds', document.getElementById('initial-pot').value);
  refreshHandUI();
});

function logAction(player, type, amount) {
  hand.actionHistory.push({ street: hand.street, player, type, amount });

  if (player !== 'hero') {
    if (type === 'fold') hand.players[player].active = false;
  } else if (hand.pendingDecisionId) {
    // auto-registrar la acción real de hero contra la última decisión calculada
    const actionMap = { fold: 'fold', check: 'check', call: 'call', bet: 'bet_value', raise: 'bet_value' };
    api('POST', '/api/session/record-action', {
      decision_id: hand.pendingDecisionId, hand_id: hand.handId, actual_action: actionMap[type] || type,
    }).then(res => {
      const note = document.createElement('div');
      note.className = 'notice';
      note.textContent = res.matched_recommendation
        ? 'Registrado para la sesión — coincidió con la mejor recomendación.'
        : `Registrado para la sesión — diferencia de valor: ${res.value_gap} (mejor recomendación: ${res.best_recommendation}).`;
      document.getElementById('decision-results').prepend(note);
    }).catch(() => { /* si falla el registro de sesión, no interrumpe el resto del flujo */ });
    hand.pendingDecisionId = null;
  }

  openActionSeat = null;
  refreshHandUI();
}

document.getElementById('btn-next-street').onclick = () => {
  if (!hand) return;
  const idx = STREET_ORDER.indexOf(hand.street);
  if (idx === STREET_ORDER.length - 1) { alert('Ya estás en el río, no hay más calles.'); return; }
  hand.potBeforeStreet = potNow();
  hand.street = STREET_ORDER[idx + 1];
  openActionSeat = null;
  boardPicker.setMax(STREET_BOARD_SIZE[hand.street]);
  document.getElementById('contemplated-bet').value = '';
  document.getElementById('initial-pot-field').style.display = 'none'; // ya cumplió su única función
  document.getElementById('hand-status-text').textContent = `Mano en curso (${hand.handId}) — calle: ${hand.street}.`;
  document.getElementById('decision-results').innerHTML = '';
  refreshHandUI();
};

function refreshHandUI() {
  if (!hand) return;
  document.getElementById('pot-display').textContent = potNow();
  document.getElementById('current-street-label').textContent = hand.street;

  const listEl = document.getElementById('action-log-list');
  const acts = currentStreetActions();
  listEl.innerHTML = acts.length
    ? acts.map((a) => `<div class="action-item"><span>${a.player} — ${a.type}${a.amount ? ' (+' + a.amount + ')' : ''}</span></div>`).join('')
    : '<p class="hint">Sin acciones todavía en esta calle.</p>';

  const hintEl = document.getElementById('facing-bet-hint');
  const contemplatedField = document.getElementById('contemplated-bet-field');
  if (facingBetNow()) {
    hintEl.textContent = `Enfrentás una apuesta de ${betAmountFacing()} de ${currentBetLevelAction().player}.`;
    contemplatedField.style.display = 'none';
  } else {
    hintEl.textContent = `Nadie te está apostando ahora mismo — bote ${potNow()}.`;
    contemplatedField.style.display = 'block';
  }

  refreshSeatActionRow();
  refreshHeroActionTrigger();
  renderActionChooser();
  refreshPlayersPanel();
}

function refreshSeatActionRow() {
  const row = document.getElementById('seat-action-row');
  row.innerHTML = '';

  activeNonHeroPlayers().forEach(name => {
    const btn = document.createElement('div');
    btn.className = 'seat-btn' + (openActionSeat === name ? ' open' : '');
    btn.textContent = name;
    btn.onclick = () => { openActionSeat = (openActionSeat === name) ? null : name; refreshSeatActionRow(); refreshHeroActionTrigger(); renderActionChooser(); };
    row.appendChild(btn);
  });

  Object.keys(hand.players).filter(n => !hand.players[n].active).forEach(name => {
    const btn = document.createElement('div');
    btn.className = 'seat-btn folded';
    btn.textContent = name;
    row.appendChild(btn);
  });
}

function refreshHeroActionTrigger() {
  const row = document.getElementById('hero-action-trigger-row');
  row.innerHTML = '';
  const heroBtn = document.createElement('div');
  heroBtn.className = 'seat-btn hero-seat' + (openActionSeat === 'hero' ? ' open' : '');
  heroBtn.textContent = 'MI JUGADA';
  heroBtn.onclick = () => { openActionSeat = (openActionSeat === 'hero') ? null : 'hero'; refreshSeatActionRow(); refreshHeroActionTrigger(); renderActionChooser(); };
  row.appendChild(heroBtn);
}

function renderActionChooser() {
  // el selector se dibuja en un contenedor distinto según si es la
  // acción de un rival (arriba, junto al bote) o la tuya propia (abajo,
  // después de "Calcular") — Punto 1: tu jugada va DESPUÉS del cálculo
  const rivalContainer = document.getElementById('action-chooser-container');
  const heroContainer = document.getElementById('hero-action-chooser-container');
  const container = openActionSeat === 'hero' ? heroContainer : rivalContainer;
  (openActionSeat === 'hero' ? rivalContainer : heroContainer).innerHTML = '';
  if (!openActionSeat) { container.innerHTML = ''; return; }

  // ojo: esto usa la perspectiva del ASIENTO seleccionado (no la de hero) —
  // cada jugador enfrenta la misma apuesta vigente salvo que sea quien la hizo
  const facingForThisSeat = facingBetFor(openActionSeat);
  const callAmountForThisSeat = betAmountFor(openActionSeat);
  const callLabel = facingForThisSeat ? `Call (${callAmountForThisSeat})` : 'Call';
  container.innerHTML = `
    <div class="action-chooser">
      <div class="action-chooser-grid">
        <div class="action-chooser-btn fold" data-act="fold">Fold</div>
        <div class="action-chooser-btn" data-act="check">Check</div>
        <div class="action-chooser-btn" data-act="call">${callLabel}</div>
        <div class="action-chooser-btn bet" data-act="betraise">Bet / Raise</div>
      </div>
      <div class="field" id="bet-amount-field" style="display:none; margin-top:10px">
        <label>Monto que agrega con esta apuesta/subida</label>
        <input type="number" id="bet-amount-input" placeholder="ej. 70">
        <button class="secondary" id="btn-confirm-bet" style="margin-top:8px">Confirmar</button>
      </div>
    </div>`;

  container.querySelectorAll('.action-chooser-btn').forEach(btn => {
    btn.onclick = () => {
      const act = btn.dataset.act;
      if (act === 'betraise') {
        document.getElementById('bet-amount-field').style.display = 'block';
        document.getElementById('bet-amount-input').focus();
        return;
      }
      const amount = act === 'call' ? (facingForThisSeat ? callAmountForThisSeat : 0) : 0;
      logAction(openActionSeat, act, amount);
    };
  });
  const confirmBtn = container.querySelector('#btn-confirm-bet');
  if (confirmBtn) {
    confirmBtn.onclick = () => {
      const amt = parseFloat(document.getElementById('bet-amount-input').value) || 0;
      if (amt <= 0) { alert('Poné un monto mayor a 0'); return; }
      const alreadyBetThisStreet = currentStreetActions().some(a => a.type === 'bet' || a.type === 'raise');
      logAction(openActionSeat, alreadyBetThisStreet ? 'raise' : 'bet', amt);
    };
  }
}

function refreshPlayersPanel() {
  const panel = document.getElementById('players-panel');
  const names = Object.keys(hand.players);
  if (!names.length) {
    panel.innerHTML = '<p class="hint">Todavía no hay jugadores — configurá la mesa arriba.</p>';
    return;
  }
  names.forEach(name => {
    const p = hand.players[name];
    let card = panel.querySelector(`[data-player="${CSS.escape(name)}"]`);
    if (!card) {
      card = document.createElement('div');
      card.className = 'candidate';
      card.dataset.player = name;
      card.innerHTML = `
        <div class="candidate-head">
          <span class="candidate-action">${name}</span>
          <span class="badge player-status-badge"></span>
        </div>
        <div class="row" style="margin-top:8px">
          <select class="player-position" style="flex:1">
            ${POSITION_OPTIONS.map(([v, l]) => `<option value="${v}">${l}</option>`).join('')}
          </select>
        </div>
        <div class="field">
          <label>Su rango (notación — vacío = cualquier mano al azar)</label>
          <input type="text" class="player-range" placeholder="22+, A9s+, KJo+">
        </div>
        <button class="secondary btn-suggest-for-player">Sugerir rango según su última acción</button>
        <div class="suggest-inline-result" style="margin-top:8px"></div>
      `;
      panel.appendChild(card);

      card.querySelector('.player-position').value = p.position || '';
      card.querySelector('.player-range').value = p.rangeNotation || '';

      card.querySelector('.player-position').addEventListener('change', (e) => {
        hand.players[name].position = e.target.value;
      });
      card.querySelector('.player-range').addEventListener('input', (e) => {
        hand.players[name].rangeNotation = e.target.value;
        hand.players[name].suggestedWeights = null; // escribir a mano cancela la sugerencia
      });
      card.querySelector('.btn-suggest-for-player').onclick = () => suggestRangeFor(name, card);
    }
    // esto SÍ se actualiza en cada refresco, sin recrear el input (no se pierde lo que el usuario tipeó)
    const badge = card.querySelector('.player-status-badge');
    badge.textContent = p.active ? 'activo' : 'retirado';
    card.style.opacity = p.active ? '1' : '0.5';
  });
}

async function suggestRangeFor(name, cardEl) {
  const resultEl = cardEl.querySelector('.suggest-inline-result');
  // busca la ÚLTIMA acción de ESTE jugador en la calle actual (simplificación:
  // no mira calles anteriores — si todavía no actuó en esta calle, pide que actúe primero)
  const acts = currentStreetActions().filter(a => a.player === name);
  if (!acts.length) {
    resultEl.innerHTML = '<div class="notice error">Este jugador todavía no actuó en esta calle.</div>';
    return;
  }
  const action = acts[acts.length - 1];
  if (!['call', 'bet', 'raise'].includes(action.type)) {
    resultEl.innerHTML = '<div class="notice error">Hace falta una acción de pagar, apostar o subir.</div>';
    return;
  }
  const idxInStreet = currentStreetActions().indexOf(action);
  const potBefore = hand.potBeforeStreet + currentStreetActions().slice(0, idxInStreet)
    .filter(a => a.type !== 'fold' && a.type !== 'check')
    .reduce((s, a) => s + (a.amount || 0), 0);
  if (potBefore <= 0 || !action.amount) {
    resultEl.innerHTML = '<div class="notice error">Hace falta un bote de referencia y un monto en la acción.</div>';
    return;
  }
  const potFraction = action.amount / potBefore;
  const numPlayersRaw = document.getElementById('num-players').value;
  const numPlayers = numPlayersRaw ? parseInt(numPlayersRaw) : null;

  resultEl.innerHTML = '<div class="notice">Calculando…</div>';
  try {
    const r = await api('POST', '/api/ranges/suggest', {
      villain_label: name, street: hand.street, pot_fraction: potFraction,
      action_type: action.type, villain_position: hand.players[name].position || null, num_players: numPlayers,
    });
    const sourceLabel = r.source === 'real_sizing_tell_ewma'
      ? `datos reales de este jugador (${r.n_observations} observaciones)`
      : 'una heurística genérica (todavía no hay datos suficientes de este jugador en esta calle/tamaño)';
    resultEl.innerHTML = `<div class="notice">~${r.combo_count} combos, basada en ${sourceLabel}${r.position_informed ? ' + su posición' : ' (sin posición cargada)'}.</div>
      <button class="secondary btn-use-suggestion" style="margin-top:8px">Usar esta sugerencia</button>`;
    resultEl.querySelector('.btn-use-suggestion').onclick = () => {
      hand.players[name].suggestedWeights = r.weights;
      hand.players[name].rangeNotation = '';
      cardEl.querySelector('.player-range').value = '';
      resultEl.innerHTML = `<div class="notice">Sugerencia aplicada (~${r.combo_count} combos) — escribir en "Su rango" la reemplaza.</div>`;
    };
  } catch (e) {
    resultEl.innerHTML = `<div class="notice error">${e.message}</div>`;
  }
}

document.getElementById('btn-calcular').onclick = async () => {
  const resultsEl = document.getElementById('decision-results');
  if (!hand) { resultsEl.innerHTML = '<div class="notice error">Primero tocá "Nueva mano".</div>'; return; }
  resultsEl.innerHTML = '<div class="notice">Calculando…</div>';

  const hero = heroPicker.getCards();
  if (hero.length !== 2) {
    resultsEl.innerHTML = '<div class="notice error">Elegí tus 2 cartas primero.</div>';
    return;
  }
  const board = boardPicker.getCards();
  const dead = deadPicker.getCards();
  const street = hand.street;
  const facingBet = facingBetNow();
  let bet, pot;
  if (facingBet) {
    bet = betAmountFacing();
    pot = potBeforeLastAction();
  } else {
    // nadie te apostó — si cargaste cuánto pensás apostar, se manda igual
    // (así "Calcular" también puede evaluar apostar de valor/farol, no solo chequear)
    const contemplated = document.getElementById('contemplated-bet').value;
    bet = contemplated ? parseFloat(contemplated) : null;
    pot = potNow();
  }
  const primary = primaryVillainName();
  const heroRangeNotation = document.getElementById('hero-range').value.trim();
  const heroPosition = document.getElementById('hero-position').value || null;
  const numPlayersRaw = document.getElementById('num-players').value;
  const numPlayers = numPlayersRaw ? parseInt(numPlayersRaw) : null;

  const active = activeNonHeroPlayers();
  if (!active.length) {
    resultsEl.innerHTML = '<div class="notice error">Todavía no hay ningún rival activo — configurá la mesa arriba.</div>';
    return;
  }
  const opponents = active.map(name => {
    const p = hand.players[name];
    let range;
    if (p.rangeNotation) range = { method: 'notation', notation: p.rangeNotation };
    else if (p.suggestedWeights) range = { method: 'paint', paint: p.suggestedWeights };
    else range = { method: 'random' };
    return { label: name, range };
  });

  const body = {
    hero, board, dead, street, facing_bet: facingBet,
    bet, pot,
    primary_villain: primary,
    opponents,
    hero_range: heroRangeNotation ? { method: 'notation', notation: heroRangeNotation } : null,
    hero_position: heroPosition,
    num_players: numPlayers,
    num_sims: 20000,
  };

  try {
    const r = await api('POST', '/api/decision', body);
    hand.pendingDecisionId = r.decision_id;
    renderDecisionResults(r);
  } catch (e) {
    resultsEl.innerHTML = `<div class="notice error">${e.message}</div>`;
  }
};

function renderDecisionResults(r) {
  const el = document.getElementById('decision-results');
  let html = '';

  if (r.validation_issues && r.validation_issues.length) {
    r.validation_issues.forEach(i => {
      html += `<div class="notice ${i.severity === 'error' ? 'error' : ''}">${i.message}</div>`;
    });
  }

  if (r.equity) {
    html += '<div class="card-panel"><h2>Equity</h2><div class="equity-bar">';
    r.equity.players.forEach((p, idx) => {
      const colors = ['var(--gold)', 'var(--bg-raised)', '#3a4a40', '#4a5a50'];
      html += `<div class="equity-seg" style="width:${p.equity_pct}%; background:${colors[idx % colors.length]}; color:${idx===0?'#1a1409':'var(--text)'}">${p.label} ${p.equity_pct}%</div>`;
    });
    html += `</div><p class="hint">Modo: ${r.equity.mode}</p></div>`;
  }

  if (r.hand_breakdown) {
    const b = r.hand_breakdown;
    html += '<div class="card-panel"><h2>Cantos</h2>';
    html += `<p style="margin-bottom:8px"><strong>Vos tenés:</strong> <span class="badge">${b.hero_hand_type}</span></p>`;
    if (b.villain_top_types.length) {
      html += `<p style="margin-bottom:8px"><strong>Rival (más probable):</strong> ` +
        b.villain_top_types.map(t => `<span class="badge">${t.name} ${t.pct}%</span>`).join(' ') + `</p>`;
    }
    if (b.danger_cards.length) {
      html += b.danger_cards.map(d => `<p class="hint">⚠️ ${d}</p>`).join('');
    }
    html += '</div>';
  }

  html += '<div class="card-panel"><h2>Acciones candidatas</h2>';
  const maxAbs = Math.max(...r.candidates.map(c => Math.abs(c.heuristic_value)), 0.01);
  r.candidates.forEach(c => {
    const cls = c.heuristic_value > 0 ? 'pos' : (c.heuristic_value < 0 ? 'neg' : '');
    const pct = Math.min(100, Math.abs(c.heuristic_value) / maxAbs * 100);
    const actionLabel = {fold: 'Retirarse', call: 'Pagar', check: 'Chequear', bet_value: 'Apostar (valor)', bet_bluff: 'Apostar (farol)'}[c.action] || c.action;
    html += `<div class="candidate">
      <div class="candidate-head">
        <span class="candidate-action">${actionLabel}</span>
        <span class="candidate-value ${cls}">${c.heuristic_value >= 0 ? '+' : ''}${c.heuristic_value}</span>
      </div>
      <div class="value-track"><div class="value-fill" style="width:${pct}%"></div></div>
      <div class="candidate-reasons">${c.top_reasons.map(x => `<p>${x}</p>`).join('')}</div>
    </div>`;
  });
  html += '</div>';

  if (r.gto_exploit) {
    html += `<div class="card-panel"><h2>Mezcla GTO / Explotador</h2>
      <p><span class="num">${Math.round(r.gto_exploit.weight_exploit_final*100)}%</span> línea explotadora
      <span class="badge">Punto 11</span></p>
      <p class="hint">${r.gto_exploit.reasoning}</p>
    </div>`;
  }

  if (r.bluff_opportunity) {
    const b = r.bluff_opportunity;
    html += `<div class="card-panel"><h2>Oportunidad de farol</h2>
      <p>${b.estimated_success_pct}% estimado vs. ${b.min_required_pct}% mínimo necesario
      <span class="badge">${b.is_above_threshold ? 'supera el umbral' : 'no supera el umbral'}</span></p>`;
    if (b.top_candidates && b.top_candidates.length) {
      html += '<p class="hint">Mejores combos candidatos: ' + b.top_candidates.map(c => c.hand_type).join(', ') + '</p>';
    }
    html += '</div>';
  }

  html += `<div class="notice">Cuando decidas, tocá "MI JUGADA" arriba — queda guardada sola para la revisión de sesión.</div>`;

  el.innerHTML = html;
}

// ============================================================
// VISTA: JUGADORES
// ============================================================
async function loadPlayers() {
  const listEl = document.getElementById('players-list');
  try {
    const r = await api('GET', '/api/players');
    if (!r.players.length) {
      listEl.innerHTML = '<div class="empty-state">Todavía no registraste ninguna mano.</div>';
      return;
    }
    listEl.innerHTML = r.players.map(p => `<div class="player-row" data-p="${p}"><span>${p}</span><span>›</span></div>`).join('');
    listEl.querySelectorAll('.player-row').forEach(row => {
      row.onclick = () => loadPlayerDetail(row.dataset.p);
    });
  } catch (e) {
    listEl.innerHTML = `<div class="notice error">${e.message}</div>`;
  }
}

async function loadPlayerDetail(player) {
  const el = document.getElementById('player-detail');
  el.innerHTML = '<div class="notice">Cargando…</div>';
  try {
    const p = await api('GET', `/api/players/${encodeURIComponent(player)}/profile`);
    const fmt = (v) => v === null || v === undefined ? '—' : (typeof v === 'number' ? v.toFixed(1) : v);
    el.innerHTML = `<div class="card-panel">
      <h2>${p.player}</h2>
      <p class="hint">${p.hands_dealt} manos registradas</p>
      <div class="stat-grid">
        <div class="stat-box"><div class="v">${fmt(p.vpip_pct)}%</div><div class="l">VPIP</div></div>
        <div class="stat-box"><div class="v">${fmt(p.pfr_pct)}%</div><div class="l">PFR</div></div>
        <div class="stat-box"><div class="v">${fmt(p.aggression_factor)}</div><div class="l">AF</div></div>
        <div class="stat-box"><div class="v">${fmt(p.threebet_pct)}%</div><div class="l">3-bet</div></div>
        <div class="stat-box"><div class="v">${fmt(p.fold_to_cbet_pct)}%</div><div class="l">fold-vs-cbet</div></div>
        <div class="stat-box"><div class="v">${fmt(p.tightness_score)}</div><div class="l">tightness</div></div>
      </div>
      <p class="hint">Agresión (Punto 3): ${fmt(p.aggression_score)}/100</p>
      <h3 style="margin-top:16px">Notas</h3>
      ${p.notes.length ? p.notes.map(n => `<p>• ${n.text} ${n.tag ? `<span class="badge">${n.tag}</span>` : ''}</p>`).join('') : '<p class="hint">Sin notas todavía.</p>'}
      <div class="field" style="margin-top:12px">
        <label>Agregar nota</label>
        <textarea id="new-note-text" placeholder="ej. Sobre-apuesta el flop casi siempre con manos monstruo"></textarea>
      </div>
      <div class="field">
        <label>Etiqueta (opcional)</label>
        <input type="text" id="new-note-tag" placeholder="sizing-tell, tilt, ...">
      </div>
      <button class="primary" id="btn-add-note">Guardar nota</button>
    </div>`;

    document.getElementById('btn-add-note').onclick = async () => {
      const text = document.getElementById('new-note-text').value.trim();
      if (!text) return;
      const tag = document.getElementById('new-note-tag').value.trim() || null;
      await api('POST', '/api/players/notes', {player, text, tag});
      loadPlayerDetail(player);
    };
  } catch (e) {
    el.innerHTML = `<div class="notice error">${e.message}</div>`;
  }
}

// ============================================================
// VISTA: MANOS (registrar historial)
// ============================================================
const handBoardPicker = makeCardPicker('hand-board-slots', 5);
let actionRows = [];
let actionRowCounter = 0;

function addActionRow() {
  const id = actionRowCounter++;
  actionRows.push(id);
  renderActionRows();
}

function renderActionRows() {
  const el = document.getElementById('hand-actions-list');
  el.innerHTML = actionRows.map(id => `
    <div class="action-item" data-id="${id}">
      <input type="text" class="a-player" placeholder="jugador" style="width:90px">
      <select class="a-street">
        <option value="preflop">preflop</option><option value="flop">flop</option>
        <option value="turn">turn</option><option value="river">river</option>
      </select>
      <select class="a-type">
        <option value="post_blind">post_blind</option><option value="fold">fold</option>
        <option value="check">check</option><option value="call">call</option>
        <option value="bet">bet</option><option value="raise">raise</option>
      </select>
      <input type="number" class="a-pot" placeholder="% bote (ej 0.7)" step="0.01" style="width:100px">
      <button class="remove-btn" data-remove="${id}">✕</button>
    </div>
  `).join('');
  el.querySelectorAll('[data-remove]').forEach(btn => {
    btn.onclick = () => {
      actionRows = actionRows.filter(id => id !== parseInt(btn.dataset.remove));
      renderActionRows();
    };
  });
}

document.getElementById('btn-add-action').onclick = addActionRow;
addActionRow(); addActionRow();

const showdownToggle = makeToggleGroup('showdown-toggle', 'false', (v) => {
  document.getElementById('showdown-hands-field').style.display = v === 'true' ? 'block' : 'none';
});

document.getElementById('btn-submit-hand').onclick = async () => {
  const resultEl = document.getElementById('hand-submit-result');
  const handId = document.getElementById('hand-id').value.trim();
  const players = document.getElementById('hand-players').value.split(',').map(s => s.trim()).filter(Boolean);
  const board = handBoardPicker.getCards();
  const winners = document.getElementById('hand-winners').value.split(',').map(s => s.trim()).filter(Boolean);
  const showdown = showdownToggle.get() === 'true';

  const actions = [...document.querySelectorAll('#hand-actions-list .action-item')].map((row, idx) => {
    const potVal = row.querySelector('.a-pot').value;
    const type = row.querySelector('.a-type').value;
    return {
      player: row.querySelector('.a-player').value.trim(),
      street: row.querySelector('.a-street').value,
      action_type: type,
      order: idx,
      pot_fraction: (potVal && (type === 'bet' || type === 'raise')) ? parseFloat(potVal) : null,
    };
  });

  let showdown_hands = {};
  if (showdown) {
    const raw = document.getElementById('hand-showdown-hands').value.trim();
    raw.split(';').map(s => s.trim()).filter(Boolean).forEach(pair => {
      const [player, cards] = pair.split(':');
      const [c1, c2] = cards.split(',').map(s => s.trim());
      if (player && c1 && c2) showdown_hands[player.trim()] = [c1, c2];
    });
  }

  try {
    const r = await api('POST', '/api/hands', {
      hand_id: handId || ('mano-' + Date.now()), players, board, actions, winners, showdown, showdown_hands,
    });
    if (r.accepted) {
      resultEl.innerHTML = '<div class="notice">Mano guardada — se sumó al historial.</div>';
    } else {
      resultEl.innerHTML = '<div class="notice error">' + r.issues.map(i => i.message).join('<br>') + '</div>';
    }
  } catch (e) {
    resultEl.innerHTML = `<div class="notice error">${e.message}</div>`;
  }
};

// ============================================================
// VISTA: SESIÓN
// ============================================================
async function loadSession() {
  const summaryEl = document.getElementById('session-summary');
  const reviewEl = document.getElementById('session-hands-to-review');
  try {
    const s = await api('GET', '/api/session/review');
    if (!s.n_decisions) {
      summaryEl.innerHTML = '<div class="empty-state">Todavía no registraste ninguna decisión.</div>';
      reviewEl.innerHTML = '';
      return;
    }
    summaryEl.innerHTML = `
      <div class="stat-grid">
        <div class="stat-box"><div class="v">${s.n_decisions}</div><div class="l">decisiones</div></div>
        <div class="stat-box"><div class="v">${s.match_rate_pct}%</div><div class="l">coincidencia</div></div>
        <div class="stat-box"><div class="v">${s.total_value_lost}</div><div class="l">valor perdido</div></div>
      </div>`;

    const hr = await api('GET', '/api/session/review/hands-to-review?top_n=10');
    reviewEl.innerHTML = hr.hands.length
      ? hr.hands.map(h => `<div class="candidate">
          <div class="candidate-head">
            <span class="candidate-action">${h.hand_id} · ${h.street}</span>
            <span class="candidate-value ${h.value_gap > 0 ? 'neg' : ''}">${h.value_gap}</span>
          </div>
          <div class="candidate-reasons"><p>Hiciste: ${h.actual_action} · Mejor: ${h.best_recommendation}</p></div>
        </div>`).join('')
      : '<div class="empty-state">Nada para repasar todavía.</div>';
  } catch (e) {
    summaryEl.innerHTML = `<div class="notice error">${e.message}</div>`;
  }
}
