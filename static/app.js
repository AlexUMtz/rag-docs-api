const API = '';
let selectedDocumentId = null;
let documents = [];

const docList = document.getElementById('doc-list');
const docEmpty = document.getElementById('doc-empty');
const chatArea = document.getElementById('chat-area');
const questionInput = document.getElementById('question-input');
const sendBtn = document.getElementById('send-btn');
const fileInput = document.getElementById('file-input');
const docBadge = document.getElementById('doc-badge');
const uploadBtn = document.querySelector('.upload-btn');

// Cargar documentos
async function loadDocuments() {
  try {
    const res = await fetch(`${API}/api/documents/`);
    const data = await res.json();
    documents = data.documents;
    docBadge.textContent = 'Todos los documentos';
    docBadge.style.display = 'inline-block';
    renderDocuments();
  } catch (e) {
    console.error('Error cargando documentos:', e);
  }
}

function renderDocuments() {
  const allItem = `
    <article class="doc-item ${!selectedDocumentId ? 'active' : ''}" id="doc-all">
      <div class="doc-icon">
        <svg viewBox="0 0 16 16" fill="none">
          <path d="M2 4h12M2 8h12M2 12h12" stroke="#6b7280" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="doc-info">
        <p class="doc-name">Todos los documentos</p>
        <small class="doc-meta">${documents.length} documentos</small>
      </div>
    </article>
  `;

  const items = documents.map((doc) => createDocItem(doc)).join('');
  docList.innerHTML =
    allItem +
    (documents.length === 0
      ? '<p class="doc-empty">Sube un PDF para comenzar.</p>'
      : items);

  document
    .getElementById('doc-all')
    .addEventListener('click', () => deselectDocument());

  docList.querySelectorAll('.doc-item[data-id]').forEach((item) => {
    item.addEventListener('click', () => selectDocument(item.dataset.id));
    item.querySelector('.doc-delete').addEventListener('click', (e) => {
      e.stopPropagation();
      deleteDocument(item.dataset.id);
    });
  });
}

if (selectedDocumentId) {
  const active = docList.querySelector('[data-id="${selectedDocumentId}"]');
  if (active) active.classList.add('active');
}

function createDocItem(doc) {
  const isActive = selectedDocumentId === doc.document_id ? 'active' : '';
  return `
    <article class="doc-item ${isActive}" data-id="${doc.document_id}">
      <div class="doc-icon">
        <svg viewBox="0 0 16 16"><path d="M4 0h6l4 4v10a2 2 0 01-2 2H4a2 2 0 01-2-2V2a2 2 0 012-2z"/></svg>
      </div>
      <div class="doc-info">
        <p class="doc-name">${escapeHtml(doc.filename)}</p>
        <small class="doc-meta">${doc.chunk_count ? doc.chunk_count + ' chunks' : ''}</small>
      </div>
      <button class="doc-delete" title="Eliminar documento" aria-label="Eliminar ${escapeHtml(doc.filename)}">
        <svg viewBox="0 0 12 12" fill="none">
          <path d="M2 2l8 8M10 2l-8 8" stroke="#6b7280" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
    </article>
  `;
}

// Seleccionar documento
function selectDocument(id) {
  selectedDocumentId = id;
  const doc = documents.find((d) => d.document_id === id);
  if (doc) {
    docBadge.textContent = doc.filename;
    docBadge.style.display = 'inline-block';
  }
  renderDocuments();
}

function deselectDocument() {
  selectedDocumentId = null;
  docBadge.textContent = 'Todos los documentos';
  docBadge.style.display = 'inline-block';
  renderDocuments();
}

// Upload
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  uploadBtn.classList.add('loading');
  uploadBtn.querySelector('span') &&
    (uploadBtn.querySelector('span').textContent = 'Subiendo ...');

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch(`${API}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      alert(err.detail || 'Error al subir el documento');
      return;
    }

    const data = await res.json();
    await loadDocuments();
    selectDocument(data.document_id);
  } catch (e) {
    alert('Error de conexión al subir el documento');
  } finally {
    uploadBtn.classList.remove('loading');
    fileInput.value = '';
  }
});

// Eliminar documento
async function deleteDocument(id) {
  if (!confirm('¿Estás seguro de eliminar este documento?')) return;

  try {
    const res = await fetch(`${API}/api/documents/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) return;

    if (selectDocumentId === id) {
      selectDocumentId = null;
      docBadge.style.display = 'none';
    }
    await loadDocuments();
  } catch (e) {
    alert('Error de conexión al eliminar el documento');
  }
}

// Chat
function appendMessage(role, content, sources = []) {
  const article = document.createElement('article');
  article.className = role === 'user' ? 'msg-user' : 'msg-ai';

  let sourcesHtml = '';
  if (sources.length > 0) {
    const cards = sources
      .map(
        (s) => `
      <div class="source-card">
        <p class="source-text">${escapeHtml(s.content)}</p>
        <small class="source-file">${escapeHtml(s.filename)}${s.page !== null ? ' — pág. ' + (s.page + 1) : ''}</small>
      </div>
    `,
      )
      .join('');
    sourcesHtml = `
      <aside class="sources">
        <p class="source-label">Fuentes</p>
        ${cards}
      </aside>
    `;
  }

  article.innerHTML = `<div class="bubble">${escapeHtml(content)}</div>${sourcesHtml}`;
  chatArea.appendChild(article);
  chatArea.scrollTop = chatArea.scrollHeight;
}

function appendThinking() {
  const div = document.createElement('div');
  div.className = 'msg-ai';
  div.innerHTML = `
    <div class="thinking">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </div>
  `;
  chatArea.appendChild(div);
  chatArea.scrollTop = chatArea.scrollHeight;
  return div;
}

async function sendQuestion() {
  const question = questionInput.value.trim();
  if (!question) return;

  questionInput.value = '';
  sendBtn.disabled = true;

  appendMessage('user', question);
  const thinking = appendThinking();

  try {
    const body = { question };
    if (selectedDocumentId) body.document_id = selectedDocumentId;

    const res = await fetch(`${API}/api/qa/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    thinking.remove();

    const data = await res.json();
    appendMessage('ai', data.answer, data.sources);
  } catch (e) {
    thinking.remove();
    appendMessage(
      'ai',
      'Error de conexión. Verifica que el servidor esté corriendo.',
    );
  } finally {
    sendBtn.disable = false;
  }
}

// ── Enter para enviar ──────────────────────────────────────────
questionInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendQuestion();
  }
});

questionInput.addEventListener('input', () => {
  questionInput.style.height = 'auto';
  questionInput.style.height = Math.min(questionInput.scrollHeight, 120) + 'px';
});

sendBtn.addEventListener('click', sendQuestion);

// ── Utilidades ─────────────────────────────────────────────────
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ── Init ───────────────────────────────────────────────────────
loadDocuments();
