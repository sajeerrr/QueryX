/* upload.js — Handles PDF upload and integrates with file list */

const dropProgress = document.getElementById("dropProgress");
const progressBar  = document.getElementById("progressBar");
let uploadInProgress = false;
let activeUpload = null;
window.isDocumentProcessing = false;

// ── Show processing state in the chat area (right panel) ──
function showProcessingView(fileName) {
    const messages = document.getElementById("messages");
    if (!messages) return;
    messages.innerHTML = "";

    const row = document.createElement("div");
    row.className = "message ai processing-message";
    row.id = "processingMessage";
    row.innerHTML = `
        <div class="msg-avatar ai">Q</div>
        <div class="bubble processing-bubble">
            <div class="processing-header">
                <div class="processing-spinner"></div>
                <strong>File is processing…</strong>
            </div>
            <p class="processing-sub">Please wait while <span class="processing-file-name"></span> is prepared.</p>
            <div class="processing-bar-wrap">
                <div class="processing-bar" id="chatProgressBar"></div>
            </div>
            <button type="button" class="stop-processing-btn" id="stopProcessingBtn">Stop processing</button>
        </div>
    `;
    const stopBtn = row.querySelector("#stopProcessingBtn");
    row.querySelector(".processing-file-name").textContent = fileName || "your file";
    stopBtn?.addEventListener("click", () => {
        stopBtn.disabled = true;
        stopBtn.textContent = "Cancelling…";
        stopBtn.classList.add("is-cancelling");
        window.cancelCurrentUpload?.();
    });
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
    // Several parts of the UI can request the welcome view. Do not let one of
    // those requests erase an upload animation that is still in progress.
    if (window.isDocumentProcessing) return;

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

function showUploadFailureView(fileName, error) {
    const messages = document.getElementById("messages");
    if (!messages) return;
    messages.innerHTML = "";

    const row = document.createElement("div");
    row.className = "message ai";
    row.innerHTML = `
        <div class="msg-avatar ai">Q</div>
        <div class="bubble processing-bubble">
            <div class="processing-header"><strong>Upload could not start</strong></div>
            <p class="processing-sub"></p>
            <button type="button" class="starter-chip" id="retryUploadBtn">Choose a PDF and try again</button>
        </div>
    `;
    row.querySelector(".processing-sub").textContent = `${fileName}: ${error}`;
    row.querySelector("#retryUploadBtn").addEventListener("click", () => {
        document.getElementById("fileInput")?.click();
    });
    messages.appendChild(row);
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

window.cancelCurrentUpload = async function() {
    if (!activeUpload || activeUpload.cancelled) return;

    activeUpload.cancelled = true;
    const cancelBtn = document.getElementById("stopProcessingBtn");
    if (cancelBtn) {
        cancelBtn.disabled = true;
        cancelBtn.textContent = "Cancelling…";
        cancelBtn.classList.add("is-cancelling");
    }
    activeUpload.controller.abort();
    // Tell the server to stop even if it has already received the complete PDF.
    cancelDocumentUpload(activeUpload.uploadId).catch(error => {
        console.warn("[QueryX upload] could not send cancellation request", error);
    });
};

function showUploadCancelledView(fileName) {
    const messages = document.getElementById("messages");
    if (!messages) return;
    messages.innerHTML = `
        <div class="welcome-card">
            <div class="welcome-icon-wrap">✓</div>
            <h3 class="welcome-title">Processing stopped</h3>
            <p class="welcome-sub">${fileName} was not added. You can choose another PDF whenever you’re ready.</p>
        </div>`;
}

/**
 * Main upload function: immediately adds optimistic item to left sidebar,
 * activates animations, and smoothly transitions on completion.
 */
window.startUpload = async function(file) {
    // A file can be received through several UI paths (drop zone, window drop,
    // file picker). Keep one upload lifecycle in control of the processing UI.
    if (uploadInProgress) return;

    if (!file) {
        showToast("Please select a PDF document first.", "error");
        return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf") {
        showToast("Only PDF files are supported.", "error");
        return;
    }

    uploadInProgress = true;
    const controller = new AbortController();
    const uploadId = crypto.randomUUID();
    activeUpload = { controller, uploadId, cancelled: false };
    console.info("[QueryX upload] UI processing started", { name: file.name, bytes: file.size });
    // Prevent the initial /documents request from restoring the upload screen
    // while this upload owns the visible state.
    window.isDocumentProcessing = true;

    const uploadBtn     = document.getElementById("uploadBtn");
    const uploadBtnText = document.getElementById("uploadBtnText");
    if (uploadBtn) uploadBtn.disabled = true;
    if (uploadBtnText) uploadBtnText.textContent = "Uploading…";
    if (dropProgress) dropProgress.classList.add("visible");
    const newChatBtn = document.getElementById("navNewChat");
    if (newChatBtn) newChatBtn.disabled = true;

    // Enter the processing view before changing any other UI state. This makes
    // the transition immediate, even while the browser is still sending a PDF.
    showView("Chat");
    showProcessingView(file.name);

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

    // Keep the UI animated while the normal upload endpoint performs the
    // complete extraction → chunking → embedding → indexing workflow. Unlike
    // a streamed response, this request cannot lose its final event midway.
    let visualProgress = 8;
    const processingTicker = setInterval(() => {
        visualProgress = Math.min(visualProgress + (visualProgress < 70 ? 6 : 1.5), 90);
        if (progressBar) progressBar.style.width = visualProgress + "%";
        const chatBar = document.getElementById("chatProgressBar");
        if (chatBar) chatBar.style.width = visualProgress + "%";

        if (typeof _fileCardMap !== "undefined") {
            const card = _fileCardMap.get(tempId);
            const meta = card?.querySelector(".file-bubble-meta");
            if (meta) meta.textContent = visualProgress < 70 ? "Processing…" : "Indexing…";
        }
    }, 450);

    try {
        const result = await uploadDocument(file, { signal: controller.signal, uploadId });
        clearInterval(processingTicker);

        // Ensure 100%
        if (progressBar) progressBar.style.width = "100%";
        const chatBar = document.getElementById("chatProgressBar");
        if (chatBar) chatBar.style.width = "100%";

        setTimeout(() => {
            if (dropProgress) dropProgress.classList.remove("visible");
            if (progressBar) progressBar.style.width = "0%";

            showToast(`✓ ${result.filename} — ${result.indexed_chunks} chunks indexed`, "success");

            // ── 3. Update placeholder in LEFT sidebar: stop animations, show check/icon ──
            const idx = uploadedFiles.findIndex(f => f.id === tempId);
            if (idx !== -1) {
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
            setTimeout(() => {
                window.isDocumentProcessing = false;
                showWelcomeView();
            }, 350);
        }, 300);

    } catch (err) {
        clearInterval(processingTicker);
        console.error("[QueryX upload] failed", err);
        if (dropProgress) dropProgress.classList.remove("visible");
        if (progressBar) progressBar.style.width = "0%";

        const wasCancelled = activeUpload?.uploadId === uploadId && activeUpload.cancelled;
        if (wasCancelled || err.name === "AbortError") {
            uploadedFiles = uploadedFiles.filter(f => f.id !== tempId);
            renderFileList();
            window.isDocumentProcessing = false;
            showUploadCancelledView(file.name);
            showToast("Processing stopped", "info");
            return;
        }

        // Auto-recovery: Check if the server actually finished processing despite connection reset
        try {
            await new Promise(r => setTimeout(r, 600));
            const serverDocs = await getDocuments();
            if (serverDocs && Array.isArray(serverDocs)) {
                const found = serverDocs.find(d => d.filename === file.name);
                if (found) {
                    const idx = uploadedFiles.findIndex(f => f.id === tempId);
                    if (idx !== -1) {
                        if (typeof _fileCardMap !== 'undefined') {
                            const card = _fileCardMap.get(tempId);
                            if (card) {
                                _fileCardMap.delete(tempId);
                                _fileCardMap.set(found.document_id, card);
                            }
                        }
                        uploadedFiles[idx] = {
                            id: found.document_id,
                            name: found.filename,
                            chunks: found.chunks || 1,
                            uploading: false,
                            active: true
                        };
                    }
                    renderFileList();
                    window.isDocumentProcessing = false;
                    showWelcomeView();
                    showToast(`✓ ${found.filename} indexed`, "success");
                    return;
                }
            }
        } catch (recoveryErr) {
            // Ignore recovery check error
        }

        // Remove optimistic placeholder on genuine failure
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
            showView("Chat");
        }
        window.isDocumentProcessing = false;
        showUploadFailureView(file.name, err.message || "Unknown upload error");
        showToast(err.message || "Upload failed. Please check backend server.", "error");
    } finally {
        clearInterval(processingTicker);
        uploadInProgress = false;
        if (uploadBtn) uploadBtn.disabled = false;
        if (uploadBtnText) uploadBtnText.textContent = "Select a PDF first";
        const newChatBtn = document.getElementById("navNewChat");
        if (newChatBtn) newChatBtn.disabled = false;
        if (activeUpload?.uploadId === uploadId) activeUpload = null;
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

// Keep the file-picker lifecycle beside the upload logic. The page's initial
// document loader cannot decide what view to show after this handler starts.
const uploadFileInput = document.getElementById("fileInput");
if (uploadFileInput) {
    uploadFileInput.onchange = () => {
        const file = uploadFileInput.files && uploadFileInput.files[0];
        if (file) startUpload(file);
        uploadFileInput.value = "";
    };
}
