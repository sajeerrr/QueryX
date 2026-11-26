/* ═══════════════════════════════════════════════════
   QueryX — Core App State & UI Logic
═══════════════════════════════════════════════════ */

let uploadedFiles = [];
let _fileCardMap = new Map();

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function isPdfFile(file) {
    return Boolean(
        file &&
        (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf"))
    );
}

// ── View switcher ──
window.showView = function(name) {
    // An active upload owns the right panel until its backend request completes.
    if (window.isDocumentProcessing && name !== "Chat") return;
    document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
    const el = document.getElementById("view" + name);
    if (el) el.classList.add("active");
};

// ── File list rendering (in-place updates to prevent flicker) ──
function renderFileList() {
    const list = document.getElementById("fileList");
    const empty = document.getElementById("panelEmpty");
    if (!list || !empty) return;

    if (uploadedFiles.length === 0) {
        list.innerHTML = "";
        _fileCardMap.clear();
        empty.style.display = "flex";
        const chatView = document.getElementById("viewChat");
        if (!chatView || !chatView.classList.contains("active")) {
            showView("Upload");
        }
        return;
    }

    empty.style.display = "none";

    // Remove deleted cards
    const currentIds = new Set(uploadedFiles.map(f => f.id));
    for (const [id, card] of _fileCardMap) {
        if (!currentIds.has(id)) {
            card.remove();
            _fileCardMap.delete(id);
        }
    }

    const docIconSvg = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    `;
    const spinnerHtml = `<div class="processing-spinner" style="width:18px;height:18px;border-width:2.5px;"></div>`;

    uploadedFiles.forEach((file, i) => {
        let bubble = _fileCardMap.get(file.id);

        if (bubble) {
            bubble.dataset.id = file.id;
            const meta = bubble.querySelector(".file-bubble-meta");
            if (meta) meta.textContent = file.uploading ? "Processing…" : `${file.chunks} chunks · PDF`;

            const iconWrap = bubble.querySelector(".file-bubble-icon");
            if (iconWrap) {
                iconWrap.innerHTML = file.uploading ? spinnerHtml : docIconSvg;
            }

            if (file.uploading) {
                bubble.classList.add("uploading");
            } else if (bubble.classList.contains("uploading")) {
                bubble.classList.remove("uploading");
                bubble.style.animation = "fileBubbleSuccess .35s var(--spring)";
            }

            bubble.classList.toggle("active", Boolean(file.active));
            return;
        }

        const safeName = escapeHtml(file.name);
        bubble = document.createElement("div");
        bubble.dataset.id = file.id;
        bubble.className = "file-bubble" + (file.uploading ? " uploading" : "") + (file.active ? " active" : "");
        bubble.style.setProperty("--i", i);
        bubble.innerHTML = `
            <div class="file-bubble-icon">
                ${file.uploading ? spinnerHtml : docIconSvg}
            </div>
            <div class="file-bubble-info">
                <span class="file-bubble-name" title="${safeName}">${safeName}</span>
                <span class="file-bubble-meta">${file.uploading ? "Processing…" : escapeHtml(file.chunks) + " chunks · PDF"}</span>
            </div>
            <button class="file-bubble-delete" data-index="${i}" title="Remove document">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </button>
        `;

        // Click bubble → activate and show chat
        bubble.addEventListener("click", (e) => {
            if (e.target.closest(".file-bubble-delete")) return;
            if (file.uploading) return;
            uploadedFiles.forEach(f => f.active = false);
            file.active = true;
            renderFileList();
            showView("Chat");
            if (typeof showWelcomeView === "function") {
                showWelcomeView();
            }
        });

        // Delete button
        const delBtn = bubble.querySelector(".file-bubble-delete");
        delBtn.addEventListener("click", async (e) => {
            e.stopPropagation();
            const fileId = bubble.dataset.id || file.id;
            const currentDoc = uploadedFiles.find(f => f.id === fileId) || file;
            const wasActive = currentDoc.active;
            const fileName = currentDoc.name;

            bubble.style.animation = "none";
            bubble.style.transition = "opacity .2s var(--ease), transform .2s var(--ease)";
            bubble.style.opacity = "0";
            bubble.style.transform = "translateX(-12px) scale(.95)";

            try {
                await deleteDocument(fileId);
            } catch (err) {
                console.error("Delete API error:", err);
                showToast("Failed to delete from server.", "error");
            }

            setTimeout(() => {
                if (bubble.parentNode) bubble.remove();
                _fileCardMap.delete(fileId);
                uploadedFiles = uploadedFiles.filter(f => f.id !== fileId);
                showToast(`"${fileName}" deleted`, "info");

                if (uploadedFiles.length === 0) {
                    const messages = document.getElementById("messages");
                    if (messages) messages.innerHTML = "";
                    _fileCardMap.clear();
                    empty.style.display = "flex";
                    showView("Upload");
                } else if (wasActive) {
                    uploadedFiles[0].active = true;
                    renderFileList();
                    if (typeof showWelcomeView === "function") {
                        showWelcomeView();
                    }
                } else {
                    renderFileList();
                }
            }, 220);
        });

        if (list.children[i]) {
            list.insertBefore(bubble, list.children[i]);
        } else {
            list.appendChild(bubble);
        }
        _fileCardMap.set(file.id, bubble);
    });
}

// ── Toast ──
window.showToast = function(msg, type = "info") {
    const t = document.getElementById("toast");
    if (!t) return;
    t.textContent = msg;
    t.className = `toast toast-${type} show`;
    setTimeout(() => { t.className = "toast"; }, 3200);
};

// ── Drop zone and file selection interactions ──
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const uploadBtnText = document.getElementById("uploadBtnText");

function setFile(file) {
    if (!uploadBtn || !dropZone) return;
    uploadBtn.disabled = false;
    if (uploadBtnText) uploadBtnText.textContent = `Upload "${file.name}"`;
    const dropText = dropZone.querySelector(".drop-text");
    if (dropText) {
        dropText.innerHTML = `📄 <strong>${escapeHtml(file.name)}</strong> (${(file.size / 1024).toFixed(0)} KB · Ready to upload)`;
    }
}

if (dropZone) {
    ["dragover", "dragenter"].forEach(evt => {
        dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.add("dragover"); });
    });
    ["dragleave", "dragend", "drop"].forEach(evt => {
        dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.remove("dragover"); });
    });
    dropZone.addEventListener("drop", e => {
        const file = e.dataTransfer?.files?.[0];
        // Prevent bubbling to the global drop listener so the upload only starts once.
        e.stopPropagation();
        if (isPdfFile(file)) {
            if (typeof startUpload === "function") {
                startUpload(file);
            } else {
                setFile(file);
            }
        } else if (file) {
            showToast("Please upload a valid PDF document.", "error");
        }
    });

    dropZone.addEventListener("click", (e) => {
        if (e.target.tagName !== "LABEL" && fileInput) {
            fileInput.click();
        }
    });
}

window.addEventListener("dragover", e => { e.preventDefault(); });
window.addEventListener("drop", e => {
    e.preventDefault();
    const file = e.dataTransfer?.files?.[0];
    if (isPdfFile(file) && typeof startUpload === "function") {
        startUpload(file);
    }
});

// ── Nav & Action Buttons ──
const navNewChat = document.getElementById("navNewChat");
if (navNewChat) {
    navNewChat.addEventListener("click", () => {
        if (typeof newSession === "function") newSession();
        const messages = document.getElementById("messages");
        if (messages) messages.innerHTML = "";
        showView("Chat");
        if (uploadedFiles.length > 0) {
            const activeDoc = uploadedFiles.find(f => f.active) || uploadedFiles[0];
            uploadedFiles.forEach(f => { f.active = (f.id === activeDoc.id); });
            renderFileList();
            if (typeof showWelcomeView === "function") {
                showWelcomeView();
            }
        }
    });
}

const uploadTriggerBtn = document.getElementById("uploadTriggerBtn");
if (uploadTriggerBtn) {
    uploadTriggerBtn.addEventListener("click", () => {
        if (fileInput) fileInput.click();
    });
}

const attachBtn = document.getElementById("attachBtn");
if (attachBtn) {
    attachBtn.addEventListener("click", () => {
        if (fileInput) fileInput.click();
    });
}

// ── Initial render ──
renderFileList();
