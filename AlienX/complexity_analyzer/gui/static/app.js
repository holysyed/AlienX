/* ─────────────────────────────────────────────────────────
   Algorithm Complexity Analyzer — Frontend Script
   app.js
───────────────────────────────────────────────────────── */

'use strict';

// ── DOM references ────────────────────────────────────────
const $ = id => document.getElementById(id);
const analyzeBtn    = $('analyzeBtn');
const clearBtn      = $('clearBtn');
const langSelect    = $('langSelect');
const themeToggle   = $('themeToggle');
const demoChips     = $('demoChips');

const emptyState    = $('emptyState');
const resultsContent= $('resultsContent');
const errorState    = $('errorState');
const errorMsg      = $('errorMsg');

const resultHeader  = $('resultHeader');
const scoreSection  = $('scoreSection');
const caseGrid      = $('caseGrid');
const breakdownGrid = $('breakdownGrid');
const breakdownCard = $('breakdownCard');
const recurrenceCard= $('recurrenceCard');
const recurrenceBody= $('recurrenceBody');
const obsCard       = $('obsCard');
const obsList       = $('obsList');
const sugList       = $('sugList');

// ── CodeMirror Setup ─────────────────────────────────────
const cm = CodeMirror.fromTextArea($('codeEditor'), {
  theme:        'dracula',
  mode:         'python',
  lineNumbers:  true,
  tabSize:      4,
  indentWithTabs: false,
  lineWrapping: false,
  autofocus:    true,
  extraKeys: {
    'Ctrl-Enter': runAnalysis,
    'Cmd-Enter':  runAnalysis,
    Tab: cm => cm.execCommand('indentMore'),
  },
});
cm.setSize('100%', '100%');

// ── Theme Toggle ─────────────────────────────────────────
const THEME_KEY = 'aca-theme';
(function initTheme() {
  if (localStorage.getItem(THEME_KEY) === 'light') enableLight();
})();

themeToggle.addEventListener('click', () => {
  if (document.body.classList.contains('light')) {
    document.body.classList.remove('light');
    cm.setOption('theme', 'dracula');
    localStorage.setItem(THEME_KEY, 'dark');
  } else {
    enableLight();
    localStorage.setItem(THEME_KEY, 'light');
  }
});

function enableLight() {
  document.body.classList.add('light');
  cm.setOption('theme', 'default');
}

// ── Language → CodeMirror mode map ───────────────────────
const LANG_MODES = {
  python:     'python',
  c:          'text/x-csrc',
  cpp:        'text/x-c++src',
  java:       'text/x-java',
  javascript: 'javascript',
  pseudocode: 'text/plain',
  auto:       null,
};

langSelect.addEventListener('change', () => {
  const mode = LANG_MODES[langSelect.value] || 'python';
  cm.setOption('mode', mode);
});

// ── Clear ────────────────────────────────────────────────
clearBtn.addEventListener('click', () => {
  cm.setValue('');
  cm.focus();
  showEmpty();
});

// ── Analyze button ────────────────────────────────────────
analyzeBtn.addEventListener('click', runAnalysis);

async function runAnalysis() {
  const code = cm.getValue().trim();
  if (!code) { showEmpty(); return; }

  setLoading(true);
  hideAll();

  try {
    const resp = await fetch('/api/analyze', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ code, language: langSelect.value }),
    });
    const data = await resp.json();
    if (!resp.ok || data.error) throw new Error(data.error || 'Analysis failed');
    renderResults(data);
  } catch (err) {
    showError(err.message || 'Something went wrong. Make sure the server is running.');
  } finally {
    setLoading(false);
  }
}

// ── Load demos on startup ────────────────────────────────
(async function loadDemos() {
  try {
    const resp = await fetch('/api/demos');
    const demos = await resp.json();
    demos.forEach(d => {
      const chip = document.createElement('button');
      chip.className = 'demo-chip';
      chip.innerHTML = `${d.name} <span class="chip-badge ${badgeClass(d.complexity)}">${d.complexity}</span>`;
      chip.addEventListener('click', () => loadDemo(d));
      demoChips.appendChild(chip);
    });
  } catch { /* server not ready yet */ }
})();

function badgeClass(c) {
  if (c.includes('log n') && !c.includes('n log')) return 'badge-fast';
  if (c === 'O(1)') return 'badge-fast';
  if (c.includes('n log') || c === 'O(n)') return 'badge-med';
  if (c.includes('2^') || c.includes('n!')) return 'badge-exp';
  return 'badge-slow';
}

function loadDemo(demo) {
  cm.setValue(demo.code);
  langSelect.value = demo.language;
  const mode = LANG_MODES[demo.language] || 'python';
  cm.setOption('mode', mode);
  runAnalysis();
}

// ── State helpers ────────────────────────────────────────
function setLoading(on) {
  analyzeBtn.disabled = on;
  analyzeBtn.classList.toggle('loading', on);
}

function hideAll() {
  emptyState.classList.add('hidden');
  resultsContent.style.display = 'none';
  errorState.classList.add('hidden');
}

function showEmpty() {
  hideAll();
  emptyState.classList.remove('hidden');
}

function showError(msg) {
  hideAll();
  errorMsg.textContent = msg;
  errorState.classList.remove('hidden');
}

// ── Render results ───────────────────────────────────────
function renderResults(d) {
  hideAll();

  // Header
  resultHeader.innerHTML = `
    <div class="result-header-inner">
      <span class="lang-badge lang-${d.language}">${d.language}</span>
      <div>
        ${d.known_algorithm ? `<div class="result-algo-name">${d.known_algorithm}</div>` : ''}
        <div class="result-desc">${d.description}</div>
      </div>
    </div>`;

  // Score meter
  const rank = d.worst_rank || 5;
  const pct  = Math.min(100, (rank / 10) * 100);
  const meterColor = complexityColor(rank);
  scoreSection.innerHTML = `
    <div class="score-card">
      <div class="score-label">Complexity Overview</div>
      <div class="complexity-meter">
        <div class="complexity-meter-fill" id="meterFill"
             style="width:0%;background:${meterColor}"></div>
      </div>
      <div class="score-values">
        <div class="score-val">
          <div class="score-val-label">Best</div>
          <div class="score-val-text" style="color:var(--emerald)">${d.complexity.best?.notation || '—'}</div>
        </div>
        <div class="score-val">
          <div class="score-val-label">Average</div>
          <div class="score-val-text" style="color:var(--amber)">${d.complexity.average?.notation || '—'}</div>
        </div>
        <div class="score-val">
          <div class="score-val-label">Worst</div>
          <div class="score-val-text" style="color:var(--rose)">${d.complexity.worst?.notation || '—'}</div>
        </div>
        <div class="score-val">
          <div class="score-val-label">Space</div>
          <div class="score-val-text" style="color:var(--cyan)">${d.complexity.space?.notation || '—'}</div>
        </div>
      </div>
    </div>`;
  setTimeout(() => {
    const fill = $('meterFill');
    if (fill) fill.style.width = pct + '%';
  }, 60);

  // Case cards
  const cases = [
    { key: 'best',    label: 'Best Case',    type: 'best',    notation: 'Omega (Ω)' },
    { key: 'average', label: 'Average Case', type: 'average', notation: 'Theta (Θ)' },
    { key: 'worst',   label: 'Worst Case',   type: 'worst',   notation: 'Big-O (O)' },
    { key: 'space',   label: 'Space',        type: 'space',   notation: 'Auxiliary' },
  ];
  caseGrid.innerHTML = cases.map(c => {
    const comp = d.complexity[c.key];
    if (!comp) return '';
    return `
      <div class="case-card case-${c.type}">
        <div class="case-card-top">
          <span class="case-card-type type-${c.type}">${c.label}</span>
          <span class="case-notation">${c.notation}</span>
        </div>
        <div class="case-complexity">${comp.notation}</div>
        <div class="case-explanation">${comp.explanation}</div>
      </div>`;
  }).join('');

  // Breakdown
  renderBreakdown(d.breakdown);

  // Recurrence
  if (d.recurrence) {
    recurrenceCard.classList.remove('hidden');
    renderRecurrence(d.recurrence);
  } else {
    recurrenceCard.classList.add('hidden');
  }

  // Observations
  renderObservations(d.observations, d.suggestions);

  resultsContent.style.display = 'flex';
}

function complexityColor(rank) {
  if (rank <= 2) return 'linear-gradient(90deg, #34d399, #6ee7b7)';
  if (rank <= 4) return 'linear-gradient(90deg, #34d399, #fbbf24)';
  if (rank <= 6) return 'linear-gradient(90deg, #fbbf24, #fb923c)';
  if (rank <= 8) return 'linear-gradient(90deg, #fb923c, #f43f5e)';
  return 'linear-gradient(90deg, #f43f5e, #a21caf)';
}

// ── Breakdown renderer ───────────────────────────────────
function renderBreakdown(b) {
  const rows = [];

  // Loops
  const nd = b.max_nesting;
  const dc = nd <= 1 ? 'depth-' + nd : nd === 2 ? 'depth-2' : nd === 3 ? 'depth-3' : 'depth-high';
  rows.push(['Loops', b.loops.length
    ? b.loops.slice(0, 4).map(l => `<span class="tag tag-loop">${escHtml(l.split('(')[0].trim())}</span>`).join('') +
      (b.loops.length > 4 ? `<span class="tag">+${b.loops.length - 4} more</span>` : '')
    : '<span style="color:var(--text-3)">None</span>']);

  rows.push(['Max Nesting', `<span class="depth-badge ${dc}">${nd}</span>`]);

  rows.push(['Recursion', b.has_recursion
    ? b.recursive_funcs.map(f => `<span class="tag tag-rec">${escHtml(f)}</span>`).join('')
    : '<span style="color:var(--text-3)">None</span>']);

  rows.push(['Conditionals', b.conditionals.length
    ? b.conditionals.slice(0, 3).map(c => `<span class="tag tag-cond">${escHtml(c)}</span>`).join('') +
      (b.conditionals.length > 3 ? `<span class="tag">+${b.conditionals.length - 3}</span>` : '')
    : '<span style="color:var(--text-3)">None</span>']);

  rows.push(['Built-in Calls', b.builtin_calls.length
    ? b.builtin_calls.slice(0, 4).map(([n, c]) =>
        `<span class="tag tag-builtin">${escHtml(n)}()</span>`).join('')
    : '<span style="color:var(--text-3)">None</span>']);

  rows.push(['Functions', b.functions.length
    ? b.functions.slice(0, 5).map(f => `<span class="tag tag-func">${escHtml(f)}</span>`).join('')
    : '<span style="color:var(--text-3)">—</span>']);

  if (b.data_structures && b.data_structures.length) {
    rows.push(['Data Structures', [...new Set(b.data_structures)].map(s =>
      `<span class="tag">${escHtml(s)}</span>`).join('')]);
  } else {
    rows.push(['Data Structures', '<span style="color:var(--text-3)">None</span>']);
  }

  breakdownGrid.innerHTML = rows.map(([key, val]) => `
    <div class="breakdown-row">
      <div class="breakdown-key">${key}</div>
      <div class="breakdown-val">${val}</div>
    </div>`).join('');
}

// ── Recurrence renderer ──────────────────────────────────
function renderRecurrence(r) {
  recurrenceBody.innerHTML = `
    <div class="recurrence-eq">${escHtml(r.relation)}</div>
    <div class="recurrence-meta">
      ${r.master_case ? `
        <div class="meta-row">
          <span class="meta-key">Theorem</span>
          <span class="meta-val muted">${escHtml(r.master_case)}</span>
        </div>` : ''}
      <div class="meta-row">
        <span class="meta-key">Solution</span>
        <span class="meta-val highlight">${escHtml(r.solution)}</span>
      </div>
      <div class="meta-row">
        <span class="meta-key">Stack Space</span>
        <span class="meta-val">${escHtml(r.space)}</span>
      </div>
    </div>`;
}

// ── Observations renderer ─────────────────────────────────
function renderObservations(obs, sug) {
  // Parse [OK] / [!!] icons
  function parseObs(text) {
    text = text.replace(/\[bold cyan\](.*?)\[\/bold cyan\]/gi, '<strong style="color:var(--cyan)">$1</strong>');
    if (text.startsWith('[OK]')) return { icon: '✓', cls: 'emerald', text: text.replace('[OK]', '').trim() };
    if (text.startsWith('[!!]')) return { icon: '!', cls: 'rose',    text: text.replace('[!!]', '').trim() };
    return { icon: '·', cls: 'text-3', text };
  }

  obsList.innerHTML = obs.length ? `
    <div class="obs-list">${obs.map(o => {
      const p = parseObs(o);
      return `<div class="obs-item">
        <span class="obs-icon" style="color:var(--${p.cls})">${p.icon}</span>
        <span class="obs-text">${p.text}</span>
      </div>`;
    }).join('')}</div>` : '';

  sugList.innerHTML = sug.length ? `
    <div class="sug-list">${sug.map(s => `
      <div class="sug-item">
        <span class="sug-arrow">-&gt;</span>
        <span class="sug-text">${escHtml(s)}</span>
      </div>`).join('')}</div>` : '';
}

// ── Utility ──────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
