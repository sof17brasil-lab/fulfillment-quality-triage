/* Method & SQL page. Everything here is rendered from the same data/ files the
   dashboard reads, so the two pages cannot disagree. */

const DATA = 'data/';
const BUILD = Date.now();     // see the note in main.js

async function json(n, attempt = 0) {
  const r = await fetch(`${DATA}${n}.json?v=${BUILD}.${attempt}`, { cache: 'no-store' });
  if (!r.ok) throw new Error(`could not load ${n} (HTTP ${r.status})`);
  const t = await r.text();
  try {
    return JSON.parse(t);
  } catch {
    if (attempt < 2) return json(n, attempt + 1);
    throw new Error(`${n} arrived incomplete (${t.length} bytes) after ${attempt + 1} attempts`);
  }
}
const text = (p) => fetch(`${p}?v=${BUILD}`, { cache: 'no-store' })
  .then((r) => r.ok ? r.text() : Promise.reject(p));

const cell = (tr, value, cls) => {
  const td = document.createElement('td');
  if (cls) td.className = cls;
  td.textContent = value;
  tr.appendChild(td);
  return td;
};

/* ---------- validation checks ---------- */
function renderChecks(rows) {
  const tb = document.querySelector('#t-checks tbody');
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    cell(tr, r.n, 'is-text');
    cell(tr, r.check_name, 'is-text');
    cell(tr, Number(r.expected).toLocaleString('en-US'));
    cell(tr, Number(r.actual).toLocaleString('en-US'));
    cell(tr, r.status, 'is-text ' + (r.status === 'PASS' ? 'pass' : 'fail'));
    tb.appendChild(tr);
  });
  const passed = rows.filter((r) => r.status === 'PASS').length;
  document.getElementById('checks-summary').textContent =
    `${passed} of ${rows.length} passing on this build.`;
}

/* ---------- the ledger ---------- */
function renderLedger(rows) {
  const tb = document.querySelector('#t-ledger tbody');
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    cell(tr, r.id, 'is-text q');
    cell(tr, r.claim, 'is-text');
    cell(tr, r.value);
    cell(tr, r.unit, 'is-text');
    cell(tr, r.sql_source, 'is-text q');
    cell(tr, r.agreement === 'MATCH' ? 'matched' : 'SQL only',
         'is-text ' + (r.agreement === 'MATCH' ? 'pass' : ''));
    tb.appendChild(tr);
  });
  const matched = rows.filter((r) => r.agreement === 'MATCH').length;
  document.getElementById('ledger-summary').textContent =
    `${rows.length} numbers. ${matched} recomputed independently in pandas and matched; ` +
    `${rows.length - matched} come from SQL only.`;
}

/* ---------- sources ---------- */
function renderSources(facts) {
  const tb = document.querySelector('#t-sources tbody');
  facts.forEach((f) => {
    const tr = document.createElement('tr');
    cell(tr, f.id, 'is-text q');
    cell(tr, f.fact, 'is-text');
    cell(tr, f.words, 'is-text');
    tb.appendChild(tr);
  });
  document.getElementById('sources-summary').textContent =
    `${facts.length} outside facts are quoted on the site. Every one is ticked in SOURCES.md. ` +
    `Unticked sources are held back by the build.`;
}

/* ---------- SQL files ---------- */
async function renderSql(names) {
  const host = document.getElementById('sql-list');
  for (const name of names) {
    const d = document.createElement('details');
    const s = document.createElement('summary');
    s.textContent = name;
    d.appendChild(s);
    host.appendChild(d);

    let body = null;
    d.addEventListener('toggle', async () => {
      if (!d.open || body) return;
      body = document.createElement('pre');
      body.textContent = 'loading…';
      d.appendChild(body);
      try { body.textContent = await text('sql/' + name); }
      catch { body.textContent = 'could not load ' + name; }
    });

    // the question each file answers sits in its first comment lines
    try {
      const src = await text('sql/' + name);
      const q = src.split('\n').slice(1).filter((l) => l.startsWith('--'))
                   .map((l) => l.replace(/^--\s?/, '').trim())
                   .filter(Boolean)[0];
      if (q) {
        const em = document.createElement('em');
        em.textContent = q;
        s.appendChild(em);
      }
    } catch { /* the summary still works without it */ }
  }
}

async function boot() {
  // sequential: see the concurrency note in main.js
  const checks = await json('09_validation_checks');
  const ledger = await json('numbers_ledger');
  const facts = await json('public_facts');
  const manifest = await json('sql_manifest');
  renderChecks(checks[0]);
  renderLedger(ledger);
  renderSources(facts);
  await renderSql(manifest);
  document.documentElement.dataset.ready = 'true';
}

boot().catch((e) => {
  console.error(e);
  document.documentElement.dataset.ready = 'error';
});
