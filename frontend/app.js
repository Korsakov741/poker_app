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
// Selector de cartas — grilla de las 52 SIEMPRE visible, UN
// toque llena el próximo espacio vacío (sin elegir el espacio antes).
// Para borrar una carta, tocás esa carta ya puesta en la fila de arriba.
// ============================================================
function makeCardPicker(containerId, initialMax) {
  const container = document.getElementById(containerId);
  let max = initialMax;
  let cards = [];

  function nextEmptyIndex() {
    for (let i = 0; i < max; i++) if (!cards[i]) return i;
    return -1;
  }

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
        slot.onclick = () => {
          cards[i] = null;
          render();
          if (containerId === 'board-slots') onBoardChanged();
        };
      } else {
        slot.className = 'card-slot empty';
        slot.textContent = '+';
      }
      slotsRow.appendChild(slot);
    }
    container.appendChild(slotsRow);

    if (max > 0) {
      const grid = document.createElement('div');
      grid.className = 'card-grid-picker';
      RANKS.slice().reverse().forEach(r => {
        const row = document.createElement('div');
        row.className = 'card-grid-row';
        SUITS.forEach(([letter, symbol]) => {
          const code = r + letter;
          const used = cards.includes(code);
          const cell = document.createElement('div');
          cell.className = 'card-grid-cell' + ((letter === 'h' || letter === 'd') ? ' red' : '') + (used ? ' used' : '');
          cell.textContent = r + symbol;
          if (!used) {
            cell.onclick = () => {
              const idx = nextEmptyIndex();
              if (idx === -1) return; // lleno — tocá una carta puesta arriba para borrarla primero
              cards[idx] = code;
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
    setMax: (n) => { max = n; cards = cards.slice(0, n); render(); },
    clear: () => { cards = []; render(); },
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
// VISTA: DECISIÓN — "mano en curso" (modo rápido: sin bote, sin
// acciones con monto — solo cartas, quién sigue activo, y rangos
// opcionales. Todo lo que dependía de montos quedó oculto, no
// borrado: el motor sigue soportándolo igual si algún día vuelve.)
// ============================================================
const heroPicker = makeCardPicker('hero-slots', 2);
const boardPicker = makeCardPicker('board-slots', 5);
const deadPicker = makeCardPicker('dead-slots', 4);

const POSITION_OPTIONS = [
  ['', '— sin especificar —'], ['early', 'Temprana'], ['middle', 'Media'], ['late', 'Tardía'],
  ['button', 'Botón'], ['sb', 'Ciega chica'], ['bb', 'Ciega grande'],
];

// la calle se deduce SOLA de cuántas cartas hay cargadas en el board —
// ya no hace falta un botón "siguiente calle" que avanza a mano
function streetFromBoardLength(n) {
  if (n === 0) return 'preflop';
  if (n === 3) return 'flop';
  if (n === 4) return 'turn';
  if (n === 5) return 'river';
  return null; // 1 o 2 cartas: todavía no es una calle válida
}

function onBoardChanged() {
  const label = document.getElementById('current-street-label');
  const street = streetFromBoardLength(boardPicker.getCards().length);
  label.textContent = street || '— cargando board —';
}

// ---------- configuración de mesa (se recuerda entre manos de la misma sesión) ----------
let tableSeatActive = {};

function renderSeatConfig() {
  const size = parseInt(document.getElementById('table-size-input').value) || 6;
  const row = document.getElementById('seat-config-row');
  row.innerHTML = '';
  for (let i = 1; i <= size; i++) {
    const name = `A${i}`;
    if (!(name in tableSeatActive)) tableSeatActive[name] = true;
    const btn = document.createElement('div');
    btn.className = 'seat-btn' + (tableSeatActive[name] ? '' : ' off');
    btn.textContent = name;
    btn.onclick = () => { tableSeatActive[name] = !tableSeatActive[name]; renderSeatConfig(); };
    row.appendChild(btn);
  }
  Object.keys(tableSeatActive).forEach(k => {
    const num = parseInt(k.replace('A', ''));
    if (num > size) delete tableSeatActive[k];
  });
}
document.getElementById('table-size-input').addEventListener('input', renderSeatConfig);

document.getElementById('btn-apply-table-size').onclick = () => {
  if (!hand) { alert('Primero tocá "Nueva mano"'); return; }
  localStorage.setItem('pokerapp_table_size', document.getElementById('table-size-input').value);
  Object.keys(tableSeatActive).forEach(name => {
    if (tableSeatActive[name]) {
      if (!hand.players[name]) hand.players[name] = { position: '', active: true, rangeNotation: '' };
    } else if (hand.players[name]) {
      delete hand.players[name];
    }
  });
  refreshHandUI();
};

// ---------- estado de la mano en curso ----------
function newHandState() {
  return {
    players: {}, // {nombre: {position, active, rangeNotation}}
  };
}
let hand = null;

function activeNonHeroPlayers() {
  if (!hand) return [];
  return Object.keys(hand.players).filter(p => hand.players[p].active);
}

document.getElementById('btn-new-hand').onclick = () => {
  hand = newHandState();
  heroPicker.clear();
  boardPicker.clear();
  deadPicker.clear();
  document.getElementById('table-size-input').value = localStorage.getItem('pokerapp_table_size') || '6';
  document.getElementById('hand-active-ui').style.display = 'block';
  document.getElementById('hand-status-text').textContent = 'Mano en curso.';
  document.getElementById('decision-results').innerHTML = '';
  onBoardChanged();
  renderSeatConfig();
  // los asientos marcados activos de una mano anterior arrancan cargados solos
  Object.keys(tableSeatActive).forEach(name => {
    if (tableSeatActive[name]) hand.players[name] = { position: '', active: true, rangeNotation: '' };
  });
  refreshHandUI();
};

function refreshHandUI() {
  if (!hand) return;
  refreshSeatActionRow();
  refreshPlayersPanel();
}

function refreshSeatActionRow() {
  const row = document.getElementById('seat-action-row');
  const names = Object.keys(hand.players);
  if (!names.length) {
    row.innerHTML = '<p class="hint">Configurá la mesa arriba para que aparezcan los rivales acá.</p>';
    return;
  }
  row.innerHTML = '';
  names.forEach(name => {
    const p = hand.players[name];
    const btn = document.createElement('div');
    btn.className = 'seat-btn' + (p.active ? '' : ' retired');
    btn.textContent = name;
    btn.onclick = () => { hand.players[name].active = !hand.players[name].active; refreshHandUI(); };
    row.appendChild(btn);
  });
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
      `;
      panel.appendChild(card);
      card.querySelector('.player-position').value = p.position || '';
      card.querySelector('.player-range').value = p.rangeNotation || '';
      card.querySelector('.player-position').addEventListener('change', (e) => { hand.players[name].position = e.target.value; });
      card.querySelector('.player-range').addEventListener('input', (e) => { hand.players[name].rangeNotation = e.target.value; });
    }
    const badge = card.querySelector('.player-status-badge');
    badge.textContent = p.active ? 'activo' : 'retirado';
    card.style.opacity = p.active ? '1' : '0.5';
  });
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
  const street = streetFromBoardLength(board.length);
  if (street === null) {
    resultsEl.innerHTML = '<div class="notice error">Te faltan cartas para una calle válida — necesitás 0 (preflop), 3 (flop), 4 (turn) o 5 (río) cartas en el board, no 1 ni 2.</div>';
    return;
  }
  const dead = deadPicker.getCards();
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
    return { label: name, range: p.rangeNotation ? { method: 'notation', notation: p.rangeNotation } : { method: 'random' } };
  });

  const body = {
    hero, board, dead, street, facing_bet: false,
    primary_villain: active[0],
    opponents,
    hero_range: heroRangeNotation ? { method: 'notation', notation: heroRangeNotation } : null,
    hero_position: heroPosition,
    num_players: numPlayers,
    num_sims: 20000,
  };

  try {
    const r = await api('POST', '/api/decision', body);
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
      // flex-grow en vez de width fijo: así cada jugador tiene un ancho
      // MÍNIMO garantizado (min-width) aunque su equity sea 0% — antes,
      // con 0%, el segmento quedaba con ancho cero y el número
      // desaparecía por completo (el bote SIGUE mostrando el número real,
      // esto es solo un arreglo de cómo se ve, no del cálculo)
      html += `<div class="equity-seg" style="flex-grow:${Math.max(p.equity_pct, 0.1)}; flex-basis:0; min-width:54px; background:${colors[idx % colors.length]}; color:${idx===0?'#1a1409':'var(--text)'}">${p.label} ${p.equity_pct}%</div>`;
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
  } else if (r.street === 'preflop') {
    html += '<p class="hint">Cargá las 3 cartas del flop para ver "Cantos" (tu mano clasificada y la del rival).</p>';
  }

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
