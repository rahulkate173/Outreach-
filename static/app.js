const API = '/api';
const statusEl = document.getElementById('status');
const outreachEl = document.getElementById('outreach');
const fileEl = document.getElementById('file');
const rawEl = document.getElementById('raw');
const btnEl = document.getElementById('btn');
const historyListEl = document.getElementById('historyList');
const emptyHistoryEl = document.getElementById('emptyHistory');
const ollamaBannerEl = document.getElementById('ollamaBanner');

function setOllamaBanner(show) {
  if (!ollamaBannerEl) return;
  if (show) ollamaBannerEl.classList.remove('hidden');
  else ollamaBannerEl.classList.add('hidden');
}

function setStatus(msg, isErr = false) {
  statusEl.textContent = msg;
  statusEl.className = 'status' + (isErr ? ' err' : ' ok');
}

function escapeHtml(s) {
  if (s == null) return '';
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

function renderOutreach(data, fromHistory = false) {
  const outreach = data.outreach || {};
  const profile_preview = data.profile_preview || '';
  const raw_llm_output = data.raw_llm_output;
  let html = '';

  if (outreach.cold_email) {
    const ce = outreach.cold_email;
    html += `
      <div class="outreach-block">
        <h3>Cold email</h3>
        ${ce.subject ? `<div class="subject">Subject: ${escapeHtml(ce.subject)}</div>` : ''}
        <pre>${escapeHtml(typeof ce.body === 'string' ? ce.body : JSON.stringify(ce.body))}</pre>
      </div>`;
  }
  if (outreach.whatsapp) {
    html += `<div class="outreach-block"><h3>WhatsApp</h3><pre>${escapeHtml(outreach.whatsapp)}</pre></div>`;
  }
  if (outreach.linkedin_dm) {
    html += `<div class="outreach-block"><h3>LinkedIn DM</h3><pre>${escapeHtml(outreach.linkedin_dm)}</pre></div>`;
  }
  if (outreach.tone_used) {
    html += `<div class="outreach-block"><h3>Tone</h3><p>${escapeHtml(outreach.tone_used)}</p></div>`;
  }
  if (outreach.raw_response) {
    html += `<div class="outreach-block"><h3>Model output</h3><pre>${escapeHtml(outreach.raw_response)}</pre></div>`;
  }
  if (raw_llm_output && !outreach.cold_email && !outreach.whatsapp && !outreach.linkedin_dm) {
    html += `<div class="outreach-block"><h3>Raw output</h3><pre>${escapeHtml(raw_llm_output)}</pre></div>`;
  }
  html += `<div class="raw-box"><strong>Profile used</strong><br/><pre>${escapeHtml(profile_preview)}</pre></div>`;
  outreachEl.innerHTML = html;
}

function formatDate(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch (_) { return iso; }
}

function renderHistoryList(history, activeId) {
  if (!history || history.length === 0) {
    emptyHistoryEl.style.display = 'block';
    historyListEl.querySelectorAll('.history-item').forEach(el => el.remove());
    return;
  }
  emptyHistoryEl.style.display = 'none';
  const fragment = document.createDocumentFragment();
  history.forEach(entry => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'history-item' + (entry.id === activeId ? ' active' : '');
    btn.dataset.id = String(entry.id);
    btn.innerHTML = `<div class="date">${escapeHtml(formatDate(entry.created_at))}</div><div class="snippet">${escapeHtml(entry.profile_preview || 'Outreach')}</div>`;
    btn.addEventListener('click', () => loadHistoryEntry(entry.id));
    fragment.appendChild(btn);
  });
  historyListEl.querySelectorAll('.history-item').forEach(el => el.remove());
  historyListEl.insertBefore(fragment, emptyHistoryEl);
}

async function loadHistory() {
  try {
    const res = await fetch(API + '/history');
    const data = await res.json().catch(() => ({}));
    renderHistoryList(data.history || [], null);
  } catch (_) {}
}

async function loadHistoryEntry(id) {
  setStatus('Loading…');
  try {
    const res = await fetch(API + '/history/' + id);
    if (!res.ok) { setStatus('Failed to load chat.', true); return; }
    const data = await res.json();
    renderOutreach(data, true);
    setStatus('Loaded past outreach.');
    historyListEl.querySelectorAll('.history-item').forEach(el => {
      el.classList.toggle('active', parseInt(el.dataset.id, 10) === id);
    });
  } catch (e) {
    setStatus('Error: ' + e.message, true);
  }
}

async function generate() {
  const file = fileEl.files[0];
  const raw = rawEl.value.trim();

  if (!file && !raw) {
    setStatus('Upload a file or paste profile data.', true);
    return;
  }

  setStatus('Generating…');
  btnEl.disabled = true;
  outreachEl.innerHTML = '';

  try {
    const form = new FormData();
    if (file) form.append('file', file);
    if (raw && !file) form.append('raw_text', raw);
    form.append('model', 'phi3:mini');

    const res = await fetch(API + '/generate', { method: 'POST', body: form });
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const detail = data.detail;
      const isOllamaDown = detail && (detail.code === 'ollama_not_running' || (detail.steps && detail.message));
      if (isOllamaDown) {
        setOllamaBanner(true);
        setStatus(detail.message || 'Ollama is not running.', true);
        const steps = (detail.steps || []).map(s => escapeHtml(s)).join('</li><li>');
        outreachEl.innerHTML = '<div class="ollama-banner"><h3>Ollama is not running</h3><p>' + escapeHtml(detail.message || '') + '</p><ol><li>' + steps + '</li></ol></div>';
      } else {
        setStatus(typeof detail === 'string' ? detail : (detail && detail.message) || res.statusText || 'Request failed', true);
        if (detail && typeof detail === 'string') {
          outreachEl.innerHTML = '<div class="outreach-block"><p class="status err">' + escapeHtml(detail) + '</p></div>';
        }
      }
      return;
    }

    renderOutreach(data);
    setStatus('Done. Saved to history.');
    loadHistory();
    historyListEl.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
    const first = historyListEl.querySelector('.history-item');
    if (first) first.classList.add('active');
  } catch (e) {
    setStatus('Network error: ' + e.message, true);
  } finally {
    btnEl.disabled = false;
  }
}

btnEl.addEventListener('click', generate);
fileEl.addEventListener('change', () => { rawEl.value = ''; });
rawEl.addEventListener('input', () => { fileEl.value = ''; });

async function checkOllama() {
  try {
    const res = await fetch('/health');
    const data = await res.json().catch(() => ({}));
    setOllamaBanner(!data.ollama);
  } catch (_) {
    setOllamaBanner(true);
  }
}

checkOllama();
loadHistory();
