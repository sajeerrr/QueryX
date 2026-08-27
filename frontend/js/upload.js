/* upload.js — Handles PDF upload and integrates with file list */

const dropProgress = document.getElementById("dropProgress");
const progressBar  = document.getElementById("progressBar");

document.getElementById("uploadBtn").addEventListener("click", async () => {
    const fileInput    = document.getElementById("fileInput");
    const uploadBtn    = document.getElementById("uploadBtn");
    const uploadBtnText= document.getElementById("uploadBtnText");
    const file = fileInput.files[0];

    if (!file) { showToast("Please select a PDF first.", "error"); return; }

    uploadBtn.disabled = true;
    uploadBtnText.textContent = "Uploading…";
    dropProgress.classList.add("visible");

    let pct = 0;
    const ticker = setInterval(() => {
        pct = Math.min(pct + Math.random() * 18, 85);
        progressBar.style.width = pct + "%";
    }, 200);

    try {
        const result = await uploadDocument(file);
        clearInterval(ticker);
        progressBar.style.width = "100%";
        setTimeout(() => {
            dropProgress.classList.remove("visible");
            progressBar.style.width = "0%";
        }, 600);

        showToast(`✓ ${result.filename} — ${result.indexed_chunks} chunks indexed`, "success");

        // Add to uploaded files list and re-render
        uploadedFiles.push({
            id: result.document_id,
            name: result.filename,
            chunks: result.indexed_chunks
        });
        renderFileList();

        // Switch to chat view
        showView("Chat");
        addWelcomeAfterUpload(result.filename);

        // Mark the newly added file as active
        const bubbles = document.querySelectorAll('.file-bubble');
        bubbles.forEach(b => b.classList.remove('active'));
        if (bubbles.length > 0) bubbles[bubbles.length - 1].classList.add('active');

    } catch (err) {
        clearInterval(ticker);
        dropProgress.classList.remove("visible");
        progressBar.style.width = "0%";
        showToast("Upload failed. Check the server.", "error");
    } finally {
        uploadBtn.disabled = false;
        uploadBtnText.textContent = "Select a PDF first";
    }
});

function addWelcomeAfterUpload(filename) {
    const messages = document.getElementById("messages");
    messages.innerHTML = "";
    const row = document.createElement("div");
    row.className = "message ai";
    row.innerHTML = `
        <div class="msg-avatar ai">Q</div>
        <div class="bubble">📄 <strong>${filename}</strong> is ready. Ask me anything about it!</div>
    `;
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
}
