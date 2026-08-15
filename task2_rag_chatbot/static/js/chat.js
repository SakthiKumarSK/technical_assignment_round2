/* Task 2 Local LLM RAG Chatbot Client */
document.addEventListener('DOMContentLoaded', () => {
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  const modelSelect = document.getElementById('model-select');
  const docDropzone = document.getElementById('doc-dropzone');
  const fileInput = document.getElementById('file-input');
  const docListContainer = document.getElementById('doc-list-container');
  const docCountDisplay = document.getElementById('doc-count');
  const statsVectorsDisplay = document.getElementById('stats-total-vectors');
  const uploadStatusText = document.getElementById('upload-status-text');
  const systemStatusBadge = document.getElementById('system-status-badge');
  const systemStatusText = document.getElementById('system-status-text');
  const clearAllDocsBtn = document.getElementById('clear-all-docs-btn');
  const resetChatBtn = document.getElementById('reset-chat-btn');
  const suggestionChips = document.querySelectorAll('.suggestion-chip');

  let conversationHistory = [];

  // Initial load
  fetchHealthAndModels();
  refreshDocumentList();

  // Auto-resize chat textarea
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
  });

  // Suggestion chips
  suggestionChips.forEach(chip => {
    chip.addEventListener('click', () => {
      chatInput.value = chip.getAttribute('data-query');
      chatInput.focus();
    });
  });

  // Reset Chat
  if (resetChatBtn) {
    resetChatBtn.addEventListener('click', () => {
      conversationHistory = [];
      chatMessages.innerHTML = `
        <div class="message-row assistant">
          <div class="avatar assistant">&#9881;</div>
          <div class="message-bubble">
            <div class="message-text">Chat cleared. Ready for your questions!</div>
          </div>
        </div>
      `;
    });
  }

  // Clear All Documents
  if (clearAllDocsBtn) {
    clearAllDocsBtn.addEventListener('click', async () => {
      if (confirm("Are you sure you want to clear all documents from the vector database?")) {
        try {
          await fetch('/api/documents', { method: 'DELETE' });
          refreshDocumentList();
        } catch (err) {
          console.error("Error clearing documents:", err);
        }
      }
    });
  }

  // Document Upload handling
  if (docDropzone && fileInput) {
    docDropzone.addEventListener('click', () => fileInput.click());

    docDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      docDropzone.style.borderColor = '#2563eb';
    });

    docDropzone.addEventListener('dragleave', () => {
      docDropzone.style.borderColor = '#334155';
    });

    docDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      docDropzone.style.borderColor = '#334155';
      if (e.dataTransfer.files.length > 0) {
        handleFileUpload(e.dataTransfer.files);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        handleFileUpload(fileInput.files);
      }
    });
  }

  async function handleFileUpload(files) {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    uploadStatusText.style.display = 'block';
    uploadStatusText.textContent = `Uploading & chunking ${files.length} document(s)...`;

    try {
      const resp = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData
      });

      if (!resp.ok) {
        throw new Error(await resp.text());
      }

      const data = await resp.json();
      uploadStatusText.textContent = `Indexed ${data.total_new_chunks} chunks into FAISS!`;
      setTimeout(() => { uploadStatusText.style.display = 'none'; }, 4000);
      refreshDocumentList();
    } catch (err) {
      uploadStatusText.textContent = `Upload failed: ${err.message}`;
      uploadStatusText.style.color = '#ef4444';
      console.error(err);
    }
  }

  async function refreshDocumentList() {
    try {
      const resp = await fetch('/api/documents');
      if (resp.ok) {
        const docs = await resp.json();
        docCountDisplay.textContent = docs.length;

        if (docs.length === 0) {
          docListContainer.innerHTML = `<div style="color: #64748b; font-size: 0.775rem; text-align: center; padding: 1rem 0;">No documents ingested yet.</div>`;
          statsVectorsDisplay.textContent = "0";
          return;
        }

        let totalVectors = 0;
        docListContainer.innerHTML = docs.map(d => {
          totalVectors += d.total_chunks;
          return `
            <div class="doc-item">
              <div style="overflow: hidden;">
                <div class="doc-name" title="${d.file_name}">${d.file_name}</div>
                <div class="doc-meta">${d.total_chunks} chunks &bull; ${Math.round(d.file_size_bytes / 1024)} KB</div>
              </div>
              <button class="doc-delete-btn" onclick="window.deleteDoc('${d.doc_id}')" title="Delete document">&times;</button>
            </div>
          `;
        }).join('');

        statsVectorsDisplay.textContent = totalVectors;
      }
    } catch (err) {
      console.error("Failed to load documents:", err);
    }
  }

  window.deleteDoc = async (docId) => {
    try {
      await fetch(`/api/documents/${docId}`, { method: 'DELETE' });
      refreshDocumentList();
    } catch (err) {
      console.error("Failed to delete document:", err);
    }
  };

  async function fetchHealthAndModels() {
    try {
      const resp = await fetch('/api/health');
      if (resp.ok) {
        const health = await resp.json();
        if (health.ollama_connected) {
          systemStatusBadge.style.backgroundColor = '#ecfdf5';
          systemStatusBadge.style.color = '#059669';
          systemStatusText.textContent = `Ollama Online (${health.available_models.length} Models)`;
        } else {
          systemStatusBadge.style.backgroundColor = '#eff6ff';
          systemStatusBadge.style.color = '#1d4ed8';
          systemStatusText.textContent = 'Local Engine Ready';
        }

        if (health.available_models && health.available_models.length > 0) {
          modelSelect.innerHTML = health.available_models.map(m =>
            `<option value="${m}">${m}</option>`
          ).join('');
        }
      }
    } catch (err) {
      console.warn("Health check error:", err);
    }
  }

  // Chat Submission
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const question = chatInput.value.trim();
    if (!question) return;

    // Append User Message
    appendMessage('user', question);
    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;

    // Create Assistant Placeholder
    const assistantRow = document.createElement('div');
    assistantRow.className = 'message-row assistant';
    assistantRow.innerHTML = `
      <div class="avatar assistant">&#9881;</div>
      <div class="message-bubble">
        <div class="message-text" id="current-response-text" style="color: #64748b;">Retrieving relevant document chunks and generating grounded answer...</div>
        <div class="citations-wrapper" id="current-citations" style="display: none;"></div>
      </div>
    `;
    chatMessages.appendChild(assistantRow);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    const responseTextEl = assistantRow.querySelector('#current-response-text');
    const citationsEl = assistantRow.querySelector('#current-citations');

    try {
      const selectedModel = modelSelect.value || 'llama3.2';
      const payload = {
        question: question,
        model: selectedModel,
        top_k: 4,
        history: conversationHistory
      };

      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!resp.ok) {
        throw new Error(await resp.text());
      }

      const data = await resp.json();
      responseTextEl.style.color = 'var(--text-main)';
      responseTextEl.innerHTML = formatMarkdown(data.answer);

      // Render Citations
      if (data.citations && data.citations.length > 0) {
        renderCitations(citationsEl, data.citations);
      }

      // Update history
      conversationHistory.push({ role: 'user', content: question });
      conversationHistory.push({ role: 'assistant', content: data.answer });

    } catch (err) {
      responseTextEl.style.color = '#ef4444';
      responseTextEl.textContent = `Error: ${err.message}`;
    } finally {
      sendBtn.disabled = false;
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  });

  function appendMessage(role, text) {
    const row = document.createElement('div');
    row.className = `message-row ${role}`;
    row.innerHTML = `
      <div class="avatar ${role}">${role === 'user' ? 'U' : '&#9881;'}</div>
      <div class="message-bubble">
        <div class="message-text">${formatMarkdown(text)}</div>
      </div>
    `;
    chatMessages.appendChild(row);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function renderCitations(container, citations) {
    container.style.display = 'block';
    container.innerHTML = `
      <div class="citations-header">
        <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z"/></svg>
        <span>Grounded Source Citations (${citations.length})</span>
      </div>
      <div class="citation-chips">
        ${citations.map((c, i) => `
          <div class="citation-chip" data-idx="${i}" onclick="window.toggleCitationSnippet(this)">
            <strong>${c.document_name}</strong>
            <span>(Chunk #${c.chunk_index}, ${c.similarity_percentage}%)</span>
          </div>
        `).join('')}
      </div>
      ${citations.map((c, i) => `
        <div class="citation-snippet-modal" id="citation-snippet-${i}">
          <div style="font-weight: 700; margin-bottom: 0.3rem; color: #1e40af;">
            Source: ${c.document_name} &bull; Page ${c.page_number} &bull; Match: ${c.similarity_percentage}%
          </div>
          <div>${c.snippet}</div>
        </div>
      `).join('')}
    `;
  }

  window.toggleCitationSnippet = (chipEl) => {
    const idx = chipEl.getAttribute('data-idx');
    const modal = chipEl.closest('.citations-wrapper').querySelector(`#citation-snippet-${idx}`);
    if (modal) {
      const isVisible = modal.style.display === 'block';
      modal.style.display = isVisible ? 'none' : 'block';
    }
  };

  function formatMarkdown(text) {
    if (!text) return '';
    let formatted = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code style="background:#f1f5f9;padding:0.15rem 0.35rem;border-radius:4px;font-family:monospace;font-size:0.85em;">$1</code>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n- /g, '<br>&bull; ')
      .replace(/\n/g, '<br>');
    return formatted;
  }
});
