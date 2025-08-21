const state = {
  topic: 'overall',
  sortKey: 'overall',
  sortDir: 'desc',
  rows: [],
  filtered: []
};

const tBody = () => document.querySelector('#leaderboard tbody');
const headers = () => Array.from(document.querySelectorAll('#leaderboard thead th.sortable'));

async function load(topic) {
  const errorBoxId = 'error-box';
  const showError = (msg) => {
    let el = document.getElementById(errorBoxId);
    if (!el) {
      el = document.createElement('div');
      el.id = errorBoxId;
      el.style.color = '#b00020';
      el.style.margin = '8px 0';
      const container = document.querySelector('#leaderboard')?.parentElement || document.body;
      container.prepend(el);
    }
    el.textContent = msg;
  };
  const clearError = () => {
    const el = document.getElementById(errorBoxId);
    if (el) el.textContent = '';
  };

  try {
    const res = await fetch(`/api/leaderboard?topic=${encodeURIComponent(topic)}`);
    if (!res.ok) {
      showError(`Failed to load leaderboard (${res.status})`);
      return;
    }
    const data = await res.json();
    clearError();
    state.rows = Array.isArray(data) ? data : [];
    applyFilter();
  } catch (err) {
    showError('Network error while loading leaderboard. Please retry.');
  }
}

function applyFilter() {
  const q = document.getElementById('search').value.trim().toLowerCase();
  state.filtered = !q ? state.rows : state.rows.filter(r =>
    r.model.toLowerCase().includes(q) || r.org.toLowerCase().includes(q)
  );
  sortAndRender();
}

function sortAndRender() {
  const key = state.sortKey;
  const dir = state.sortDir === 'asc' ? 1 : -1;
  const numeric = ['rank','text','translate','vision','overall'];
  const rows = [...state.filtered].sort((a,b)=>{
    const av = a[key], bv = b[key];
    if (numeric.includes(key)) return (av - bv) * dir;
    return av.localeCompare(bv) * dir;
  });
  render(rows);
  markSortedColumn();
}

function render(rows) {
  const fmtDate = (iso) => new Date(iso).toLocaleDateString('nl-NL', { year: 'numeric', month: 'short', day: 'numeric' });
  const html = rows.map(r => `
    <tr>
      <td>${r.rank}</td>
      <td class="left">${r.model}</td>
      <td class="left">${r.org}</td>
      <td>${r.text.toFixed(1)}</td>
      <td>${r.translate.toFixed(1)}</td>
      <td>${r.vision.toFixed(1)}</td>
      <td><strong>${r.overall.toFixed(1)}</strong></td>
      <td class="left">${fmtDate(r.updated_at)}</td>
    </tr>
  `).join('');
  tBody().innerHTML = html;
}

function markSortedColumn(){
  headers().forEach(h=>h.classList.remove('sorted-asc','sorted-desc'));
  const h = headers().find(h=>h.dataset.key===state.sortKey);
  if (h) h.classList.add(state.sortDir==='asc'?'sorted-asc':'sorted-desc');
}

function setupSorting(){
  headers().forEach(h=>{
    h.addEventListener('click', ()=>{
      const key = h.dataset.key;
      if (state.sortKey === key) {
        state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
      } else {
        state.sortKey = key;
        state.sortDir = key === 'model' || key === 'org' ? 'asc' : 'desc';
      }
      sortAndRender();
    });
  });
}

function setupTabs(){
  const tabs = Array.from(document.querySelectorAll('.tab'));
  tabs.forEach(tab=>{
    tab.addEventListener('click', ()=>{
      tabs.forEach(t=>t.classList.remove('active'));
      tab.classList.add('active');
      state.topic = tab.dataset.topic;
      // default sort
      if (state.topic === 'overall') {
        state.sortKey = 'overall'; state.sortDir = 'desc';
      } else if (state.topic === 'text' || state.topic === 'translate' || state.topic === 'vision') {
        state.sortKey = tab.dataset.topic; state.sortDir = 'desc';
      }
      load(state.topic);
    });
  });
}

function setupSearch(){
  document.getElementById('search').addEventListener('input', ()=>{
    applyFilter();
  });
}

window.addEventListener('DOMContentLoaded', ()=>{
  setupSorting();
  setupTabs();
  setupSearch();
  load(state.topic);
});
