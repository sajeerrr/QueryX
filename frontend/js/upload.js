/* upload.js — Handles PDF upload and integrates with file list */

const dropProgress = document.getElementById("dropProgress");
const progressBar  = document.getElementById("progressBar");

// ── Show processing state in the chat area (right panel) ──
function showProcessingView(fileName) {
    const messages = document.getElementById("messages");
    if (!messages) return;
    messages.innerHTML = "";

    const row = document.createElement("div");
    row.className = "message ai";
    row.id = "processingMessage";
    row.innerHTML = `
        <div class="msg-avatar ai">Q</div>
        <div class="bubble processing-bubble">
            <div class="processing-header">
                <div class="processing-spinner"></div>
                <strong>Indexing Document</strong>
            </div>
            <p class="processing-sub">Extracting text, chunking, and building vector embeddings${fileName ? ' for <em>' + fileName + '</em>' : ''}…</p>
            <div class="processing-bar-wrap">
                <div class="processing-bar" id="chatProgressBar"></div>
            </div>
        </div>
    `;
    messages.appendChild(row);

    // Disable chat input while processing
    const questionInput = document.getElementById("question");
    const sendBtn = document.getElementById("sendBtn");
    if (questionInput) {
        questionInput.disabled = true;
        questionInput.placeholder = "Waiting for document to finish processing…";
    }
    if (sendBtn) sendBtn.disabled = true;
}

// ── Show Welcome / Ready View with starter prompt chips ──
function showWelcomeView() {
    const messages = document.getElementById("messages");
    if (!messages) return;
    messages.innerHTML = "";

    const welcome = document.createElement("div");
    welcome.className = "welcome-card";
    welcome.id = "welcomeCard";
    welcome.innerHTML = `
        <div class="welcome-icon-wrap">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <h3 class="welcome-title">Document Ready</h3>
        <p class="welcome-sub">Ask any question about your document, or choose a quick starter below:</p>
        <div class="starter-chips">
            <button class="starter-chip" onclick="askStarterQuestion('Summarize key points in this document')">✨ Summarize key points</button>
            <button class="starter-chip" onclick="askStarterQuestion('What are the main topics covered?')">💡 Main topics</button>
            <button class="starter-chip" onclick="askStarterQuestion('Extract important key takeaways')">📌 Key takeaways</button>
        </div>
    `;
    messages.appendChild(welcome);

    // Re-enable chat input
    const questionInput = document.getElementById("question");
    const sendBtn = document.getElementById("sendBtn");
    if (questionInput) {
        questionInput.disabled = false;
        questionInput.placeholder = "Ask anything about your document…";
        questionInput.focus();
    }
    if (sendBtn) sendBtn.disabled = false;
}

// Helper to fill input and trigger send on starter chip click
window.askStarterQuestion = function(text) {
    const questionInput = document.getElementById("question");
    if (questionInput) {
        questionInput.value = text;
        if (typeof sendQuestion === 'function') sendQuestion();
    }
};

window.showProcessingView = showProcessingView;
window.showWelcomeView = showWelcomeView;

/**
 * Main upload function: immediately adds optimistic item to left sidebar,
 * activates animations, and smoothly transitions on completion.
 */
window.startUpload = async function(file) {
    if (!file) {
        showToast("Please select a PDF document first.", "error");
        return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf") {
        showToast("Only PDF files are supported.", "error");
        return;
    }

    const uploadBtn     = document.getElementById("uploadBtn");
    const uploadBtnText = document.getElementById("uploadBtnText");
    if (uploadBtn) uploadBtn.disabled = true;
    if (uploadBtnText) uploadBtnText.textContent = "Uploading…";
    if (dropProgress) dropProgress.classList.add("visible");

    // ── 1. Optimistic: add card to LEFT sidebar with processing spinner & shimmer ──
    const tempId = '__uploading_' + Date.now();
    uploadedFiles.forEach(f => f.active = false);
    uploadedFiles.unshift({
        id: tempId,
        name: file.name,
        chunks: '…',
        uploading: true,
        active: true
    });
    renderFileList();

    // ── 2. Immediately switch to Chat view and show processing on the RIGHT panel ──
    showView("Chat");
    showProcessingView(file.name);

    let pct = 10;
    const ticker = setInterval(() => {
        pct = Math.min(pct + Math.random() * 12 + 4, 88);
        if (progressBar) progressBar.style.width = pct + "%";
        const chatBar = document.getElementById("chatProgressBar");
        if (chatBar) chatBar.style.width = pct + "%";
    }, 200);

    try {
        const result = await uploadDocument(file);
        clearInterval(ticker);

        if (progressBar) progressBar.style.width = "100%";
        const chatBar = document.getElementById("chatProgressBar");
        if (chatBar) chatBar.style.width = "100%";

        setTimeout(() => {
            if (dropProgress) dropProgress.classList.remove("visible");
            if (progressBar) progressBar.style.width = "0%";
        }, 500);

        showToast(`✓ ${result.filename} — ${result.indexed_chunks} chunks indexed`, "success");

        // ── 3. Update placeholder in LEFT sidebar: stop animations, show check/icon ──
        const idx = uploadedFiles.findIndex(f => f.id === tempId);
        if (idx !== -1) {
            // Update _fileCardMap key if card was already cached
            if (typeof _fileCardMap !== 'undefined') {
                const card = _fileCardMap.get(tempId);
                if (card) {
                    _fileCardMap.delete(tempId);
                    _fileCardMap.set(result.document_id, card);
                }
            }

            uploadedFiles[idx] = {
                id: result.document_id,
                name: result.filename,
                chunks: result.indexed_chunks,
                uploading: false,
                active: true
            };
        }
        renderFileList();

        // ── 4. Transition chat area from processing → ready welcome view ──
        setTimeout(() => showWelcomeView(), 300);

    } catch (err) {
        clearInterval(ticker);
        if (dropProgress) dropProgress.classList.remove("visible");
        if (progressBar) progressBar.style.width = "0%";

        // Remove optimistic placeholder on error
        uploadedFiles = uploadedFiles.filter(f => f.id !== tempId);
        renderFileList();

        const questionInput = document.getElementById("question");
        const sendBtn = document.getElementById("sendBtn");
        if (questionInput) {
            questionInput.disabled = false;
            questionInput.placeholder = "Ask anything about your document…";
        }
        if (sendBtn) sendBtn.disabled = false;

        if (uploadedFiles.length === 0) {
            showView("Upload");
        }
        showToast(err.message || "Upload failed. Please check backend server.", "error");
    } finally {
        if (uploadBtn) uploadBtn.disabled = false;
        if (uploadBtnText) uploadBtnText.textContent = "Select a PDF first";
    }
};

// Wire up #uploadBtn button click
const uploadBtnEl = document.getElementById("uploadBtn");
if (uploadBtnEl) {
    uploadBtnEl.addEventListener("click", () => {
        const fileInput = document.getElementById("fileInput");
        if (fileInput && fileInput.files && fileInput.files[0]) {
            startUpload(fileInput.files[0]);
        }
    });
}
